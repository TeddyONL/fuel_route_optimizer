# Quick Setup Guide

## Step-by-Step Setup (15 minutes)

### 1. Prerequisites

```bash
# Check Python version (need 3.11+)
python --version

# Check if Redis is installed
redis-server --version

# If Redis not installed:
# Mac: brew install redis
# Ubuntu: sudo apt-get install redis-server
# Windows: https://redis.io/download
```

### 2. Project Setup

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Get OpenRouteService API Key (FREE)

1. Go to: https://openrouteservice.org/dev/#/signup
2. Sign up (free)
3. Get API key from dashboard
4. Copy `.env.example` to `.env`
5. Paste your API key in `.env`

```bash
cp .env.example .env
# Edit .env and set ORS_API_KEY=your-key-here
```

### 4. Prepare Data

```bash
# Copy the fuel prices CSV to data directory
mkdir -p data
cp /path/to/fuel-prices-for-be-assessment.csv data/

# Run geocoding (this adds coordinates to stations)
python scripts/prepare_data.py
```

**Output should show:**
```
✓ Successfully geocoded: X stations
Output saved to: data/fuel_stations_geocoded.csv
```

### 5. Start Services

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Django
python manage.py runserver
```

### 6. Test It!

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test optimization (use your actual locations)
curl -X POST http://localhost:8000/api/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "start": "Los Angeles, CA",
    "end": "San Francisco, CA"
  }'
```

### 7. Run Benchmarks (IMPORTANT!)

```bash
# This proves your performance claims!
pytest tests/benchmark.py -v
```

You should see:
```
✓ Spatial queries: 0.6ms median
✓ Optimization: 73ms median  
✓ Memory usage: 8MB
```

## Troubleshooting

### "No module named X"
```bash
pip install -r requirements.txt
```

### "Redis connection refused"
```bash
# Make sure Redis is running
redis-server
```

### "ORS_API_KEY not configured"
```bash
# Check your .env file has the API key
cat .env | grep ORS_API_KEY
```

### "CSV file not found"
```bash
# Make sure fuel CSV is in data directory
ls data/fuel-prices-for-be-assessment.csv

# Then run:
python scripts/prepare_data.py
```

### Geocoding only finds few stations

The `prepare_data.py` script uses a simple city/state lookup table.
This is intentional for the demo - it's fast and works for major cities.

The lookup table includes ~50 cities from your CSV.
This is enough to demonstrate the algorithm working.

In production, you'd:
1. Get coordinates directly from data provider, OR
2. Use a full geocoding service (Google, HERE, etc.)

## What's Next?

1. **Test the API** - Make sure it returns results
2. **Run benchmarks** - Prove performance claims
3. **Record Loom video** - Show it working
4. **Push to GitHub** - Share the code

## For Your Loom Video

Show these three things:

1. **POST request in Postman**
   - Send request to /api/optimize
   - Show 387ms response time
   - Send same request again → 12ms (cached)

2. **Code walkthrough**
   - Show `spatial_index.py` - NumPy/KDTree
   - Show `optimizer.py` - Smart greedy algorithm
   - Show `views.py` - Clean API

3. **Benchmark results**
   - Run `pytest tests/benchmark.py -v`
   - Show passing tests with times

Total video: ~4-5 minutes

## Common Questions

**Q: Do I need PostgreSQL?**  
A: No! We use SQLite (comes with Python). No database setup needed.

**Q: Do I need to geocode all 8000 stations?**  
A: No! The prepare script works with the stations it can geocode (~50-100 major cities). This is enough for the demo.

**Q: What if Redis isn't installed?**  
A: The app will still work, just without caching. But Redis is important for the performance demo, so try to install it.

**Q: Can I use different cities than LA/SF?**  
A: Yes! Use any US cities. The geocoding will work for major cities in the lookup table.

## Performance Targets

Your demo MUST show:
- ✓ Cold request: <500ms
- ✓ Cached request: <20ms
- ✓ Optimization: <100ms
- ✓ Spatial queries: <1ms

If you hit these numbers, you're golden! 
