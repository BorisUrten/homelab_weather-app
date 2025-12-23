import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weather_app import WeatherAPI, WeatherDB, HealthCheckHandler

# --- Fixtures ---

@patch.dict(os.environ, {
    'WEATHER_API_KEY': 'test_key',
    'CITY': 'TestCity',
    'COUNTRY': 'TestCountry',
    'DB_HOST': 'localhost',
    'DB_NAME': 'test_db',
    'DB_USER': 'test_user',
    'DB_PASSWORD': 'test_password'
})
@patch('psycopg2.connect')
def test_weather_db_init(mock_connect):
    """Test database initialization"""
    # Setup mock
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Run init
    db = WeatherDB()
    db.init_db()
    
    # Assertions
    mock_connect.assert_called_once()
    mock_cursor.execute.assert_called_once()
    assert "CREATE TABLE IF NOT EXISTS weather_data" in mock_cursor.execute.call_args[0][0]
    mock_conn.commit.assert_called_once()

@patch.dict(os.environ, {'WEATHER_API_KEY': 'test_key'})
@patch('requests.get')
def test_get_weather_data_success(mock_get):
    """Test successful weather data fetching"""
    # Setup mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        'current': {
            'temp_c': 20.5,
            'humidity': 65,
            'pressure_mb': 1013.25
        }
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    # Run method
    api = WeatherAPI()
    result = api.get_weather_data()
    
    # Assertions
    assert result is not None
    assert result['temperature'] == 20.5
    assert result['humidity'] == 65
    assert result['pressure'] == 1013.25
    assert result['city'] == 'Mississauga' # Default if not overridden in this specific test scopeenv
    assert isinstance(result['timestamp'], datetime)

@patch.dict(os.environ, {'WEATHER_API_KEY': 'test_key'})
@patch('requests.get')
def test_get_weather_data_failure(mock_get):
    """Test API failure handling"""
    # Setup mock to raise exception
    mock_get.side_effect = Exception("API Error")
    
    # Run method
    api = WeatherAPI()
    result = api.get_weather_data()
    
    # Assertions
    assert result is None

def test_health_check_handler():
    """Test health check handler logic"""
    # This is a basic test to ensure the class can be instantiated
    # A full test would require mocking the socket server
    handler = HealthCheckHandler
    assert hasattr(handler, 'do_GET')
    assert hasattr(handler, 'log_message')
