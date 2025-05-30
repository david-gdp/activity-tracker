#!/usr/bin/env python3
"""
ActivityWatch Time Tracker

This script fetches data from ActivityWatch (localhost:5600) and calculates
total non-idle and idle time for a specified day.

Usage:
    activity-tracker                    # Analyze today
    activity-tracker --date 2025-05-27  # Analyze specific date
    activity-tracker --help             # Show help
"""

import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

try:
    import requests
except ImportError:
    print("Error: 'requests' module not found.")
    print("Please install it with: pip install requests")
    sys.exit(1)


class ActivityWatchTracker:
    def __init__(self, host: str = "localhost", port: int = 5600):
        self.base_url = f"http://{host}:{port}"
        self.api_url = f"{self.base_url}/api/0"

    def get_buckets(self) -> Dict:
        """Fetch all available buckets from ActivityWatch."""
        try:
            response = requests.get(f"{self.api_url}/buckets")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching buckets: {e}")
            return {}

    def get_events(self, bucket_id: str, start_time: str, end_time: str) -> List:
        """Fetch events from a specific bucket for the given time range."""
        try:
            params = {"start": start_time, "end": end_time}
            response = requests.get(
                f"{self.api_url}/buckets/{bucket_id}/events", params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching events from bucket {bucket_id}: {e}")
            return []

    def calculate_daily_time(self, target_date: datetime) -> Tuple[float, float]:
        """
        Calculate total active and idle time for a specific day.

        Returns:
            Tuple[float, float]: (active_time_hours, idle_time_hours)
        """
        # Define the time range for the target day
        start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)

        start_iso = start_time.isoformat()
        end_iso = end_time.isoformat()

        print(f"Analyzing activity for {target_date.strftime('%Y-%m-%d')}")
        print(f"Time range: {start_iso} to {end_iso}")

        # Get all buckets
        buckets = self.get_buckets()
        if not buckets:
            print("No buckets found. Make sure ActivityWatch is running.")
            return 0.0, 0.0

        print(f"Found {len(buckets)} buckets:")
        for bucket_id in buckets:
            print(f"  - {bucket_id}")

        total_active_seconds = 0
        total_idle_seconds = 0

        # Look for AFK (Away From Keyboard) buckets to determine idle time
        afk_buckets = [bid for bid in buckets if "afk" in bid.lower()]

        if not afk_buckets:
            print(
                "Warning: No AFK buckets found. Cannot determine idle time accurately."
            )
            return 0.0, 0.0

        # Process AFK data to calculate active vs idle time
        for bucket_id in afk_buckets:
            print(f"\nProcessing bucket: {bucket_id}")
            events = self.get_events(bucket_id, start_iso, end_iso)

            if not events:
                print(f"  No events found in {bucket_id}")
                continue

            print(f"  Found {len(events)} events")

            for event in events:
                duration = event.get("duration", 0)
                data = event.get("data", {})
                status = data.get("status", "unknown")

                if status == "not-afk":
                    total_active_seconds += duration
                elif status == "afk":
                    total_idle_seconds += duration

        # Convert to hours
        active_hours = total_active_seconds / 3600
        idle_hours = total_idle_seconds / 3600

        return active_hours, idle_hours

    def print_summary(self, active_hours: float, idle_hours: float):
        """Print a formatted summary of the time tracking results."""
        total_hours = active_hours + idle_hours
        target_hours = 8.0  # 8-hour workday target

        print("\n" + "=" * 50)
        print("DAILY TIME SUMMARY")
        print("=" * 50)
        print(
            f"Active Time:  {active_hours:.2f} hours ({active_hours * 60:.0f} minutes)"
        )
        print(f"Idle Time:    {idle_hours:.2f} hours ({idle_hours * 60:.0f} minutes)")
        print(f"Total Time:   {total_hours:.2f} hours")

        if total_hours > 0:
            active_percentage = (active_hours / total_hours) * 100
            idle_percentage = (idle_hours / total_hours) * 100
            print(f"Active:       {active_percentage:.1f}%")
            print(f"Idle:         {idle_percentage:.1f}%")

        # Calculate time left to reach 8-hour workday
        print("-" * 50)
        print("8-HOUR WORKDAY PROGRESS")
        print("-" * 50)

        if active_hours >= target_hours:
            overtime_hours = active_hours - target_hours
            if overtime_hours >= 1.0:
                overtime_hours_int = int(overtime_hours)
                overtime_minutes = int((overtime_hours - overtime_hours_int) * 60)
                print(
                    f"✅ Target reached! Overtime: {overtime_hours_int}h {overtime_minutes}m"
                )
            else:
                overtime_minutes = int(overtime_hours * 60)
                print(f"✅ Target reached! Overtime: {overtime_minutes} minutes")
        else:
            remaining_hours = target_hours - active_hours
            if remaining_hours >= 1.0:
                remaining_hours_int = int(remaining_hours)
                remaining_minutes = int((remaining_hours - remaining_hours_int) * 60)
                print(f"⏳ Time left: {remaining_hours_int}h {remaining_minutes}m")
            else:
                remaining_minutes = int(remaining_hours * 60)
                print(f"⏳ Time left: {remaining_minutes} minutes")

        # Show progress percentage
        progress_percentage = min((active_hours / target_hours) * 100, 100)
        print(f"Progress:     {progress_percentage:.1f}% of 8-hour target")

        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Track daily activity using ActivityWatch data"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to analyze (YYYY-MM-DD format). Default is today.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="ActivityWatch host (default: localhost)",
    )
    parser.add_argument(
        "--port", type=int, default=5600, help="ActivityWatch port (default: 5600)"
    )

    args = parser.parse_args()

    # Parse the target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print("Error: Date must be in YYYY-MM-DD format")
            return
    else:
        target_date = datetime.now()

    # Create tracker instance
    tracker = ActivityWatchTracker(host=args.host, port=args.port)

    # Test connection
    try:
        response = requests.get(f"{tracker.base_url}/api/0/info")
        response.raise_for_status()
        print(f"Successfully connected to ActivityWatch at {tracker.base_url}")
    except requests.RequestException as e:
        print(f"Error: Cannot connect to ActivityWatch at {tracker.base_url}")
        print(f"Make sure ActivityWatch is running on {args.host}:{args.port}")
        print(f"Connection error: {e}")
        return

    # Calculate and display results
    active_hours, idle_hours = tracker.calculate_daily_time(target_date)
    tracker.print_summary(active_hours, idle_hours)


if __name__ == "__main__":
    main()
