const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface WeatherData {
  id: number;
  temperature: number;
  humidity: number;
  pressure: number;
  timestamp: string;
  city: string;
  country: string;
}

export interface WeatherStats {
  record_count: number;
  avg_temperature: number;
  min_temperature: number;
  max_temperature: number;
  avg_humidity: number;
  min_humidity: number;
  max_humidity: number;
  avg_pressure: number;
  min_pressure: number;
  max_pressure: number;
  oldest_record: string;
  newest_record: string;
}

export async function getCurrentWeather(): Promise<WeatherData> {
  const res = await fetch(`${API_BASE_URL}/api/weather/current`, {
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch current weather: ${res.statusText}`);
  }

  return res.json();
}

export async function getWeatherHistory(hours: number = 24): Promise<WeatherData[]> {
  const res = await fetch(`${API_BASE_URL}/api/weather/history?hours=${hours}`, {
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch weather history: ${res.statusText}`);
  }

  return res.json();
}

export async function getWeatherStats(hours: number = 24): Promise<WeatherStats> {
  const res = await fetch(`${API_BASE_URL}/api/weather/stats?hours=${hours}`, {
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch weather stats: ${res.statusText}`);
  }

  return res.json();
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, {
      cache: 'no-store',
    });
    return res.ok;
  } catch (error) {
    return false;
  }
}
