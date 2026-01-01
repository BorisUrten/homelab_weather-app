# Quick Start Guide

## ✅ What's Ready

Your weather monitoring application is **75% complete** and ready to test!

### Completed:
- ✅ Docker Compose with 4 services
- ✅ Flask REST API backend
- ✅ Background data collector
- ✅ PostgreSQL database
- ✅ Next.js 14 frontend (core dashboard)
- ✅ All Docker configurations
- ✅ Comprehensive test suite

## 🚀 Test It Now (5 Minutes)

### Step 1: Get Weather API Key (2 min)
1. Go to https://www.weatherapi.com/signup.aspx
2. Sign up (free)
3. Copy your API key

### Step 2: Configure Environment (1 min)
```bash
# Copy template
cp .env.docker .env

# Edit .env and replace 'your_weatherapi_key_here' with your actual key
# You can use any text editor (notepad, VS Code, etc.)
```

### Step 3: Install Frontend Dependencies (1 min)
```bash
cd frontend
npm install
cd ..
```

### Step 4: Start Application (1 min)
```bash
docker-compose up --build
```

Wait for all services to start (you'll see logs from 4 services).

### Step 5: Access Application
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/weather/current
- **Health Check**: http://localhost:8000/health

## 🎯 What You'll See

1. **Beautiful Dashboard** with:
   - Current temperature, humidity, pressure
   - Real-time auto-refresh every 30 seconds
   - Dark mode (enabled by default)
   - 24-hour statistics
   - Glassmorphism design

2. **Working Backend**:
   - Data collected every 5 minutes
   - Stored in PostgreSQL
   - REST API serving data

## 🔍 Verify Everything Works

```bash
# Check all containers are running
docker-compose ps

# Should show 4 services: frontend, backend, worker, db

# Check backend health
curl http://localhost:8000/health

# Check current weather data
curl http://localhost:8000/api/weather/current

# View logs
docker-compose logs backend
docker-compose logs worker
```

## 🛑 Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove all data (clean slate)
docker-compose down -v
```

## 📝 Next Steps for Portfolio

1. **Test the application** (5 min) - Make sure everything works
2. **Take screenshots** (10 min) - Dashboard, API responses
3. **Create CI/CD pipeline** (1 hour) - GitHub Actions workflow
4. **Deploy to cloud** (1-2 hours) - Railway + Vercel
5. **Update README** (30 min) - Portfolio-focused documentation

**See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for detailed status and roadmap.**

## ❓ Troubleshooting

### "Failed to fetch weather data"
- Check your API key in `.env` file
- Check worker logs: `docker-compose logs worker`
- Wait a few minutes for first data collection

### "Cannot connect to backend"
- Ensure backend is running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`
- Verify port 8000 is not in use

### Frontend shows blank page
- Check browser console (F12)
- Verify frontend logs: `docker-compose logs frontend`
- Try accessing backend directly: http://localhost:8000/health

### Database connection issues
- Wait 30 seconds for database initialization
- Check db health: `docker-compose logs db`
- Restart: `docker-compose restart db`

## 📞 Need Help?

Check these files:
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Detailed progress
- Backend API code: [app/api.py](app/api.py)
- Frontend code: [frontend/app/page.tsx](frontend/app/page.tsx)
- Docker config: [docker-compose.yml](docker-compose.yml)

---

**Ready to impress clients? Start with `docker-compose up` and watch it work!** 🚀
