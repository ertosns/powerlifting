#!/usr/bin/env python3
"""
Monthly Archive Script for Powerlifting Tracker

This script should be run as a cron job at the end of each month.
Example crontab entry (runs at 11:59 PM on the last day of each month):
59 23 L * * /path/to/monthly_archive_cron.py

Or use this for testing (runs every day at midnight):
0 0 * * * /path/to/monthly_archive_cron.py
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from powerlifting import app, db, check_and_archive

def run_archive():
    """Run the monthly archive process"""
    print(f"[{datetime.now()}] Starting monthly archive process...")
    
    with app.app_context():
        try:
            check_and_archive()
            print(f"[{datetime.now()}] Monthly archive completed successfully.")
        except Exception as e:
            print(f"[{datetime.now()}] ERROR: Archive failed - {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    run_archive()
