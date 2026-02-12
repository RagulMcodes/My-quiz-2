#!/bin/bash

# 🚀 Quick Deploy to Railway
# This script sets up your project for Railway deployment

echo "🎮 AI Quiz Battle - Railway Deployment Setup"
echo "=============================================="
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null
then
    echo "❌ Railway CLI not found!"
    echo "📥 Install it: npm install -g @railway/cli"
    echo "   Then run this script again."
    exit 1
fi

echo "✅ Railway CLI found"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found"
    echo "📝 Creating .env template..."
    echo "GROQ_API_KEY=your_groq_api_key_here" > .env
    echo "✅ Created .env file - please edit it with your Groq API key"
    exit 1
fi

# Check if GROQ_API_KEY is set
if grep -q "your_groq_api_key_here" .env; then
    echo "⚠️  Please edit .env and add your real Groq API key"
    exit 1
fi

echo "✅ .env file configured"
echo ""

# Initialize Railway project
echo "🚂 Initializing Railway project..."
railway login

echo ""
echo "📦 Creating new Railway project..."
railway init

echo ""
echo "🔐 Setting environment variables..."
source .env
railway variables set GROQ_API_KEY="$GROQ_API_KEY"

echo ""
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Get your deployment URL: railway domain"
echo "2. Update frontend to use: wss://your-app.railway.app"
echo "3. Test your deployment!"
echo ""
echo "📊 View logs: railway logs"
echo "🔧 Open dashboard: railway open"
echo ""
echo "🎉 Happy gaming!"
