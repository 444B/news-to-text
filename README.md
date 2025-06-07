# 📰 News to Text

A Streamlit-powered application that aggregates news from multiple RSS feeds and generates broadcast-ready scripts. Perfect for radio stations, podcasters, and content creators who need to quickly compile and format news bulletins.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- 🔍 **Smart RSS Discovery**: Automatically finds RSS feeds from news websites
- 📡 **Multi-Source Aggregation**: Combine news from multiple sources into one bulletin
- 📝 **Interactive Selection**: Choose exactly which articles to include
- 🎯 **Smart Summarization**: Automatic extractive summarization of articles
- 📄 **Script Generation**: Creates professional broadcast-ready scripts
- 💾 **Local Caching**: Saves RSS feeds for quick access
- 🎨 **Clean UI**: Intuitive Streamlit interface
- 📥 **Export Options**: Download scripts as text files

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/news-to-text.git
cd news-to-text
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database with popular news sources:
```bash
python reset_db.py
```

5. Run the application:
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Usage

### 1. Select News Sources
- Check the boxes next to pre-loaded news sources in the sidebar
- Or add custom sources using the "Add New Source" form
- The app remembers your selections between sessions

### 2. Fetch Articles
- Click "Fetch Latest Articles" to retrieve news from selected sources
- Articles are grouped by source for easy browsing

### 3. Select Articles
- Review headlines and summaries
- Check the boxes next to articles you want to include
- Selected articles will be used in your bulletin

### 4. Generate Script
- Click "Generate News Script" to create your bulletin
- The script includes:
  - Professional introduction with current date
  - Smooth transitions between stories
  - Summarized content for each article
  - Closing remarks

### 5. Edit and Export
- Edit the generated script directly in the text area
- View estimated read time
- Download as a text file for your broadcast

## 🗄️ Pre-loaded News Sources

The app comes with 16 major news sources pre-configured:

- **General News**: BBC, CNN, Reuters, AP News, NPR
- **Newspapers**: New York Times, The Guardian, Washington Post, Wall Street Journal
- **Technology**: TechCrunch, Wired, Ars Technica, The Verge
- **Business**: Bloomberg, The Economist
- **More**: Fox News

## 🛠️ Project Structure

```
news-to-text/
├── app.py              # Main Streamlit application
├── reset_db.py         # Database initialization script
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── rss_feeds.db       # SQLite database (auto-created)
└── .gitignore         # Git ignore file
```

## 🔧 Configuration

### Adding Custom RSS Feeds

You can add any RSS-enabled news source:

1. Enter the website URL in the sidebar (e.g., `example.com`)
2. The app will attempt to auto-discover the RSS feed
3. If successful, it will appear in your available sources

### Database Management

Reset the database to default sources:
```bash
python reset_db.py
```

The SQLite database (`rss_feeds.db`) stores:
- RSS feed URLs and metadata
- Active/inactive status for each source
- Last fetch timestamps

## 🤝 Contributing

Contributions are welcome! Here are some ways to help:

- 🐛 Report bugs
- 💡 Suggest new features
- 🔧 Submit pull requests
- 📝 Improve documentation

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run the app to test: `streamlit run app.py`
5. Commit: `git commit -am 'Add feature'`
6. Push: `git push origin feature-name`
7. Create a Pull Request

## 🚀 Future Enhancements

- [ ] **Text-to-Speech**: Integration with Google Cloud TTS for audio output
- [ ] **AI Summarization**: Use GPT/Claude for better article summaries
- [ ] **Multiple Templates**: Different script styles (formal, casual, etc.)
- [ ] **Scheduling**: Automated article fetching at set times
- [ ] **Categories**: Filter articles by topic
- [ ] **Authentication**: User accounts with saved preferences
- [ ] **API Access**: RESTful API for integration with other tools
- [ ] **Audio Export**: Direct MP3/WAV generation
- [ ] **Real-time Updates**: Live article streaming
- [ ] **Translation**: Multi-language support

## 🐛 Troubleshooting

### Common Issues

**"No RSS feed found" error**
- Some websites hide their RSS feeds or use non-standard locations
- Try adding `/rss`, `/feed`, or `/atom` to the URL
- Check if the site actually has an RSS feed

**Database errors after update**
- Run `python reset_db.py` to rebuild the database
- This will restore all default news sources

**Slow article fetching**
- Some news sites have rate limits
- Try selecting fewer sources at once
- Check your internet connection

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- RSS parsing by [feedparser](https://github.com/kurtmckee/feedparser)
- HTML parsing by [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Made with ❤️ for radio stations, podcasters, and news enthusiasts everywhere!