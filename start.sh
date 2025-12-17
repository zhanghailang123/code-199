#!/bin/bash
echo "===================================="
echo "  MEM Study System - Starting..."
echo "===================================="
echo
cd "$(dirname "$0")/web"
echo "Installing dependencies if needed..."
npm install
echo
echo "Starting development server..."
echo
echo "  Open browser: http://localhost:5173"
echo
npm run dev
