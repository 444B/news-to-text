#!/usr/bin/env python3
"""
Reset and populate the RSS feeds database with known news sources.
Run this script to clean and initialize your database.
"""

import sqlite3
from datetime import datetime

# Known RSS feeds for major sites
KNOWN_RSS_FEEDS = {
    'bbc.com': {
        'url': 'http://feeds.bbci.co.uk/news/rss.xml',
        'name': 'BBC News'
    },
    'reuters.com': {
        'url': 'https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best',
        'name': 'Reuters'
    },
    'cnn.com': {
        'url': 'http://rss.cnn.com/rss/cnn_topstories.rss',
        'name': 'CNN'
    },
    'nytimes.com': {
        'url': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
        'name': 'New York Times'
    },
    'theguardian.com': {
        'url': 'https://www.theguardian.com/rss',
        'name': 'The Guardian'
    },
    'washingtonpost.com': {
        'url': 'https://feeds.washingtonpost.com/rss/world',
        'name': 'Washington Post'
    },
    'apnews.com': {
        'url': 'https://rsshub.app/apnews/topics/apf-topnews',
        'name': 'AP News'
    },
    'npr.org': {
        'url': 'https://feeds.npr.org/1001/rss.xml',
        'name': 'NPR News'
    },
    'foxnews.com': {
        'url': 'https://moxie.foxnews.com/google-publisher/latest.xml',
        'name': 'Fox News'
    },
    'wsj.com': {
        'url': 'https://feeds.a.dj.com/rss/RSSWorldNews.xml',
        'name': 'Wall Street Journal'
    },
    'techcrunch.com': {
        'url': 'https://techcrunch.com/feed/',
        'name': 'TechCrunch'
    },
    'wired.com': {
        'url': 'https://www.wired.com/feed/rss',
        'name': 'Wired'
    },
    'arstechnica.com': {
        'url': 'http://feeds.arstechnica.com/arstechnica/index',
        'name': 'Ars Technica'
    },
    'theverge.com': {
        'url': 'https://www.theverge.com/rss/index.xml',
        'name': 'The Verge'
    },
    'bloomberg.com': {
        'url': 'https://feeds.bloomberg.com/markets/news.rss',
        'name': 'Bloomberg'
    },
    'economist.com': {
        'url': 'https://www.economist.com/rss',
        'name': 'The Economist'
    }
}

def reset_database():
    """Reset and populate the RSS feeds database"""
    print("🗑️  Resetting database...")
    
    # Connect to database
    conn = sqlite3.connect('rss_feeds.db')
    c = conn.cursor()
    
    # Drop existing tables
    c.execute("DROP TABLE IF EXISTS rss_feeds")
    c.execute("DROP TABLE IF EXISTS article_cache")
    
    # Create new tables with proper schema
    c.execute('''CREATE TABLE rss_feeds
                 (domain TEXT PRIMARY KEY, 
                  rss_url TEXT,
                  display_name TEXT,
                  last_checked TIMESTAMP,
                  last_success TIMESTAMP,
                  is_active INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE article_cache
                 (url_hash TEXT PRIMARY KEY,
                  url TEXT,
                  title TEXT,
                  content TEXT,
                  summary TEXT,
                  published TIMESTAMP,
                  fetched TIMESTAMP)''')
    
    print("✅ Tables created")
    
    # Populate with known feeds
    print("\n📰 Adding known RSS feeds...")
    
    for domain, feed_info in KNOWN_RSS_FEEDS.items():
        try:
            c.execute("""INSERT INTO rss_feeds 
                         (domain, rss_url, display_name, last_checked, last_success, is_active) 
                         VALUES (?, ?, ?, ?, ?, ?)""", 
                      (domain, 
                       feed_info['url'], 
                       feed_info['name'],
                       datetime.now(),
                       datetime.now(),
                       0))  # Start with all inactive
            print(f"  ✓ Added {feed_info['name']} ({domain})")
        except Exception as e:
            print(f"  ✗ Error adding {domain}: {e}")
    
    # Commit changes
    conn.commit()
    
    # Show summary
    c.execute("SELECT COUNT(*) FROM rss_feeds")
    count = c.fetchone()[0]
    print(f"\n✅ Database reset complete! Added {count} news sources.")
    
    # Close connection
    conn.close()
    
    print("\n📌 To activate sources, select them in the Streamlit app sidebar.")

if __name__ == "__main__":
    response = input("⚠️  This will delete all existing data. Continue? (yes/no): ")
    if response.lower() == 'yes':
        reset_database()
    else:
        print("Cancelled.")