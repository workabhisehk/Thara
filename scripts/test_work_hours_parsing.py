#!/usr/bin/env python3
"""
Test script to verify work hours parsing logic.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.onboarding_parser import parse_onboarding_message, normalize_time_to_24h
from telegram_bot.handlers.onboarding import parse_work_hours

async def test_parsing():
    """Test various work hours formats."""
    test_cases = [
        "9 AM to 5 PM",
        "9:00 AM - 5:00 PM",
        "Monday-Friday 9-5",
        "09:00-17:00",
        "Monday, Wednesday, Friday from 9 AM to 4 PM, with 2 hours travel time",
        "9 AM - 5 PM",
    ]
    
    print("=" * 80)
    print("Testing Work Hours Parsing")
    print("=" * 80)
    
    for text in test_cases:
        print(f"\n📝 Testing: '{text}'")
        print("-" * 80)
        
        # Test AI parser
        try:
            parsed = await parse_onboarding_message(text, current_step="work_hours")
            print(f"✅ AI Parser Result:")
            print(f"   Response type: {parsed.get('response_type')}")
            print(f"   Confidence: {parsed.get('confidence')}")
            work_hours = parsed.get('work_hours', {})
            print(f"   Start time: {work_hours.get('start_time')}")
            print(f"   End time: {work_hours.get('end_time')}")
            print(f"   Days: {work_hours.get('days', [])}")
            print(f"   Notes: {work_hours.get('notes', '')}")
            
            # Test normalization
            start_time = work_hours.get('start_time')
            end_time = work_hours.get('end_time')
            
            if start_time:
                normalized_start = normalize_time_to_24h(start_time)
                print(f"   Normalized start: {start_time} -> {normalized_start}")
            else:
                print(f"   ⚠️  No start time extracted")
                
            if end_time:
                normalized_end = normalize_time_to_24h(end_time)
                print(f"   Normalized end: {end_time} -> {normalized_end}")
            else:
                print(f"   ⚠️  No end time extracted")
                
        except Exception as e:
            print(f"   ❌ AI Parser Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Test fallback parser
        try:
            hours = parse_work_hours(text)
            if hours:
                print(f"✅ Fallback Parser Result: {hours[0]}:00 - {hours[1]}:00")
            else:
                print(f"   ⚠️  Fallback parser returned None")
        except Exception as e:
            print(f"   ❌ Fallback Parser Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_parsing())

