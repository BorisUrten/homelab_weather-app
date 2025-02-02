import os
import time
import logging
from datetime import datetime
import requests
import psycopg2
from psycopg2 import OperationalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS weather_data (
                    id SERIAL PRIMARY KEY,
                    temperature FLOAT NOT NULL,
                    humidity FLOAT,
                    pressure FLOAT,
                    timestamp TIMESTAMP NOT NULL
                );
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
        except OperationalError as e:
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
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute(
                '''INSERT INTO weather_data 
                   (temperature, humidity, pressure, timestamp) 
                   VALUES (%s, %s, %s, %s)''',
                (data['temperature'], 
                 data.get('humidity'), 
                 data.get('pressure'), 
                 data['timestamp'])
            )
            
            conn.commit()
            logger.info("Weather data stored successfully")
        except Exception as e:
            logger.error(f"Failed to store weather data: {e}")
            raise
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

class WeatherAPI:
    def __init__(self):
        self.api_key = os.getenv('WEATHER_API_KEY')
        if not self.api_key:
            raise ValueError("WEATHER_API_KEY environment variable is not set")
        self.city = os.getenv('CITY', 'London')

    def get_weather_data(self):
        """Fetch weather data from WeatherAPI.com"""
        url = f"http://api.weatherapi.com/v1/current.json?key={self.api_key}&q={self.city}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'temperature': data['current']['temp_c'],
                'humidity': data['current']['humidity'],
                'pressure': data['current']['pressure_mb'],
                'timestamp': datetime.now()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch weather data: {e}")
            return None

def main():
    # Initialize components
    try:
        weather_db = WeatherDB()
        weather_db.init_db()
        weather_api = WeatherAPI()
        
        logger.info(f"Starting weather data collection for {weather_api.city}")
        
        while True:
            try:
                weather_data = weather_api.get_weather_data()
                if weather_data:
                    logger.info(f"Temperature: {weather_data['temperature']}°C, "
                              f"Humidity: {weather_data['humidity']}%, "
                              f"Pressure: {weather_data['pressure']}mb")
                    weather_db.store_weather_data(weather_data)
                
                time.sleep(int(os.getenv('UPDATE_INTERVAL', 300)))  # Default 5 minutes
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    except Exception as e:
        logger.critical(f"Critical error: {e}")
        raise

if __name__ == "__main__":
    main()