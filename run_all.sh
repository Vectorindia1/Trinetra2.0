#!/bin/bash

# Change to the project directory
cd /home/vector/darknet_crawler

# Activate virtual environment
source tor-env/bin/activate

# Start Tor if not already running
if ! pgrep -x "tor" > /dev/null; then
    echo "🟢 Starting Tor service..."
    tor &> tor.log &
    sleep 5
else
    echo "✅ Tor is already running."
fi

# Run Scrapy crawler with proper path
echo "🚀 Starting Darknet Crawler..."
scrapy runspider crawler/spiders/tor_crawler.py -a start_url=$1 &> crawler.log &

# Run Streamlit dashboard
echo "🧪 Launching Streamlit Dashboard..."
streamlit run dashboard.py &> streamlit.log &
