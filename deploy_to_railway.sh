#!/bin/bash
# Manual Railway deployment script

echo "🚀 Starting manual Railway deployment..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install it first:"
    echo "npm install -g @railway/cli"
    exit 1
fi

echo "🔐 Logging into Railway..."
railway login

echo "🔗 Linking to your Railway project..."
railway link

echo "📦 Deploying to Railway..."
railway up

echo "📊 Checking deployment status..."
railway status

echo "📝 Viewing logs..."
railway logs --tail

echo "✅ Manual deployment initiated!"
echo "🌐 Check your Railway dashboard for deployment progress"