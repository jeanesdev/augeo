#!/bin/bash
# Start ngrok tunnel for backend API (port 8000)

echo "🚀 Starting ngrok tunnel for backend API (port 8000)..."
echo ""
echo "Once started, you'll see a URL like: https://xxxx-xx-xxx-xxx-xxx.ngrok-free.app"
echo "Update your frontend .env.local with: VITE_API_URL=https://your-ngrok-url/api/v1"
echo ""

ngrok http 8000 --log=stdout
