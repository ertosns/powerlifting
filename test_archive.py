#!/usr/bin/env python3
"""
Test script for monthly archive functionality
Run this to verify the archive system is working correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from powerlifting import app, db, User, Record, MonthlyArchive, archive_monthly_records, get_current_month
from datetime import datetime, timedelta
import json

def test_archive_system():
    """Test the monthly archive functionality"""
    print("=" * 60)
    print("Testing Monthly Archive System")
    print("=" * 60)
    
    with app.app_context():
        # Create tables
        db.create_all()
        print("✓ Database tables created/verified")
        
        # Check current month
        current = get_current_month()
        print(f"✓ Current month: {current}")
        
        # Count existing data
        users = User.query.count()
        records = Record.query.count()
        archives = MonthlyArchive.query.count()
        
        print(f"✓ Database status:")
        print(f"  - Users: {users}")
        print(f"  - Current records: {records}")
        print(f"  - Archived months: {archives}")
        
        # Test with first user (if exists)
        if users > 0:
            test_user = User.query.first()
            print(f"\n✓ Testing with user: {test_user.email}")
            
            # Get user's records
            user_records = Record.query.filter_by(user_id=test_user.id).all()
            print(f"  - Total records: {len(user_records)}")
            
            # Group by month
            monthly_groups = {}
            for rec in user_records:
                try:
                    rec_date = datetime.strptime(rec.datetime, '%Y-%m-%d')
                    month = rec_date.strftime('%Y-%m')
                    if month not in monthly_groups:
                        monthly_groups[month] = []
                    monthly_groups[month].append(rec)
                except:
                    continue
            
            print(f"  - Months with data: {list(monthly_groups.keys())}")
            print(f"  - Current month records: {len(monthly_groups.get(current, []))}")
            
            # Check archives
            user_archives = MonthlyArchive.query.filter_by(user_id=test_user.id).all()
            print(f"  - Archived months: {len(user_archives)}")
            if user_archives:
                print(f"  - Archive months: {[a.month for a in user_archives]}")
                
                # Show sample archive data
                sample = user_archives[0]
                print(f"\n✓ Sample archive ({sample.month}):")
                print(f"  - Total records: {sample.total_records}")
                print(f"  - Total received: {sample.total_received:.1f} kg")
                print(f"  - Peak total: {sample.nominal_total:.1f} kg")
                print(f"  - Created: {sample.created_at}")
        
        print("\n" + "=" * 60)
        print("Test Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Visit /powerlifting/profile to see current month records")
        print("2. Visit /admin/archive to see historical archives")
        print("3. Set up cron job for automatic monthly archiving")

if __name__ == '__main__':
    test_archive_system()
