'use client';

import { useEffect, useState } from 'react';
import { getCurrentWeather, getWeatherStats, type WeatherData, type WeatherStats } from '@/lib/api';
import { formatTemperature, formatPercentage, formatPressure, formatDate } from '@/lib/utils';
import { CloudRain, Droplets, Gauge, RefreshCw, Sun, Moon } from 'lucide-react';
import { useTheme } from 'next-themes';
import { toast } from 'sonner';

export default function Dashboard() {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [stats, setStats] = useState<WeatherStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const { theme, setTheme } = useTheme();

  const fetchData = async () => {
    try {
      setError(null);
      const [currentWeather, weatherStats] = await Promise.all([
        getCurrentWeather(),
        getWeatherStats(24),
      ]);
      setWeather(currentWeather);
      setStats(weatherStats);
      setLastUpdated(new Date());
      toast.success('Weather data updated');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch weather data';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-700 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center">
        <div className="text-white text-2xl flex items-center gap-3">
          <RefreshCw className="h-8 w-8 animate-spin" />
          Loading weather data...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center">
        <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-xl max-w-md">
          <h2 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">Error</h2>
          <p className="text-gray-700 dark:text-gray-300 mb-4">{error}</p>
          <button
            onClick={fetchData}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded flex items-center justify-center gap-2"
          >
            <RefreshCw className="h-5 w-5" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!weather) {
    return <div className="min-h-screen flex items-center justify-center">No data available</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-700 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Header */}
      <header className="bg-white/10 dark:bg-black/20 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <CloudRain className="h-8 w-8 text-white" />
            <h1 className="text-2xl font-bold text-white">Weather Monitor</h1>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
            >
              {theme === 'dark' ? (
                <Sun className="h-5 w-5 text-yellow-300" />
              ) : (
                <Moon className="h-5 w-5 text-gray-200" />
              )}
            </button>
            <button
              onClick={fetchData}
              className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Location and Time */}
        <div className="text-center mb-8">
          <h2 className="text-4xl font-bold text-white mb-2">
            {weather.city}, {weather.country}
          </h2>
          <p className="text-white/80 text-lg">
            {formatDate(weather.timestamp)}
          </p>
          <p className="text-white/60 text-sm mt-1">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>

        {/* Current Weather Card */}
        <div className="glass rounded-3xl p-8 mb-8 text-center">
          <div className="text-8xl font-bold text-white mb-4">
            {formatTemperature(weather.temperature)}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
            <div className="flex flex-col items-center">
              <Droplets className="h-8 w-8 text-blue-300 mb-2" />
              <div className="text-3xl font-semibold text-white">
                {formatPercentage(weather.humidity)}
              </div>
              <div className="text-white/70 mt-1">Humidity</div>
            </div>
            <div className="flex flex-col items-center">
              <Gauge className="h-8 w-8 text-purple-300 mb-2" />
              <div className="text-3xl font-semibold text-white">
                {formatPressure(weather.pressure)}
              </div>
              <div className="text-white/70 mt-1">Pressure</div>
            </div>
            <div className="flex flex-col items-center">
              <Sun className="h-8 w-8 text-yellow-300 mb-2" />
              <div className="text-3xl font-semibold text-white">
                {weather.temperature > 20 ? 'Warm' : 'Cool'}
              </div>
              <div className="text-white/70 mt-1">Feels Like</div>
            </div>
          </div>
        </div>

        {/* Statistics Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Temperature Stats */}
            <div className="glass rounded-2xl p-6">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <Sun className="h-5 w-5 text-yellow-300" />
                Temperature (24h)
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-white/70">Average</span>
                  <span className="text-white font-semibold">
                    {formatTemperature(stats.avg_temperature)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70">High</span>
                  <span className="text-red-300 font-semibold">
                    {formatTemperature(stats.max_temperature)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70">Low</span>
                  <span className="text-blue-300 font-semibold">
                    {formatTemperature(stats.min_temperature)}
                  </span>
                </div>
              </div>
            </div>

            {/* Humidity Stats */}
            <div className="glass rounded-2xl p-6">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <Droplets className="h-5 w-5 text-blue-300" />
                Humidity (24h)
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-white/70">Average</span>
                  <span className="text-white font-semibold">
                    {formatPercentage(stats.avg_humidity)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70">High</span>
                  <span className="text-blue-300 font-semibold">
                    {formatPercentage(stats.max_humidity)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70">Low</span>
                  <span className="text-blue-300 font-semibold">
                    {formatPercentage(stats.min_humidity)}
                  </span>
                </div>
              </div>
            </div>

            {/* Pressure Stats */}
            <div className="glass rounded-2xl p-6">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <Gauge className="h-5 w-5 text-purple-300" />
                Pressure (24h)
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-white/70">Average</span>
                  <span className="text-white font-semibold">
                    {formatPressure(stats.avg_pressure)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70">High</span>
                  <span className="text-purple-300 font-semibold">
                    {formatPressure(stats.max_pressure)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70">Low</span>
                  <span className="text-purple-300 font-semibold">
                    {formatPressure(stats.min_pressure)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Data Count */}
        {stats && (
          <div className="mt-6 text-center">
            <p className="text-white/70">
              Based on {stats.record_count} measurements in the last 24 hours
            </p>
          </div>
        )}

        {/* Navigation */}
        <div className="mt-8 flex justify-center gap-4">
          <a
            href="/history"
            className="glass px-6 py-3 rounded-lg text-white font-medium hover:bg-white/20 transition-colors"
          >
            View History
          </a>
          <a
            href="/about"
            className="glass px-6 py-3 rounded-lg text-white font-medium hover:bg-white/20 transition-colors"
          >
            About
          </a>
        </div>
      </main>
    </div>
  );
}
