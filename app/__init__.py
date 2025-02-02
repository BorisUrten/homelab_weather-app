"""
Weather Monitoring System
A Python application for collecting and storing weather data using Kubernetes.
"""

from weather_app import WeatherAPI, WeatherDB

__version__ = '1.0.0'
__author__ = 'Your Name'
__license__ = 'MIT'

# Make key classes available at package level
__all__ = ['WeatherAPI', 'WeatherDB']