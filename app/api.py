"""
Flask REST API for Weather Monitoring Application
Provides endpoints for frontend to access current weather and historical data
"""
import os
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from urllib.parse import urlparse

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# CORS Configuration
frontend_url = os.getenv('FRONTEND_URL', '*')
CORS(app, origins=[frontend_url, 'http://localhost:3000', 'http://localhost:3001'])

# Prometheus Metrics for API
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status']
)
api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

# Database connection configuration
def get_db_config():
    """Parse DATABASE_URL or use individual environment variables"""
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        # Parse Railway/Heroku-style DATABASE_URL
        # Format: postgresql://user:password@host:port/dbname
        parsed = urlparse(database_url)
        return {
            'host': parsed.hostname,
            'database': parsed.path[1:],  # Remove leading '/'
            'user': parsed.username,
            'password': parsed.password,
            'port': parsed.port or 5432
        }
    else:
        # Use individual environment variables
        return {
            'host': os.getenv('DB_HOST', 'db'),
            'database': os.getenv('DB_NAME', 'weather_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'port': int(os.getenv('DB_PORT', 5432))
        }

def get_db_connection():
    """Create and return a database connection"""
    config = get_db_config()
    return psycopg2.connect(**config, cursor_factory=RealDictCursor)

# Health check state
db_healthy = False

def check_db_health():
    """Check if database is accessible"""
    global db_healthy
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        db_healthy = True
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False
        return False

# Health and metrics endpoints
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint (liveness probe)"""
    api_requests_total.labels(method='GET', endpoint='/health', status='200').inc()
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/ready', methods=['GET'])
def ready():
    """Readiness check endpoint (checks database connectivity)"""
    if check_db_health():
        api_requests_total.labels(method='GET', endpoint='/ready', status='200').inc()
        return jsonify({
            'status': 'ready',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200
    else:
        api_requests_total.labels(method='GET', endpoint='/ready', status='503').inc()
        return jsonify({
            'status': 'not ready',
            'database': 'disconnected',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# API Endpoints
@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    """Get the most recent weather data"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('''
            SELECT id, temperature, humidity, pressure, timestamp, city, country
            FROM weather_data
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            # Convert to dict and format timestamp
            weather_data = dict(result)
            weather_data['timestamp'] = weather_data['timestamp'].isoformat()

            api_requests_total.labels(method='GET', endpoint='/api/weather/current', status='200').inc()
            return jsonify(weather_data), 200
        else:
            api_requests_total.labels(method='GET', endpoint='/api/weather/current', status='404').inc()
            return jsonify({'error': 'No weather data available'}), 404

    except Exception as e:
        logger.error(f"Error fetching current weather: {e}")
        api_requests_total.labels(method='GET', endpoint='/api/weather/current', status='500').inc()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@app.route('/api/weather/history', methods=['GET'])
def get_weather_history():
    """
    Get historical weather data
    Query params:
        - hours: number of hours to look back (default: 24)
        - limit: maximum number of records (default: 100, max: 1000)
    """
    try:
        # Parse query parameters
        hours = request.args.get('hours', default=24, type=int)
        limit = request.args.get('limit', default=100, type=int)

        # Validate parameters
        if hours < 1:
            hours = 24
        if limit < 1 or limit > 1000:
            limit = 100

        # Calculate time threshold
        time_threshold = datetime.now() - timedelta(hours=hours)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('''
            SELECT id, temperature, humidity, pressure, timestamp, city, country
            FROM weather_data
            WHERE timestamp >= %s
            ORDER BY timestamp DESC
            LIMIT %s
        ''', (time_threshold, limit))

        results = cur.fetchall()
        cur.close()
        conn.close()

        # Convert to list of dicts and format timestamps
        weather_history = []
        for row in results:
            data = dict(row)
            data['timestamp'] = data['timestamp'].isoformat()
            weather_history.append(data)

        api_requests_total.labels(method='GET', endpoint='/api/weather/history', status='200').inc()
        return jsonify(weather_history), 200

    except Exception as e:
        logger.error(f"Error fetching weather history: {e}")
        api_requests_total.labels(method='GET', endpoint='/api/weather/history', status='500').inc()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@app.route('/api/weather/stats', methods=['GET'])
def get_weather_stats():
    """
    Get weather statistics
    Query params:
        - hours: number of hours to calculate stats for (default: 24)
    """
    try:
        hours = request.args.get('hours', default=24, type=int)
        if hours < 1:
            hours = 24

        time_threshold = datetime.now() - timedelta(hours=hours)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('''
            SELECT
                COUNT(*) as record_count,
                AVG(temperature) as avg_temperature,
                MIN(temperature) as min_temperature,
                MAX(temperature) as max_temperature,
                AVG(humidity) as avg_humidity,
                MIN(humidity) as min_humidity,
                MAX(humidity) as max_humidity,
                AVG(pressure) as avg_pressure,
                MIN(pressure) as min_pressure,
                MAX(pressure) as max_pressure,
                MIN(timestamp) as oldest_record,
                MAX(timestamp) as newest_record
            FROM weather_data
            WHERE timestamp >= %s
        ''', (time_threshold,))

        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and result['record_count'] > 0:
            stats = dict(result)
            # Format timestamps
            stats['oldest_record'] = stats['oldest_record'].isoformat() if stats['oldest_record'] else None
            stats['newest_record'] = stats['newest_record'].isoformat() if stats['newest_record'] else None
            # Round float values
            for key in stats:
                if isinstance(stats[key], float):
                    stats[key] = round(stats[key], 2)

            api_requests_total.labels(method='GET', endpoint='/api/weather/stats', status='200').inc()
            return jsonify(stats), 200
        else:
            api_requests_total.labels(method='GET', endpoint='/api/weather/stats', status='404').inc()
            return jsonify({'error': 'No weather data available for the specified time range'}), 404

    except Exception as e:
        logger.error(f"Error calculating weather stats: {e}")
        api_requests_total.labels(method='GET', endpoint='/api/weather/stats', status='500').inc()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Check database health on startup
check_db_health()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting Flask API server on port {port}")
    logger.info(f"Database config: {get_db_config()['host']}/{get_db_config()['database']}")
    logger.info(f"CORS enabled for: {frontend_url}")

    app.run(host='0.0.0.0', port=port, debug=debug)
