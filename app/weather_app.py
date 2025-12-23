import os
import time
import logging
import signal
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import requests
import psycopg2
from psycopg2 import OperationalError
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
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

# Health check state
app_healthy = True
db_healthy = False

class WeatherDB:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'postgres')
        self.database = os.getenv('DB_NAME', 'weather_db')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')

    def get_connection(self):
        return psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password
        )

    def init_db(self):
        """Initialize the database and create table if it doesn't exist"""
        global db_healthy
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
            db_healthy = True
            logger.info("Database initialized successfully")
        except OperationalError as e:
            db_healthy = False
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

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health checks and metrics"""
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests for health, readiness, and metrics"""
        if self.path == '/health':
            # Liveness probe - application is running
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy' if app_healthy else 'unhealthy',
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(str(response).encode())
            
        elif self.path == '/ready':
            # Readiness probe - application is ready to serve traffic
            if db_healthy:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'status': 'ready',
                    'database': 'connected',
                    'timestamp': datetime.now().isoformat()
                }
                self.wfile.write(str(response).encode())
            else:
                self.send_response(503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'status': 'not ready',
                    'database': 'disconnected',
                    'timestamp': datetime.now().isoformat()
                }
                self.wfile.write(str(response).encode())
                
        elif self.path == '/metrics':
            # Prometheus metrics endpoint
            self.send_response(200)
            self.send_header('Content-type', CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(generate_latest())
            
        else:
            self.send_response(404)
            self.end_headers()


def start_health_server(port=8080):
    """Start the health check HTTP server in a separate thread"""
    server = HTTPServer(('', port), HealthCheckHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Health check server started on port {port}")
    return server


class WeatherAPI:
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
    global shutdown_flag, app_healthy
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag = True
    app_healthy = False

def main():
    """Main application entry point"""
    global shutdown_flag, app_healthy
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start health check server
    health_port = int(os.getenv('HEALTH_PORT', 8080))
    health_server = start_health_server(health_port)
    
    # Initialize components
    try:
        weather_db = WeatherDB()
        weather_db.init_db()
        weather_api = WeatherAPI()
        
        logger.info(f"Starting weather data collection for {weather_api.city}, {weather_api.country}")
        logger.info(f"Health endpoints available at :{health_port}/health, :{health_port}/ready, :{health_port}/metrics")
        
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
        health_server.shutdown()
        logger.info("Application stopped")
        
    except Exception as e:
        logger.critical(f"Critical error: {e}")
        app_healthy = False
        raise

if __name__ == "__main__":
    main()