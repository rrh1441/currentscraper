#!/bin/bash

# Log directory
LOG_DIR=~/CurrentScraper/logs
mkdir -p $LOG_DIR

# Current timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Log files
DEBUG_LOG="${LOG_DIR}/debug_${TIMESTAMP}.log"
SPIDER_LOG="${LOG_DIR}/spider_${TIMESTAMP}.log"
ERROR_LOG="${LOG_DIR}/error_${TIMESTAMP}.log"

echo "Starting spider run at $(date)" | tee -a $DEBUG_LOG

# Set the PATH for the environment
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Navigate to the Scrapy project directory
cd ~/CurrentScraper/Anc

echo "Running spider with verbose output..." | tee -a $DEBUG_LOG

# Run the Scrapy spider with detailed logging
/Users/ryanheger/Library/Python/3.11/bin/scrapy runspider ~/CurrentScraper/Anc/spiders/AncSpider.py \
    --loglevel=DEBUG \
    --set LOG_ENABLED=True \
    --set LOG_LEVEL=DEBUG \
    --set LOG_FILE=$SPIDER_LOG \
    --set LOG_STDOUT=True \
    2> >(tee -a $ERROR_LOG) | tee -a $SPIDER_LOG

echo "Spider run completed at $(date)" | tee -a $DEBUG_LOG

# Display summary
echo -e "\n=== Run Summary ===" | tee -a $DEBUG_LOG
echo "Debug Log: $DEBUG_LOG" | tee -a $DEBUG_LOG
echo "Spider Log: $SPIDER_LOG" | tee -a $DEBUG_LOG
echo "Error Log: $ERROR_LOG" | tee -a $DEBUG_LOG

# Show the last few lines of important log entries
echo -e "\n=== Last Debug Messages ===" | tee -a $DEBUG_LOG
tail -n 10 $SPIDER_LOG | grep "DEBUG" | tee -a $DEBUG_LOG

echo -e "\n=== Last Error Messages ===" | tee -a $DEBUG_LOG
tail -n 10 $ERROR_LOG | tee -a $DEBUG_LOG

echo -e "\n=== Spider Statistics ===" | tee -a $DEBUG_LOG
grep "Scrapy stats" -A 20 $SPIDER_LOG | tee -a $DEBUG_LOG

# Also run the verification script
echo -e "\n=== Verification Results ===" | tee -a $DEBUG_LOG
python3 ~/CurrentScraper/verify_data.py | tee -a $DEBUG_LOG
