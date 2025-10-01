# EBP Data Analysis - Optimized

This project contains both a Jupyter notebook and a Python script for EBP data ingestion, optimized for better performance, error handling, and maintainability.

## Files

- `main.py` - Main Python script
- `.env` - Environment configuration file
- `requirements.txt` - Python dependencies

## Key Optimizations

### 1. Environment Configuration
- All credentials and configuration are now managed through a `.env` file
- No hardcoded credentials in the code
- Easy configuration changes without code modifications

### 2. Enhanced Error Handling
- Comprehensive try-catch blocks throughout the code
- Retry mechanism for API calls with exponential backoff
- Graceful handling of missing data and API failures
- Detailed logging for debugging and monitoring

### 3. Improved Data Processing
- Type hints for better code clarity and IDE support
- Safe column operations that handle missing columns gracefully
- Optimized data filtering and transformation functions
- Better memory management for large datasets

### 4. Robust Logging
- Structured logging with different levels (INFO, WARNING, ERROR)
- Progress tracking for long-running operations
- Detailed error messages for troubleshooting

### 5. Flexible Export System
- Environment-based export paths
- Automatic directory creation
- Export success/failure tracking
- Configurable subdirectories

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```env
# EBP API Configuration
EBP_USERNAME=your_username
EBP_PASSWORD=your_password
EBP_API_PREFIX=https://ebp-api-service.ebp.ckw.ch

# Export Configuration
EXPORT_BASE_PATH=/Users/matthiasveitinger/Library/CloudStorage/OneDrive-FreigegebeneBibliotheken–CKW-Gruppe/CKW Insights - EBPD
EXPORT_SUBDIRECTORIES=areas,contracts,buildings,utility_units,meters,managers,profiles

# Data Processing Configuration
DEFAULT_LIMIT=20000
FILTER_WORDS=delete,geloescht,loeschen,lösch,ZEV EMD

# Logging Configuration
LOG_LEVEL=INFO
```

3. Run the script:
```bash
# Option 1: Run the Python script directly
python main.py

# Option 2: Run with virtual environment
source venv/bin/activate
python main.py


## Features

- **Automatic retry**: API calls are automatically retried on failure
- **Progress tracking**: Real-time progress updates for long operations
- **Data validation**: Comprehensive data validation and error reporting
- **Flexible configuration**: Easy configuration through environment variables
- **Robust export**: Reliable data export with error handling

## Error Handling

The notebook includes comprehensive error handling:
- API authentication failures
- Network timeouts and connection errors
- Data transformation errors
- Export failures
- Missing or invalid data

All errors are logged with detailed information for troubleshooting.
