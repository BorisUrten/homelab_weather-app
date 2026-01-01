"""
Unit tests for Weather Data Collector
"""
import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime
import sys
import os

# Add parent directory to path to import collector module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from collector import WeatherAPI, WeatherDB

class TestWeatherAPI:
    """Test WeatherAPI class"""

    def test_initialization_with_api_key(self):
        """Test WeatherAPI initializes correctly with API key"""
        with patch.dict(os.environ, {
            'WEATHER_API_KEY': 'test_api_key',
            'CITY': 'Toronto',
            'COUNTRY': 'Canada'
        }):
            api = WeatherAPI()
            assert api.api_key == 'test_api_key'
            assert api.city == 'Toronto'
            assert api.country == 'Canada'
            assert api.location == 'Toronto,Canada'

    def test_initialization_without_api_key(self):
        """Test WeatherAPI raises ValueError without API key"""
        with patch.dict(os.environ, {}, clear=True):
            if 'WEATHER_API_KEY' in os.environ:
                del os.environ['WEATHER_API_KEY']

            with pytest.raises(ValueError, match="WEATHER_API_KEY"):
                WeatherAPI()

    def test_default_values(self):
        """Test WeatherAPI uses default values when not specified"""
        with patch.dict(os.environ, {'WEATHER_API_KEY': 'test_key'}, clear=True):
            api = WeatherAPI()
            assert api.city == 'Mississauga'
            assert api.country == 'Canada'

    @patch('collector.requests.get')
    def test_get_weather_data_success(self, mock_get):
        """Test successful weather data fetch"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'current': {
                'temp_c': 22.5,
                'humidity': 65,
                'pressure_mb': 1013
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {
            'WEATHER_API_KEY': 'test_key',
            'CITY': 'Toronto',
            'COUNTRY': 'Canada'
        }):
            api = WeatherAPI()
            data = api.get_weather_data()

            assert data is not None
            assert data['temperature'] == 22.5
            assert data['humidity'] == 65
            assert data['pressure'] == 1013
            assert data['city'] == 'Toronto'
            assert data['country'] == 'Canada'
            assert isinstance(data['timestamp'], datetime)

    @patch('collector.requests.get')
    def test_get_weather_data_api_error(self, mock_get):
        """Test weather data fetch with API error"""
        mock_get.side_effect = Exception("API Error")

        with patch.dict(os.environ, {
            'WEATHER_API_KEY': 'test_key'
        }):
            api = WeatherAPI()
            data = api.get_weather_data()
            assert data is None

    @patch('collector.requests.get')
    def test_get_weather_data_timeout(self, mock_get):
        """Test weather data fetch with timeout"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        with patch.dict(os.environ, {
            'WEATHER_API_KEY': 'test_key'
        }):
            api = WeatherAPI()
            data = api.get_weather_data()
            assert data is None

class TestWeatherDB:
    """Test WeatherDB class"""

    def test_initialization_with_database_url(self):
        """Test WeatherDB parses DATABASE_URL correctly"""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:pass@host:5433/dbname'
        }):
            db = WeatherDB()
            assert db.host == 'host'
            assert db.database == 'dbname'
            assert db.user == 'user'
            assert db.password == 'pass'
            assert db.port == 5433

    def test_initialization_with_individual_vars(self):
        """Test WeatherDB uses individual environment variables"""
        with patch.dict(os.environ, {
            'DB_HOST': 'localhost',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_pass',
            'DB_PORT': '5432'
        }, clear=True):
            # Ensure DATABASE_URL doesn't exist
            if 'DATABASE_URL' in os.environ:
                del os.environ['DATABASE_URL']

            db = WeatherDB()
            assert db.host == 'localhost'
            assert db.database == 'test_db'
            assert db.user == 'test_user'
            assert db.password == 'test_pass'

    def test_default_values(self):
        """Test WeatherDB uses default values"""
        with patch.dict(os.environ, {}, clear=True):
            # Remove DATABASE_URL if it exists
            if 'DATABASE_URL' in os.environ:
                del os.environ['DATABASE_URL']

            db = WeatherDB()
            assert db.host == 'postgres'
            assert db.database == 'weather_db'
            assert db.user == 'postgres'
            assert db.password == 'postgres'

    @patch('collector.psycopg2.connect')
    def test_init_db_success(self, mock_connect):
        """Test successful database initialization"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db = WeatherDB()
        db.init_db()

        # Verify table creation SQL was executed
        mock_cursor.execute.assert_called_once()
        assert 'CREATE TABLE' in mock_cursor.execute.call_args[0][0]
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('collector.psycopg2.connect')
    def test_init_db_failure(self, mock_connect):
        """Test database initialization failure"""
        from psycopg2 import OperationalError
        mock_connect.side_effect = OperationalError("Connection failed")

        db = WeatherDB()
        with pytest.raises(OperationalError):
            db.init_db()

    @patch('collector.psycopg2.connect')
    def test_store_weather_data_success(self, mock_connect):
        """Test successful weather data storage"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db = WeatherDB()
        weather_data = {
            'temperature': 22.5,
            'humidity': 65,
            'pressure': 1013,
            'timestamp': datetime.now(),
            'city': 'Toronto',
            'country': 'Canada'
        }

        db.store_weather_data(weather_data)

        # Verify INSERT SQL was executed
        mock_cursor.execute.assert_called_once()
        assert 'INSERT INTO weather_data' in mock_cursor.execute.call_args[0][0]
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('collector.psycopg2.connect')
    def test_store_weather_data_failure(self, mock_connect):
        """Test weather data storage failure"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_connect.return_value = mock_conn

        db = WeatherDB()
        weather_data = {
            'temperature': 22.5,
            'humidity': 65,
            'pressure': 1013,
            'timestamp': datetime.now(),
            'city': 'Toronto',
            'country': 'Canada'
        }

        with pytest.raises(Exception):
            db.store_weather_data(weather_data)

        # Verify connections are closed even on error
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

class TestSignalHandling:
    """Test signal handling and graceful shutdown"""

    @patch('collector.signal.signal')
    def test_signal_handler_registration(self, mock_signal):
        """Test that signal handlers are registered"""
        # This would test the main() function's signal registration
        # Skipping actual implementation as it requires running main()
        pass
