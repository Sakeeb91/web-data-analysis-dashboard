# Web Data Analysis Dashboard

A Python-based prototype for scraping web data, performing sentiment analysis, and displaying results in an interactive dashboard.

## Features

- **Web Scraping**: Supports both static (BeautifulSoup) and dynamic (Playwright) content scraping
- **Sentiment Analysis**: Uses Hugging Face Transformers for accurate sentiment classification
- **Data Aggregation**: Daily, weekly, and hourly aggregation of sentiment data
- **Interactive Dashboard**: Real-time charts and tables with filtering capabilities
- **Data Export**: Export results as CSV or JSON
- **Scheduled Scraping**: Automated periodic data collection
- **SQLite Database**: Local storage for all scraped and analyzed data

## Requirements

- Python 3.8+
- 4GB RAM minimum (8GB recommended for transformer models)
- 2GB disk space for models and data

## Installation

1. Clone or download this project:
```bash
cd web-analysis-dashboard
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers (for dynamic content):
```bash
playwright install chromium
```

5. Run the setup script:
```bash
python setup.py
```

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

## Running the Application

### Quick Start (Demo Mode)
For immediate testing without ML dependencies:
```bash
python app_demo.py
```
Access at: http://localhost:8080

### Full Version
With all ML features (requires compatible Python version):
```bash
python app.py
```
Access at: http://localhost:5000

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

### Scheduling Automated Scraping
Configure websites in `config.py` and restart the application. The scheduler will automatically scrape at the specified intervals.

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
web-analysis-dashboard/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── setup.py             # Setup script
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
└── static/            # CSS and JavaScript
    ├── css/style.css
    └── js/charts.js
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
rm data_analysis.db
python app.py  # Will recreate the database
```

### Memory Issues
If you encounter memory errors, try:
1. Reduce `SENTIMENT_BATCH_SIZE` in config.py
2. Use a smaller model in `analyzer/sentiment.py`
3. Increase system swap space

## Performance Tips

1. **For faster scraping**: Use `use_playwright: False` for static content
2. **For better accuracy**: Increase sentiment batch size if you have sufficient RAM
3. **For storage optimization**: Run cleanup periodically (removes data older than 30 days)

## Security Notes

- The application is designed for local/development use
- For production, update `SECRET_KEY` in config.py
- Implement proper authentication before deploying publicly
- Be respectful of websites' robots.txt and terms of service

## License

This prototype is provided as-is for development and testing purposes.

## Support

For issues or questions, please refer to the documentation or create an issue in the project repository.