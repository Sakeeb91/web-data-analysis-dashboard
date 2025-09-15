#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required.")
        sys.exit(1)
    logger.info(f"✓ Python {sys.version.split()[0]} detected")

def create_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'data',
        'exports'
    ]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

    logger.info("✓ Created necessary directories")

def install_dependencies():
    """Install Python dependencies"""
    logger.info("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        sys.exit(1)

def install_playwright_browsers():
    """Install Playwright browsers"""
    logger.info("Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        logger.info("✓ Playwright browsers installed")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to install Playwright browsers: {e}")
        logger.warning("You can install them manually with: playwright install chromium")

def download_models():
    """Pre-download sentiment analysis models"""
    logger.info("Downloading sentiment analysis models...")
    try:
        from transformers import pipeline

        model = "distilbert-base-uncased-finetuned-sst-2-english"
        pipeline("sentiment-analysis", model=model)
        logger.info("✓ Sentiment analysis models downloaded")
    except Exception as e:
        logger.warning(f"Failed to download models: {e}")
        logger.warning("Models will be downloaded on first use")

def create_env_file():
    """Create .env file with default settings"""
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write("# Environment Variables\n")
            f.write("FLASK_ENV=development\n")
            f.write("FLASK_DEBUG=True\n")
            f.write("SECRET_KEY=dev-secret-key-change-in-production\n")
            f.write("DATABASE_URL=sqlite:///data_analysis.db\n")
        logger.info("✓ Created .env file with default settings")
    else:
        logger.info("✓ .env file already exists")

def test_imports():
    """Test that all required modules can be imported"""
    modules = [
        'flask',
        'flask_sqlalchemy',
        'flask_cors',
        'playwright',
        'bs4',
        'transformers',
        'torch',
        'apscheduler',
        'pandas',
        'numpy'
    ]

    failed = []
    for module in modules:
        try:
            __import__(module)
        except ImportError:
            failed.append(module)

    if failed:
        logger.error(f"Failed to import modules: {', '.join(failed)}")
        logger.error("Please run: pip install -r requirements.txt")
        sys.exit(1)

    logger.info("✓ All required modules imported successfully")

def main():
    """Main setup function"""
    logger.info("=== Web Data Analysis Dashboard Setup ===\n")

    check_python_version()
    create_directories()
    install_dependencies()
    install_playwright_browsers()
    download_models()
    create_env_file()
    test_imports()

    logger.info("\n=== Setup Complete! ===")
    logger.info("\nTo start the application:")
    logger.info("  python app.py")
    logger.info("\nThen open your browser to:")
    logger.info("  http://localhost:5000")
    logger.info("\nFor configuration options, edit config.py")

if __name__ == "__main__":
    main()