#!/bin/bash
# Start ngrok tunnel for frontend (port 5173)

echo "🚀 Starting ngrok tunnel for frontend (port 5173)..."
echo ""
echo "Once started, you'll see a URL like: https://xxxx-xx-xxx-xxx-xxx.ngrok-free.app"
echo "Open this URL on your phone to access the app"
echo ""

ngrok http 5173 --log=stdout
