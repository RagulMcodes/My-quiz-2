# ☁️ Cloud Deployment Guide - Production-Ready Quiz Server

## 🎯 Changes Made for Cloud Deployment

### ✅ MUST CHANGE (Implemented)

#### 1️⃣ Dynamic Port with 0.0.0.0 Binding
**Before:**
```python
async with websockets.serve(handle_client, "localhost", 8765):
```

**After:**
```python
port = int(os.environ.get("PORT", 8765))
async with websockets.serve(
    handle_client,
    "0.0.0.0",  # Bind to all interfaces
    port,       # Dynamic port from environment
    ping_interval=20,
    ping_timeout=20
):
```

**Why Critical:**
- `localhost` only accepts local connections - cloud won't work
- Cloud platforms assign random ports via `PORT` env variable
- `0.0.0.0` allows external connections

#### 2️⃣ Updated Startup Messages
**Before:**
```python
print("🌐 Server running on ws://localhost:8765")
```

**After:**
```python
print(f"🌐 Server running on port {port}")
```

**Why:** Prevents confusion when actual port is different

### ✅ SHOULD CHANGE (Implemented)

#### 3️⃣ Ping/Pong for Connection Health
**Added:**
```python
ping_interval=20,  # Send ping every 20 seconds
ping_timeout=20    # Disconnect if no pong in 20 seconds
```

**Why:** Cloud networks drop idle WebSocket connections - this prevents ghost users

#### 4️⃣ JSON Message Validation
**Before:**
```python
data = json.loads(message)
action = data.get("action")
```

**After:**
```python
try:
    data = json.loads(message)
except json.JSONDecodeError:
    print(f"⚠️  Invalid JSON from {user_id}")
    continue
except Exception as e:
    print(f"⚠️  Message parse error: {e}")
    continue

action = data.get("action")
```

**Why:** One bad packet won't crash the entire connection loop

#### 5️⃣ LLM Timeout Protection
**Before:**
```python
llm_questions = await loop.run_in_executor(
    None, 
    generate_quiz, 
    room.num_questions, 
    room.topic
)
```

**After:**
```python
try:
    llm_questions = await asyncio.wait_for(
        loop.run_in_executor(
            None, 
            generate_quiz, 
            room.num_questions, 
            room.topic
        ),
        timeout=20.0  # 20 second timeout
    )
except asyncio.TimeoutError:
    print(f"⚠️  LLM timeout for room {room_id}, using fallback questions")
    llm_questions = generate_quiz(5, "general knowledge")
except Exception as e:
    print(f"❌ LLM error for room {room_id}: {e}, using fallback")
    llm_questions = generate_quiz(5, "general knowledge")
```

**Why:** If Groq API hangs, room doesn't freeze forever - graceful fallback

## 🚀 Deployment Options

### Option 1: Railway (Easiest)

**Step 1: Create `Procfile`**
```
web: python quiz_server_production.py
```

**Step 2: Create `requirements.txt`**
```
websockets==12.0
langchain-groq==0.2.1
langchain-core==0.3.28
python-dotenv==1.0.0
```

**Step 3: Deploy**
1. Push to GitHub
2. Connect Railway to your repo
3. Add environment variable: `GROQ_API_KEY`
4. Railway auto-deploys!

**Cost:** Free tier available

---

### Option 2: Render

**Step 1: Create `render.yaml`**
```yaml
services:
  - type: web
    name: quiz-server
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python quiz_server_production.py
    envVars:
      - key: GROQ_API_KEY
        sync: false
```

**Step 2: Deploy**
1. Push to GitHub
2. Connect Render to your repo
3. Add `GROQ_API_KEY` in dashboard
4. Deploy!

**Cost:** Free tier available

---

### Option 3: Heroku

**Step 1: Create `Procfile`**
```
web: python quiz_server_production.py
```

**Step 2: Create `runtime.txt`**
```
python-3.11.0
```

**Step 3: Deploy**
```bash
heroku create quiz-game-server
heroku config:set GROQ_API_KEY=your_key_here
git push heroku main
```

**Cost:** Paid (no free tier anymore)

---

### Option 4: Fly.io

**Step 1: Create `fly.toml`**
```toml
app = "quiz-game"

[build]
  builder = "paketobuildpacks/builder:base"

[[services]]
  http_checks = []
  internal_port = 8080
  protocol = "tcp"
  
  [[services.ports]]
    port = 80
    handlers = ["http"]
  
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

[env]
  PORT = "8080"
```

**Step 2: Deploy**
```bash
fly launch
fly secrets set GROQ_API_KEY=your_key_here
fly deploy
```

**Cost:** Free tier available

---

### Option 5: Google Cloud Run

**Step 1: Create `Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY quiz_server_production.py .
COPY .env .

CMD ["python", "quiz_server_production.py"]
```

**Step 2: Deploy**
```bash
gcloud run deploy quiz-server \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=your_key_here
```

**Cost:** Pay per use (free tier available)

---

### Option 6: AWS EC2 (Full Control)

**Step 1: Launch EC2 instance**
- Ubuntu 22.04
- t2.micro (free tier)
- Open port 8765 in security group

**Step 2: SSH and setup**
```bash
ssh -i key.pem ubuntu@your-ip

# Install Python
sudo apt update
sudo apt install python3-pip

# Clone your code
git clone your-repo
cd your-repo

# Install dependencies
pip3 install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_key" > .env

# Run with systemd
sudo nano /etc/systemd/system/quiz.service
```

