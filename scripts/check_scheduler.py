#!/usr/bin/env python3
"""
Check if scheduler is running and list all scheduled jobs.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from scheduler.jobs import scheduler

async def check_scheduler():
    """Check scheduler status and list jobs."""
    print("=" * 60)
    print("Scheduler Status")
    print("=" * 60)
    print(f"Scheduler running: {scheduler.running}")
    print()
    
    if scheduler.running:
        jobs = scheduler.get_jobs()
        print(f"Total scheduled jobs: {len(jobs)}")
        print()
        
        if jobs:
            print("Scheduled Jobs:")
            print("-" * 60)
            for job in jobs:
                print(f"ID: {job.id}")
                print(f"  Function: {job.func_ref}")
                print(f"  Next run: {job.next_run_time}")
                print(f"  Trigger: {job.trigger}")
                print()
        else:
            print("⚠️  No jobs scheduled")
            print("   Scheduler may not have been initialized")
    else:
        print("⚠️  Scheduler is NOT running")
        print("   Jobs will not execute")
        print()
        print("To start scheduler:")
        print("  1. Restart the bot")
        print("  2. Check bot logs for scheduler initialization")

if __name__ == "__main__":
    asyncio.run(check_scheduler())

