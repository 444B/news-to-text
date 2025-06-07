import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import sqlite3
import hashlib
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin, urlparse
import json
import time
import warnings

# Suppress XML parsing warning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Initialize session state
if 'selected_articles' not in st.session_state:
    st.session_state.selected_articles = []
if 'news_script' not in st.session_state:
    st.session_state.news_script = ""
if 'active_sources' not in st.session_state:
    st.session_state.active_sources = []

# Known RSS feeds for major sites
KNOWN_RSS_FEEDS = {
    'bbc.com': 'http://feeds.bbci.co.uk/news/rss.xml',
    'bbc.co.uk': 'http://feeds.bbci.co.uk/news/rss.xml',
    'reuters.com': 'https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best',
    'cnn.com': 'http://rss.cnn.com/rss/cnn_topstories.rss',
    'nytimes.com': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
    'theguardian.com': 'https://www.theguardian.com/rss',
    'washingtonpost.com': 'https://feeds.washingtonpost.com/rss/world',
    'apnews.com': 'https://rsshub.app/apnews/topics/apf-topnews',
    'npr.org': 'https://feeds.npr.org/1001/rss.xml',
    'foxnews.com': 'https://moxie.foxnews.com/google-publisher/latest.xml',
    'wsj.com': 'https://feeds.a.dj.com/rss/RSSWorldNews.xml',
    'techcrunch.com': 'https://techcrunch.com/feed/',
    'wired.com': 'https://www.wired.com/feed/rss',
    'arstechnica.com': 'http://feeds.arstechnica.com/arstechnica/index',
    'theverge.com': 'https://www.theverge.com/rss/index.xml',
    'bloomberg.com': 'https://feeds.bloomberg.com/markets/news.rss',
    'ft.com': 'https://www.ft.com/?format=rss',
    'economist.com': 'https://www.economist.com/rss',
}

# Database setup with datetime adapter fix
def adapt_datetime(ts):
    return ts.isoformat()

def convert_datetime(ts):
    return datetime.fromisoformat(ts.decode())

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