**quiz.service:**
```ini
[Unit]
Description=Quiz Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/your-repo
ExecStart=/usr/bin/python3 quiz_server_production.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start service:**
```bash
sudo systemctl enable quiz
sudo systemctl start quiz
```

**Cost:** Free tier for 12 months

---

## 🔒 Environment Variables Required

All platforms need these:

```bash
GROQ_API_KEY=your_groq_api_key_here
PORT=8765  # Optional - cloud platforms set this automatically
```

## 🌐 Frontend Configuration

### Update WebSocket URL in Frontend

**For Production (Cloud Server):**

**Vue (`src/components/ConnectionScreen.vue`):**
```vue
const serverUrl = ref('wss://your-app.railway.app')
```

**Svelte (`src/lib/ConnectionScreen.svelte`):**
```svelte
let serverUrl = 'wss://your-app.railway.app'
```

**Important Notes:**
- Use `wss://` (secure WebSocket) for HTTPS sites
- Use `ws://` only for local development
- Most cloud platforms provide HTTPS/WSS automatically

### CORS Configuration (If Needed)

If frontend and backend are on different domains, you may need CORS headers. Most WebSocket libraries handle this automatically, but if you get CORS errors:

```python
# Add to websockets.serve():
async with websockets.serve(
    handle_client,
    "0.0.0.0",
    port,
    ping_interval=20,
    ping_timeout=20,
    # Add origin checking if needed
    origins=["https://your-frontend.netlify.app", "http://localhost:5173"]
):
```

## 📊 Testing Your Deployment

### 1. Check Server is Running
```bash
# Test WebSocket connection
wscat -c wss://your-server.com

# Or use this Python script:
python -c "import websockets, asyncio; asyncio.run(websockets.connect('wss://your-server.com'))"
```

### 2. Monitor Logs
```bash
# Railway
railway logs

# Render
render logs

# Heroku
heroku logs --tail

# Fly.io
fly logs
```

### 3. Load Test (Optional)
```bash
# Install artillery
npm install -g artillery

# Create test.yml
artillery quick --count 10 --num 50 wss://your-server.com
```

## 🐛 Common Issues

### Issue 1: WebSocket Connection Refused
**Problem:** Frontend can't connect to server

**Solutions:**
1. Check server is actually running
2. Verify WebSocket port is open
3. Use `wss://` not `ws://` for HTTPS sites
4. Check firewall rules

### Issue 2: Server Crashes on Deploy
**Problem:** Server exits immediately

**Solutions:**
1. Check environment variables are set
2. Verify `GROQ_API_KEY` is valid
3. Check server logs for Python errors
4. Ensure all dependencies are in requirements.txt

### Issue 3: LLM Timeout Issues
**Problem:** Questions not generating

**Solutions:**
1. Check Groq API key is valid
2. Verify internet connectivity
3. Fallback questions will be used automatically
4. Check Groq API rate limits

### Issue 4: Ghost Connections
**Problem:** Players shown as connected but aren't

**Solutions:**
- Already fixed with `ping_interval` and `ping_timeout`
- Increase timeout if needed: `ping_timeout=30`

## 📈 Scaling Considerations

### Current Limitations (Single Server)
- In-memory storage (`rooms = {}`)
- Won't scale beyond 1 server instance
- All state lost on restart

### Future: Multi-Server Setup
When you need to scale beyond 1 server:

**Option A: Redis for Shared State**
```python
import redis
r = redis.Redis(host='localhost', port=6379)

# Store rooms in Redis
r.set(f"room:{room_id}", json.dumps(room_data))
```

**Option B: Sticky Sessions**
Configure load balancer to route same user to same server

**Option C: Database**
Store game state in PostgreSQL/MongoDB

**When to Scale:**
- You're fine with single server up to ~1000 concurrent users
- Don't overthink scaling until you need it

## 🎯 Production Checklist

Before going live:

- [ ] Environment variables set (`GROQ_API_KEY`)
- [ ] Server runs on `0.0.0.0` not `localhost`
- [ ] Dynamic `PORT` from environment
- [ ] Ping/pong enabled for connection health
- [ ] JSON validation in message handler
- [ ] LLM timeout protection enabled
- [ ] Frontend points to production server URL
- [ ] Using `wss://` for secure connections
- [ ] Tested with multiple concurrent users
- [ ] Monitoring/logging set up
- [ ] Error alerts configured (optional)

## 💰 Cost Estimation

**Free Tier Options:**
- Railway: 500 hours/month free
- Render: 750 hours/month free
- Fly.io: 3 shared-cpu instances free
- Google Cloud Run: 2M requests/month free

**Expected Costs (if exceed free tier):**
- Railway: ~$5-10/month
- Render: ~$7/month
- Fly.io: ~$5/month
- AWS EC2: ~$3-5/month (t2.micro)

**LLM Costs (Groq):**
- Free tier: 30 requests/min
- Paid: Very cheap (~$0.50/1M tokens)

## 🚀 Quick Deploy Commands

**Railway:**
```bash
railway login
railway init
railway up
railway variables set GROQ_API_KEY=your_key
```

**Render:**
```bash
# Just connect GitHub repo in dashboard
```

**Fly.io:**
```bash
fly launch
fly secrets set GROQ_API_KEY=your_key
fly deploy
```

## 📚 Additional Resources

- [WebSockets on Heroku](https://devcenter.heroku.com/articles/websockets)
- [Railway WebSocket Guide](https://docs.railway.app/deploy/exposing-your-app#websockets)
- [Render WebSocket Support](https://render.com/docs/websockets)
- [Fly.io WebSocket Docs](https://fly.io/docs/reference/configuration/#websockets)

## 🎉 You're Production Ready!

Your server is now:
- ✅ Cloud-deployment ready
- ✅ Crash-resistant
- ✅ Timeout-protected
- ✅ Connection-health aware
- ✅ Input-validated

Deploy with confidence! 🚀
