# Web Data Analysis Dashboard

A comprehensive Python-based application for scraping web data, performing sentiment analysis, and displaying results in an interactive dashboard.

## Features

- **Web Scraping**: Supports both static (BeautifulSoup) and dynamic (Playwright) content scraping
- **Sentiment Analysis**: Uses Hugging Face Transformers for accurate sentiment classification
- **Data Aggregation**: Daily, weekly, and hourly aggregation of sentiment data
- **Interactive Dashboard**: Real-time charts and tables with filtering capabilities
- **Data Export**: Export results as CSV or JSON
- **Scheduled Scraping**: Automated periodic data collection
- **Multiple App Versions**: Demo, Simple, Production, and V2 implementations
- **Docker Support**: PostgreSQL and Redis integration for production deployment
- **SQLite Database**: Local storage for all scraped and analyzed data

## Requirements

- Python 3.8+
- 4GB RAM minimum (8GB recommended for transformer models)
- 2GB disk space for models and data

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Sakeeb91/web-data-analysis-dashboard.git
cd web-data-analysis-dashboard
```

2. Navigate to the application directory:
```bash
cd web-analysis-dashboard
```

3. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Install Playwright browsers (for dynamic content):
```bash
playwright install chromium
```

6. Run the setup script:
```bash
python setup.py
```

## Running the Application

### Demo Mode (Immediate Testing)
For immediate testing without ML dependencies:
```bash
python app_demo.py
```
Access at: http://localhost:8080

### Simple Version
Basic implementation with core features:
```bash
python app_simple.py
```
Access at: http://localhost:5001

### Production Version
Full-featured version with Docker support:
```bash
# Start Docker services (optional)
docker-compose up -d

# Run the production app
python app_production.py
# Or use the startup script
./start_production.sh
```
Access at: http://localhost:5002

### V2 Enhanced Version
Latest version with improved features:
```bash
python app_v2.py
```
Access at: http://localhost:5003

### Original Full Version
With all ML features:
```bash
python app.py
```
Access at: http://localhost:5000

## Configuration

Edit `config.py` to customize:

- `SCRAPING_INTERVAL_MINUTES`: How often to scrape (default: 60)
- `WEBSITES_TO_SCRAPE`: List of websites to monitor
- `SENTIMENT_BATCH_SIZE`: Batch size for sentiment analysis
- `DATABASE_URL`: Database connection (defaults to SQLite)

Example configuration:
```python
WEBSITES_TO_SCRAPE = [
    {
        'name': 'Tech News',
        'url': 'https://example.com/tech',
        'selector': 'article.post',
        'enabled': True
    }
]
```

## Usage

### Dashboard (Main Page)
- View real-time sentiment statistics
- Monitor sentiment distribution with pie charts
- Track sentiment trends over time
- Filter by date range and source
- View recent sentiment analysis results

### Analytics Page
- Advanced visualizations and trends
- Aggregated data by hour/day/week
- Confidence vs. score scatter plots
- Export data in multiple formats
- Manage scraping jobs

### Adding URLs for Analysis
1. Click "Add URL" button on the dashboard
2. Enter the URL to analyze
3. Optionally provide a CSS selector for specific content
4. Click "Analyze" to scrape and analyze immediately

## API Endpoints

- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/sentiments/recent` - Recent sentiment results
- `GET /api/aggregated/{period_type}` - Aggregated data (daily/weekly/hourly)
- `POST /api/scrape` - Manually scrape a URL
- `GET /api/export/{format}` - Export data (json/csv)
- `GET /api/sources` - List all data sources
- `GET /api/jobs` - List scraping jobs
- `POST /api/jobs/trigger/{job_id}` - Manually trigger a job

## Project Structure

```
web-data-analysis-dashboard/
├── README.md                     # This file
├── .gitignore                   # Git ignore rules
└── web-analysis-dashboard/      # Main application directory
    ├── app.py                   # Original Flask application
    ├── app_demo.py             # Demo version (no ML deps)
    ├── app_simple.py           # Simplified version
    ├── app_production.py       # Production version
    ├── app_v2.py              # V2 enhanced version
    ├── config.py              # Configuration settings
    ├── requirements.txt       # Python dependencies
    ├── requirements_production.txt  # Production dependencies
    ├── requirements_fixed.txt      # Fixed version dependencies
    ├── setup.py              # Setup script
    ├── docker-compose.yml    # Docker configuration
    ├── start_production.sh   # Production startup script
    ├── scraper/             # Web scraping modules
    │   ├── base_scraper.py
    │   ├── scrapers.py
    │   └── scheduler.py
    ├── analyzer/            # Sentiment analysis
    │   ├── sentiment.py
    │   └── aggregator.py
    ├── database/           # Database models and manager
    │   ├── models.py
    │   └── db_manager.py
    ├── templates/          # HTML templates
    │   ├── base.html
    │   ├── dashboard.html
    │   └── analytics.html
    ├── static/            # CSS and JavaScript
    │   ├── css/style.css
    │   └── js/charts.js
    └── docs/             # Documentation
        ├── phase1-implementation.md
        ├── phase1-complete.md
        └── demo-to-production-checklist.md
```

## Testing

Run the test files to verify functionality:

```bash
# Test sentiment analysis
python test_sentiment.py

# Test web scraping
python test_scraping.py

# Test browser automation
python test_browser.py
```

## Troubleshooting

### Model Download Issues
If the sentiment model fails to download:
```bash
python -c "from transformers import pipeline; pipeline('sentiment-analysis')"
```

### Database Issues
Reset the database:
```bash
rm data_analysis.db  # or production_v2.db
python app.py  # Will recreate the database
```

### Memory Issues
If you encounter memory errors:
1. Reduce `SENTIMENT_BATCH_SIZE` in config.py
2. Use a smaller model in `analyzer/sentiment.py`
3. Increase system swap space

### Docker Issues
If Docker services fail to start:
```bash
docker-compose down
docker-compose up -d --force-recreate
```

## Performance Tips

1. **For faster scraping**: Use `use_playwright: False` for static content
2. **For better accuracy**: Increase sentiment batch size if you have sufficient RAM
3. **For storage optimization**: Run cleanup periodically (removes data older than 30 days)

## Security Notes

- The application is designed for local/development use
- For production, update `SECRET_KEY` in config.py
- Implement proper authentication before deploying publicly
- Be respectful of websites' robots.txt and terms of service

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is provided as-is for development and testing purposes.

## Support

For issues or questions, please create an issue in the [GitHub repository](https://github.com/Sakeeb91/web-data-analysis-dashboard/issues).