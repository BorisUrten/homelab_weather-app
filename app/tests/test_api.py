"""
Unit tests for Flask REST API
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import api module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api import app, get_db_config, check_db_health

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    with patch('api.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        yield mock_cursor

class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_endpoint(self, client):
        """Test /health endpoint returns 200"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data

    def test_ready_endpoint_success(self, client):
        """Test /ready endpoint when database is healthy"""
        with patch('api.check_db_health', return_value=True):
            response = client.get('/ready')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'ready'
            assert data['database'] == 'connected'

    def test_ready_endpoint_failure(self, client):
        """Test /ready endpoint when database is unhealthy"""
        with patch('api.check_db_health', return_value=False):
            response = client.get('/ready')
            assert response.status_code == 503
            data = json.loads(response.data)
            assert data['status'] == 'not ready'
            assert data['database'] == 'disconnected'

    def test_metrics_endpoint(self, client):
        """Test /metrics endpoint returns Prometheus metrics"""
        response = client.get('/metrics')
        assert response.status_code == 200
        assert b'api_requests_total' in response.data or b'python_' in response.data

class TestWeatherEndpoints:
    """Test weather data endpoints"""

    def test_current_weather_success(self, client, mock_db_connection):
        """Test /api/weather/current endpoint with data"""
        # Mock database response
        mock_db_connection.fetchone.return_value = {
            'id': 1,
            'temperature': 22.5,
            'humidity': 65.0,
            'pressure': 1013.0,
            'timestamp': datetime.now(),
            'city': 'Mississauga',
            'country': 'Canada'
        }

        response = client.get('/api/weather/current')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['temperature'] == 22.5
        assert data['city'] == 'Mississauga'
        assert 'timestamp' in data

    def test_current_weather_no_data(self, client, mock_db_connection):
        """Test /api/weather/current endpoint with no data"""
        mock_db_connection.fetchone.return_value = None

        response = client.get('/api/weather/current')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_weather_history_default(self, client, mock_db_connection):
        """Test /api/weather/history endpoint with default parameters"""
        # Mock database response
        mock_db_connection.fetchall.return_value = [
            {
                'id': 1,
                'temperature': 22.5,
                'humidity': 65.0,
                'pressure': 1013.0,
                'timestamp': datetime.now(),
                'city': 'Mississauga',
                'country': 'Canada'
            },
            {
                'id': 2,
                'temperature': 21.0,
                'humidity': 70.0,
                'pressure': 1012.0,
                'timestamp': datetime.now() - timedelta(hours=1),
                'city': 'Mississauga',
                'country': 'Canada'
            }
        ]

        response = client.get('/api/weather/history')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]['temperature'] == 22.5

    def test_weather_history_custom_params(self, client, mock_db_connection):
        """Test /api/weather/history endpoint with custom parameters"""
        mock_db_connection.fetchall.return_value = []

        response = client.get('/api/weather/history?hours=48&limit=50')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_weather_stats_success(self, client, mock_db_connection):
        """Test /api/weather/stats endpoint with data"""
        mock_db_connection.fetchone.return_value = {
            'record_count': 10,
            'avg_temperature': 22.5,
            'min_temperature': 18.0,
            'max_temperature': 25.0,
            'avg_humidity': 65.0,
            'min_humidity': 55.0,
            'max_humidity': 75.0,
            'avg_pressure': 1013.0,
            'min_pressure': 1010.0,
            'max_pressure': 1015.0,
            'oldest_record': datetime.now() - timedelta(hours=24),
            'newest_record': datetime.now()
        }

        response = client.get('/api/weather/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['record_count'] == 10
        assert data['avg_temperature'] == 22.5
        assert 'oldest_record' in data
        assert 'newest_record' in data

    def test_weather_stats_no_data(self, client, mock_db_connection):
        """Test /api/weather/stats endpoint with no data"""
        mock_db_connection.fetchone.return_value = {'record_count': 0}

        response = client.get('/api/weather/stats')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

class TestCORS:
    """Test CORS headers"""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses"""
        response = client.get('/health')
        assert 'Access-Control-Allow-Origin' in response.headers

class TestErrorHandlers:
    """Test error handlers"""

    def test_404_handler(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

class TestDatabaseConfig:
    """Test database configuration parsing"""

    def test_database_url_parsing(self):
        """Test parsing of DATABASE_URL environment variable"""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://testuser:testpass@testhost:5433/testdb'
        }):
            config = get_db_config()
            assert config['host'] == 'testhost'
            assert config['database'] == 'testdb'
            assert config['user'] == 'testuser'
            assert config['password'] == 'testpass'
            assert config['port'] == 5433

    def test_individual_env_vars(self):
        """Test using individual environment variables"""
        with patch.dict(os.environ, {
            'DB_HOST': 'localhost',
            'DB_NAME': 'weather_db',
            'DB_USER': 'postgres',
            'DB_PASSWORD': 'postgres'
        }, clear=True):
            # Remove DATABASE_URL if it exists
            if 'DATABASE_URL' in os.environ:
                del os.environ['DATABASE_URL']

            config = get_db_config()
            assert config['host'] == 'localhost'
            assert config['database'] == 'weather_db'
            assert config['user'] == 'postgres'
