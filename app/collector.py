"""
Weather Data Collector Service
Background worker that polls WeatherAPI.com and stores data in PostgreSQL
"""
import os
import time
import logging
import signal
import sys
from datetime import datetime
from urllib.parse import urlparse
import requests
import psycopg2
from psycopg2 import OperationalError
from prometheus_client import Counter, Gauge, Histogram
try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_format = os.getenv('LOG_FORMAT', 'TEXT').upper()

root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Clear existing handlers to avoid duplicates
if root_logger.handlers:
    root_logger.handlers = []

handler = logging.StreamHandler()

if log_format == 'JSON' and jsonlogger:
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
else:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

root_logger.addHandler(handler)
logger = logging.getLogger(__name__)

# Prometheus Metrics
weather_api_requests_total = Counter(
    'weather_api_requests_total',
    'Total number of weather API requests'
)
weather_api_errors_total = Counter(
    'weather_api_errors_total',
    'Total number of weather API errors'
)
db_operations_total = Counter(
    'db_operations_total',
    'Total number of database operations',
    ['operation']
)
db_errors_total = Counter(
    'db_errors_total',
    'Total number of database errors'
)
current_temperature = Gauge(
    'current_temperature_celsius',
    'Current temperature in Celsius',
    ['city', 'country']
)
current_humidity = Gauge(
    'current_humidity_percent',
    'Current humidity percentage',
    ['city', 'country']
)
current_pressure = Gauge(
    'current_pressure_mb',
    'Current atmospheric pressure in millibars',
    ['city', 'country']
)
weather_fetch_duration = Histogram(
    'weather_fetch_duration_seconds',
    'Time spent fetching weather data'
)

class WeatherDB:
    """Database handler for weather data storage"""

    def __init__(self):
        # Check for DATABASE_URL first (Railway/Heroku style)
        database_url = os.getenv('DATABASE_URL')

        if database_url:
            # Parse DATABASE_URL: postgresql://user:password@host:port/dbname
            parsed = urlparse(database_url)
            self.host = parsed.hostname
            self.database = parsed.path[1:]  # Remove leading '/'
            self.user = parsed.username
            self.password = parsed.password
            self.port = parsed.port or 5432
        else:
            # Use individual environment variables
            self.host = os.getenv('DB_HOST', 'postgres')
            self.database = os.getenv('DB_NAME', 'weather_db')
            self.user = os.getenv('DB_USER', 'postgres')
            self.password = os.getenv('DB_PASSWORD', 'postgres')
            self.port = int(os.getenv('DB_PORT', 5432))

    def get_connection(self):
        """Create and return a database connection"""
        return psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password,
            port=self.port
        )

    def init_db(self):
        """Initialize the database and create table if it doesn't exist"""
        try:
            db_operations_total.labels(operation='init').inc()
            conn = self.get_connection()
            cur = conn.cursor()

            cur.execute('''
                CREATE TABLE IF NOT EXISTS weather_data (
                    id SERIAL PRIMARY KEY,
                    temperature FLOAT NOT NULL,
                    humidity FLOAT,
                    pressure FLOAT,
                    timestamp TIMESTAMP NOT NULL,
                    city VARCHAR(100) NOT NULL,
                    country VARCHAR(100) NOT NULL
                );
            ''')

            conn.commit()
            logger.info("Database initialized successfully")
        except OperationalError as e:
            db_errors_total.inc()
            logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    def store_weather_data(self, data):
        """Store weather data in the database"""
        try:
            db_operations_total.labels(operation='insert').inc()
            conn = self.get_connection()
            cur = conn.cursor()

            cur.execute(
                '''INSERT INTO weather_data
                   (temperature, humidity, pressure, timestamp, city, country)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (data['temperature'],
                 data.get('humidity'),
                 data.get('pressure'),
                 data['timestamp'],
                 data['city'],
                 data['country'])
            )

            conn.commit()
            logger.info(f"Weather data stored successfully for {data['city']}, {data['country']}")
        except Exception as e:
            db_errors_total.inc()
            logger.error(f"Failed to store weather data: {e}")
            raise
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()


class WeatherAPI:
    """Weather API client for fetching data from WeatherAPI.com"""

    def __init__(self):
        self.api_key = os.getenv('WEATHER_API_KEY')
        if not self.api_key:
            raise ValueError("WEATHER_API_KEY environment variable is not set")
        self.city = os.getenv('CITY', 'Mississauga')
        self.country = os.getenv('COUNTRY', 'Canada')
        self.location = f"{self.city},{self.country}"

    def get_weather_data(self):
        """Fetch weather data from WeatherAPI.com"""
        url = f"http://api.weatherapi.com/v1/current.json?key={self.api_key}&q={self.location}"
        try:
            weather_api_requests_total.inc()
            start_time = time.time()

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            weather_fetch_duration.observe(time.time() - start_time)

            # Update Prometheus gauges
            current_temperature.labels(city=self.city, country=self.country).set(data['current']['temp_c'])
            current_humidity.labels(city=self.city, country=self.country).set(data['current']['humidity'])
            current_pressure.labels(city=self.city, country=self.country).set(data['current']['pressure_mb'])

            return {
                'temperature': data['current']['temp_c'],
                'humidity': data['current']['humidity'],
                'pressure': data['current']['pressure_mb'],
                'timestamp': datetime.now(),
                'city': self.city,
                'country': self.country
            }
        except requests.exceptions.RequestException as e:
            weather_api_errors_total.inc()
            logger.error(f"Failed to fetch weather data: {e}")
            return None


# Graceful shutdown flag
shutdown_flag = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_flag
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag = True

def main():
    """Main application entry point"""
    global shutdown_flag

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize components
    try:
        weather_db = WeatherDB()
        weather_db.init_db()
        weather_api = WeatherAPI()

        logger.info(f"Starting weather data collection for {weather_api.city}, {weather_api.country}")
        logger.info(f"Update interval: {os.getenv('UPDATE_INTERVAL', 300)} seconds")

        while not shutdown_flag:
            try:
                weather_data = weather_api.get_weather_data()
                if weather_data:
                    logger.info(f"Location: {weather_data['city']}, {weather_data['country']}, "
                              f"Temperature: {weather_data['temperature']}°C, "
                              f"Humidity: {weather_data['humidity']}%, "
                              f"Pressure: {weather_data['pressure']}mb")
                    weather_db.store_weather_data(weather_data)

                # Use smaller sleep intervals to check shutdown flag more frequently
                update_interval = int(os.getenv('UPDATE_INTERVAL', 300))
                for _ in range(update_interval):
                    if shutdown_flag:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry

        logger.info("Shutting down gracefully...")
        logger.info("Collector stopped")

    except Exception as e:
        logger.critical(f"Critical error: {e}")
        raise

if __name__ == "__main__":
    main()