def init_db():
    conn = sqlite3.connect('rss_feeds.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS rss_feeds
                 (domain TEXT PRIMARY KEY, 
                  rss_url TEXT,
                  display_name TEXT,
                  last_checked TIMESTAMP,
                  last_success TIMESTAMP,
                  is_active INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS article_cache
                 (url_hash TEXT PRIMARY KEY,
                  url TEXT,
                  title TEXT,
                  content TEXT,
                  summary TEXT,
                  published TIMESTAMP,
                  fetched TIMESTAMP)''')
    
    # Check if we need to add new columns to existing database
    c.execute("PRAGMA table_info(rss_feeds)")
    columns = [column[1] for column in c.fetchall()]
    
    # Add missing columns
    if 'display_name' not in columns:
        c.execute("ALTER TABLE rss_feeds ADD COLUMN display_name TEXT")
        # Update existing rows with a default display name
        c.execute("UPDATE rss_feeds SET display_name = domain WHERE display_name IS NULL")
    
    if 'is_active' not in columns:
        c.execute("ALTER TABLE rss_feeds ADD COLUMN is_active INTEGER DEFAULT 0")
    
    conn.commit()
    conn.close()

# Get all cached feeds
def get_cached_feeds():
    conn = sqlite3.connect('rss_feeds.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    try:
        c.execute("""SELECT domain, rss_url, display_name, last_success, is_active 
                     FROM rss_feeds 
                     WHERE rss_url IS NOT NULL 
                     ORDER BY display_name""")
        feeds = c.fetchall()
    except sqlite3.OperationalError:
        # If there's an error, return empty list
        feeds = []
    conn.close()
    return feeds

# Update feed active status
def update_feed_active_status(domain, is_active):
    conn = sqlite3.connect('rss_feeds.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("UPDATE rss_feeds SET is_active = ? WHERE domain = ?", (is_active, domain))
    conn.commit()
    conn.close()

# Find RSS feed from website
def find_rss_feed(url):
    """Attempt to find RSS feed URL from a website"""
    try:
        # Clean up domain
        domain = urlparse(url).netloc or url
        domain = domain.replace('www.', '')
        
        # Check known feeds first
        if domain in KNOWN_RSS_FEEDS:
            return KNOWN_RSS_FEEDS[domain]
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for RSS links in <link> tags
        rss_links = []
        for link in soup.find_all('link', type=['application/rss+xml', 'application/atom+xml']):
            if link.get('href'):
                rss_links.append(urljoin(url, link['href']))
        
        # Look for RSS links in page content
        if not rss_links:
            for a in soup.find_all('a', href=True):
                href = a['href'].lower()
                if any(term in href for term in ['rss', 'feed', 'atom', 'xml']):
                    if any(term in href for term in ['.xml', '/rss', '/feed', '/atom']):
                        full_url = urljoin(url, a['href'])
                        rss_links.append(full_url)
        
        # Try common RSS paths
        if not rss_links:
            common_paths = ['/rss', '/feed', '/rss.xml', '/feed.xml', '/atom.xml', 
                          '/index.xml', '/feeds', '/blog/feed', '/news/rss',
                          '/rss/news', '/feed/news', '/?feed=rss2', '/feed.rss']
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            
            for path in common_paths:
                try:
                    test_url = urljoin(base_url, path)
                    test_response = requests.get(test_url, timeout=5, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    if test_response.status_code == 200:
                        content_type = test_response.headers.get('content-type', '').lower()
                        if any(term in content_type for term in ['xml', 'rss', 'atom']):
                            rss_links.append(test_url)
                            break
                except:
                    continue
        
        # Validate RSS links
        valid_rss = None
        for rss_url in rss_links[:3]:  # Check first 3 candidates
            try:
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    valid_rss = rss_url
                    break
            except:
                continue
        
        return valid_rss
    
    except Exception as e:
        st.error(f"Error finding RSS feed: {str(e)}")
        return None

# Get or fetch RSS URL
def get_rss_url(domain):
    conn = sqlite3.connect('rss_feeds.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    
    # Clean domain
    clean_domain = domain.replace('http://', '').replace('https://', '').replace('www.', '')
    
    # Check cache
    c.execute("SELECT rss_url, last_checked FROM rss_feeds WHERE domain = ?", (clean_domain,))
    result = c.fetchone()
    
    if result and result[0]:
        # If checked within last 7 days, use cached
        if result[1]:
            last_checked = result[1]
            if datetime.now() - last_checked < timedelta(days=7):
                conn.close()
                return result[0]
    
    # Find RSS feed
    rss_url = find_rss_feed(domain)
    
    # Determine display name
    display_name = clean_domain.replace('.com', '').replace('.org', '').replace('.net', '').title()
    
    # Update cache
    if rss_url:
        c.execute("""INSERT OR REPLACE INTO rss_feeds 
                     (domain, rss_url, display_name, last_checked, last_success) 
                     VALUES (?, ?, ?, ?, ?)""", 
                  (clean_domain, rss_url, display_name, datetime.now(), datetime.now()))
    else:
        c.execute("""INSERT OR REPLACE INTO rss_feeds 
                     (domain, rss_url, display_name, last_checked) 
                     VALUES (?, ?, ?, ?)""", 
                  (clean_domain, None, display_name, datetime.now()))
    
    conn.commit()
    conn.close()
    return rss_url

# Fetch articles from RSS feed
def fetch_articles(rss_url, limit=20):
    try:
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            return []
        
        articles = []
        for entry in feed.entries[:limit]:
            article = {
                'title': entry.get('title', 'No title'),
                'url': entry.get('link', ''),
                'published': entry.get('published', entry.get('updated', '')),
                'summary': entry.get('summary', ''),
                'content': ''
            }
            
            # Try to get full content
            if 'content' in entry:
                article['content'] = entry.content[0].value
            elif 'description' in entry:
                article['content'] = entry.description
            
            # Clean HTML from content
            if article['content']:
                soup = BeautifulSoup(article['content'], 'html.parser')
                article['content'] = soup.get_text(separator=' ', strip=True)
            
            # Clean summary too
            if article['summary']:
                soup = BeautifulSoup(article['summary'], 'html.parser')
                article['summary'] = soup.get_text(separator=' ', strip=True)
            
            articles.append(article)
        
        return articles
    except Exception as e:
        st.error(f"Error fetching articles from {rss_url}: {str(e)}")
        return []

# Generate summary (simplified version)
def generate_summary(text, max_sentences=3):
    """Simple extractive summarization"""
    if not text:
        return ""
    
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if len(sentences) <= max_sentences:
        return ' '.join(sentences) + '.'
    
    # Simple scoring based on word frequency
    word_freq = {}
    for sentence in sentences:
        words = sentence.lower().split()
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
    
    # Score sentences
    sentence_scores = {}
    for sentence in sentences:
        score = 0
        words = sentence.lower().split()
        for word in words:
            score += word_freq.get(word, 0)
        sentence_scores[sentence] = score / len(words) if words else 0
    
    # Get top sentences
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
    top_sentences = sorted(top_sentences, key=lambda x: sentences.index(x[0]))
    
    return ' '.join([s[0] for s in top_sentences]) + '.'

# Generate news script
def generate_news_script(articles):
    """Generate a news readout script from selected articles"""
    script = f"Good evening, and welcome to the news. Today is {datetime.now().strftime('%B %d, %Y')}.\n\n"
    script += f"In today's bulletin, we have {len(articles)} stories for you.\n\n"
    
    for i, article in enumerate(articles, 1):
        script += f"--- Story {i} ---\n\n"
        script += f"{article['title']}\n\n"
        
        # Use content or summary
        content = article.get('content', '') or article.get('summary', '')
        if content:
            summary = generate_summary(content)
            script += summary
        else:
            script += "Details are still emerging on this story."
        
        script += "\n\n"
        
        if i < len(articles):
            script += "Moving on to our next story...\n\n"
    
    script += "That concludes our news bulletin for today. Thank you for listening."
    
    return script

# Streamlit UI
def main():
    st.set_page_config(page_title="News to Text", page_icon="📰", layout="wide")
    
    st.title("📰 News to Text")
    st.markdown("Transform news sources into broadcast-ready scripts")
    
    # Initialize database
    init_db()
    
    # Sidebar for news sources
    with st.sidebar:
        st.header("News Sources")
        
        # Show cached feeds
        cached_feeds = get_cached_feeds()
        if cached_feeds:
            st.subheader("Available Sources")
            st.caption("Select sources to include in your bulletin:")
            
            for domain, rss_url, display_name, last_success, is_active in cached_feeds:
                # Initialize active sources
                if is_active and domain not in st.session_state.active_sources:
                    st.session_state.active_sources.append(domain)
                
                # Checkbox for each source
                checked = st.checkbox(
                    display_name or domain,
                    value=domain in st.session_state.active_sources,
                    key=f"source_{domain}"
                )
                
                if checked and domain not in st.session_state.active_sources:
                    st.session_state.active_sources.append(domain)
                    update_feed_active_status(domain, 1)
                elif not checked and domain in st.session_state.active_sources:
                    st.session_state.active_sources.remove(domain)
                    update_feed_active_status(domain, 0)
            
            st.divider()
        
        # Add new source
        st.subheader("Add New Source")
        with st.form("add_source"):
            new_source = st.text_input(
                "News website", 
                placeholder="e.g., bbc.com, reuters.com",
                help="Popular sites: bbc.com, reuters.com, cnn.com, theguardian.com, npr.org"
            )
            add_button = st.form_submit_button("Add Source")
            
            if add_button and new_source:
                with st.spinner(f"Finding RSS feed for {new_source}..."):
                    rss_url = get_rss_url(new_source)
                    if rss_url:
                        st.success(f"✅ Found RSS feed for {new_source}")
                        # Refresh to show new source
                        st.rerun()
                    else:
                        st.error(f"❌ Could not find RSS feed for {new_source}")
    
    # Main content area
    if not st.session_state.active_sources:
        st.info("👈 Select news sources from the sidebar to get started")
        st.markdown("""
        ### Getting Started
        1. Check the boxes next to available news sources in the sidebar
        2. Or add new sources using the form
        3. Click 'Fetch Latest Articles' to retrieve news
        4. Select articles and generate your script!
        
        **Tip:** Try these popular news sites: BBC, CNN, The Guardian, NPR, TechCrunch
        """)
        return
    
    # Display active sources
    st.markdown(f"**Active sources:** {', '.join(st.session_state.active_sources)}")
    
    # Fetch articles button
    if st.button("🔄 Fetch Latest Articles", type="primary"):
        with st.spinner("Fetching articles..."):
            all_articles = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, source in enumerate(st.session_state.active_sources):
                status_text.text(f"Fetching from {source}...")
                progress_bar.progress((i + 1) / len(st.session_state.active_sources))
                
                # Get RSS URL from cache
                conn = sqlite3.connect('rss_feeds.db', detect_types=sqlite3.PARSE_DECLTYPES)
                c = conn.cursor()
                c.execute("SELECT rss_url FROM rss_feeds WHERE domain = ?", (source,))
                result = c.fetchone()
                conn.close()
                
                if result and result[0]:
                    articles = fetch_articles(result[0])
                    for article in articles:
                        article['source'] = source
                    all_articles.extend(articles)
            
            st.session_state.all_articles = all_articles
            progress_bar.empty()
            status_text.empty()
            
            if all_articles:
                st.success(f"Fetched {len(all_articles)} articles!")
            else:
                st.warning("No articles found. Try different sources.")
    
    # Display articles for selection
    if 'all_articles' in st.session_state and st.session_state.all_articles:
        st.header("Select Articles for Your Bulletin")
        
        # Group articles by source
        articles_by_source = {}
        for article in st.session_state.all_articles:
            source = article['source']
            if source not in articles_by_source:
                articles_by_source[source] = []
            articles_by_source[source].append(article)
        
        # Display articles
        for source, articles in articles_by_source.items():
            with st.expander(f"📰 {source} ({len(articles)} articles)", expanded=True):
                for article in articles[:10]:  # Limit display
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        # Create unique key for checkbox
                        article_key = hashlib.md5(f"{article['url']}{article['title']}".encode()).hexdigest()
                        selected = st.checkbox("Select", key=f"select_{article_key}")
                        
                        if selected and article not in st.session_state.selected_articles:
                            st.session_state.selected_articles.append(article)
                        elif not selected and article in st.session_state.selected_articles:
                            st.session_state.selected_articles.remove(article)
                    
                    with col2:
                        st.markdown(f"**{article['title']}**")
                        if article['summary']:
                            st.caption(article['summary'][:200] + "...")
                        if article['published']:
                            st.caption(f"Published: {article['published']}")
        
        # Generate script section
        if st.session_state.selected_articles:
            st.header(f"Generate Script ({len(st.session_state.selected_articles)} articles selected)")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🎙️ Generate News Script", type="primary"):
                    with st.spinner("Generating script..."):
                        script = generate_news_script(st.session_state.selected_articles)
                        st.session_state.news_script = script
            
            with col2:
                if st.button("🗑️ Clear Selection"):
                    st.session_state.selected_articles = []
                    st.session_state.news_script = ""
                    st.rerun()
            
            # Display generated script
            if st.session_state.news_script:
                st.subheader("Generated News Script")
                
                # Script display with edit capability
                edited_script = st.text_area(
                    "Edit your script:", 
                    value=st.session_state.news_script,
                    height=400
                )
                
                # Download options
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    st.download_button(
                        label="📥 Download Script",
                        data=edited_script,
                        file_name=f"news_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                
                with col2:
                    # Placeholder for TTS
                    if st.button("🔊 Generate Audio (Coming Soon)", disabled=True):
                        st.info("Text-to-speech functionality will be available in the next update")
                
                with col3:
                    # Word count
                    word_count = len(edited_script.split())
                    read_time = word_count / 150  # Average reading speed
                    st.metric("Read Time", f"{read_time:.1f} min")

if __name__ == "__main__":
    main()