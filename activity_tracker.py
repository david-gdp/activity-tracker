#!/usr/bin/env python3
"""
ActivityWatch Time Tracker

This script fetches data from ActivityWatch (localhost:5600) and calculates
total non-idle and idle time for a specified day or week.

Usage:
    activity-tracker                    # Analyze today
    activity-tracker --date 2025-05-27  # Analyze specific date
    activity-tracker --week             # Analyze this week
    activity-tracker --week --date 2025-05-27  # Analyze week containing this date
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

    def get_week_range(self, target_date: datetime) -> Tuple[datetime, datetime]:
        """
        Get the start and end of the week containing the target date.
        Week starts on Monday.

        Returns:
            Tuple[datetime, datetime]: (week_start, week_end)
        """
        # Get the Monday of the week containing target_date
        days_since_monday = target_date.weekday()
        week_start = target_date - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # Get the Sunday of the same week
        week_end = week_start + timedelta(days=7)

        return week_start, week_end

    def calculate_weekly_time(
        self, target_date: datetime
    ) -> Tuple[float, float, List[Tuple[str, float]]]:
        """
        Calculate total active and idle time for a week (Monday to Sunday).

        Returns:
            Tuple[float, float, List[Tuple[str, float]]]: (total_active_hours, total_idle_hours, daily_breakdown)
        """
        week_start, week_end = self.get_week_range(target_date)

        print(
            f"Analyzing weekly activity from {week_start.strftime('%Y-%m-%d')} to {(week_end - timedelta(days=1)).strftime('%Y-%m-%d')}"
        )

        total_active_hours = 0.0
        total_idle_hours = 0.0
        daily_breakdown = []

        # Calculate time for each day of the week
        current_date = week_start
        while current_date < week_end:
            active_hours, idle_hours = self.calculate_daily_time(current_date)
            total_active_hours += active_hours
            total_idle_hours += idle_hours

            day_name = current_date.strftime("%A")
            daily_breakdown.append(
                (f"{day_name} ({current_date.strftime('%Y-%m-%d')})", active_hours)
            )

            current_date += timedelta(days=1)

        return total_active_hours, total_idle_hours, daily_breakdown

    def calculate_finish_time(
        self, active_hours: float, target_hours: float = 8.0
    ) -> str:
        """
        Calculate when the user will finish work based on current active time.

        Returns:
            str: Estimated finish time in HH:MM:SS format
        """
        if active_hours >= target_hours:
            return "Already completed target hours!"

        remaining_hours = target_hours - active_hours
        remaining_seconds = remaining_hours * 3600

        # Calculate finish time from now
        now = datetime.now()
        finish_time = now + timedelta(seconds=remaining_seconds)

        return finish_time.strftime("%H:%M:%S")

    def calculate_overtime_range(
        self,
        active_hours: float,
        target_hours: float = 8.0,
        target_date: datetime = None,
    ) -> str:
        """
        Calculate the overtime time range when user has worked more than target hours.

        Returns:
            str: Overtime range in "HH:MM:SS - HH:MM:SS" format
        """
        if active_hours <= target_hours:
            return ""

        overtime_hours = active_hours - target_hours
        overtime_seconds = overtime_hours * 3600

        # Calculate overtime range
        if target_date is None or target_date.date() == datetime.now().date():
            # For today, use current time as end point
            end_time = datetime.now()
        else:
            # For historical dates, assume end of workday (e.g., 18:00) plus overtime
            base_end_time = target_date.replace(
                hour=18, minute=0, second=0, microsecond=0
            )
            end_time = base_end_time + timedelta(seconds=overtime_seconds)

        overtime_start = end_time - timedelta(seconds=overtime_seconds)

        return (
            f"{overtime_start.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')}"
        )

    def is_holiday(self, target_date: datetime) -> bool:
        """
        Check if the given date is a holiday (weekend).
        Currently supports rule-based detection for Saturday (5) and Sunday (6).

        Returns:
            bool: True if the date is a holiday (weekend), False otherwise
        """
        # weekday() returns 0-6 where Monday=0, Sunday=6
        return target_date.weekday() in [5, 6]  # Saturday=5, Sunday=6

    def get_holiday_info(self, target_date: datetime) -> str:
        """
        Get holiday information for the given date.

        Returns:
            str: Holiday name or empty string if not a holiday
        """
        weekday = target_date.weekday()
        if weekday == 5:
            return "Saturday"
        elif weekday == 6:
            return "Sunday"
        return ""

    def calculate_holiday_overtime_range(
        self, active_hours: float, target_date: datetime = None
    ) -> str:
        """
        Calculate the overtime range for holidays where entire working time is overtime.

        Returns:
            str: Overtime range in "HH:MM:SS - HH:MM:SS" format
        """
        if active_hours <= 0:
            return ""

        active_seconds = active_hours * 3600

        # Calculate overtime range
        if target_date is None or target_date.date() == datetime.now().date():
            # For today, use current time as end point
            end_time = datetime.now()
        else:
            # For historical dates, assume end of workday (e.g., 18:00) but calculate based on actual hours
            base_start_time = target_date.replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            end_time = base_start_time + timedelta(seconds=active_seconds)

        start_time = end_time - timedelta(seconds=active_seconds)

        return f"{start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')}"

    def print_summary(
        self, active_hours: float, idle_hours: float, target_date: datetime = None
    ):
        """Print a formatted summary of the time tracking results."""
        total_hours = active_hours + idle_hours
        target_hours = 8.0  # 8-hour workday target

        # Use today's date if target_date is None
        analysis_date = target_date if target_date is not None else datetime.now()
        is_holiday = self.is_holiday(analysis_date)
        holiday_name = self.get_holiday_info(analysis_date)

        print("\n" + "=" * 50)
        print("DAILY TIME SUMMARY")
        print("=" * 50)

        # Show holiday status
        if is_holiday:
            print(f"🏖️  HOLIDAY: {holiday_name} ({analysis_date.strftime('%Y-%m-%d')})")
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
        if is_holiday:
            print("HOLIDAY OVERTIME")
        else:
            print("8-HOUR WORKDAY PROGRESS")
        print("-" * 50)

        if is_holiday:
            # On holidays, entire working time is considered overtime
            if active_hours > 0:
                if active_hours >= 1.0:
                    active_hours_int = int(active_hours)
                    active_minutes = int((active_hours - active_hours_int) * 60)
                    print(f"⚠️  Holiday Overtime: {active_hours_int}h {active_minutes}m")
                else:
                    active_minutes = int(active_hours * 60)
                    print(f"⚠️  Holiday Overtime: {active_minutes} minutes")

                # Show holiday overtime range
                overtime_range = self.calculate_holiday_overtime_range(
                    active_hours, target_date
                )
                if overtime_range:
                    print(f"Holiday work period: {overtime_range}")
            else:
                print("🎉 No work on holiday - well deserved rest!")
        else:
            # Regular workday logic
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

                # Show overtime range
                overtime_range = self.calculate_overtime_range(
                    active_hours, target_hours, target_date
                )
                if overtime_range:
                    print(f"Overtime period: {overtime_range}")
            else:
                remaining_hours = target_hours - active_hours
                if remaining_hours >= 1.0:
                    remaining_hours_int = int(remaining_hours)
                    remaining_minutes = int(
                        (remaining_hours - remaining_hours_int) * 60
                    )
                    print(f"⏳ Time left: {remaining_hours_int}h {remaining_minutes}m")
                else:
                    remaining_minutes = int(remaining_hours * 60)
                    print(f"⏳ Time left: {remaining_minutes} minutes")

        # Show progress percentage
        if is_holiday:
            print(f"Holiday work: {active_hours:.2f} hours (all considered overtime)")
        else:
            progress_percentage = min((active_hours / target_hours) * 100, 100)
            print(f"Progress:     {progress_percentage:.1f}% of 8-hour target")

            # Show estimated finish time (only for today and non-holidays)
            if target_date is None or target_date.date() == datetime.now().date():
                if active_hours < target_hours:
                    finish_time = self.calculate_finish_time(active_hours, target_hours)
                    print(f"Estimated finish time: {finish_time}")

        print("=" * 50)

    def print_weekly_summary(
        self,
        total_active_hours: float,
        total_idle_hours: float,
        daily_breakdown: List[Tuple[str, float]],
        week_start: datetime,
    ):
        """Print a formatted summary of the weekly time tracking results."""
        total_hours = total_active_hours + total_idle_hours
        target_weekly_hours = 40.0  # 40-hour work week target

        print("\n" + "=" * 60)
        print("WEEKLY TIME SUMMARY")
        print("=" * 60)
        print(
            f"Week of {week_start.strftime('%Y-%m-%d')} to {(week_start + timedelta(days=6)).strftime('%Y-%m-%d')}"
        )
        print("-" * 60)

        # Daily breakdown
        for day_info, hours in daily_breakdown:
            print(f"{day_info:<30} {hours:>6.2f} hours")

        print("-" * 60)
        print(
            f"Total Active Time:  {total_active_hours:.2f} hours ({total_active_hours * 60:.0f} minutes)"
        )
        print(
            f"Total Idle Time:    {total_idle_hours:.2f} hours ({total_idle_hours * 60:.0f} minutes)"
        )
        print(f"Total Time:         {total_hours:.2f} hours")

        if total_hours > 0:
            active_percentage = (total_active_hours / total_hours) * 100
            print(f"Active Percentage:  {active_percentage:.1f}%")

        # Calculate weekly progress
        print("-" * 60)
        print("40-HOUR WORK WEEK PROGRESS")
        print("-" * 60)

        if total_active_hours >= target_weekly_hours:
            overtime_hours = total_active_hours - target_weekly_hours
            if overtime_hours >= 1.0:
                overtime_hours_int = int(overtime_hours)
                overtime_minutes = int((overtime_hours - overtime_hours_int) * 60)
                print(
                    f"✅ Weekly target reached! Overtime: {overtime_hours_int}h {overtime_minutes}m"
                )
            else:
                overtime_minutes = int(overtime_hours * 60)
                print(f"✅ Weekly target reached! Overtime: {overtime_minutes} minutes")
        else:
            remaining_hours = target_weekly_hours - total_active_hours
            if remaining_hours >= 1.0:
                remaining_hours_int = int(remaining_hours)
                remaining_minutes = int((remaining_hours - remaining_hours_int) * 60)
                print(
                    f"⏳ Time left this week: {remaining_hours_int}h {remaining_minutes}m"
                )
            else:
                remaining_minutes = int(remaining_hours * 60)
                print(f"⏳ Time left this week: {remaining_minutes} minutes")

        # Show weekly progress percentage
        progress_percentage = min((total_active_hours / target_weekly_hours) * 100, 100)
        print(f"Weekly Progress:    {progress_percentage:.1f}% of 40-hour target")

        # Average daily hours
        avg_daily_hours = total_active_hours / 7
        print(f"Average Daily:      {avg_daily_hours:.2f} hours")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Track daily or weekly activity using ActivityWatch data"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to analyze (YYYY-MM-DD format). Default is today.",
    )
    parser.add_argument(
        "--week",
        action="store_true",
        help="Analyze weekly data (Monday to Sunday). Use with --date to specify week containing that date.",
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
    if args.week:
        # Weekly analysis
        total_active_hours, total_idle_hours, daily_breakdown = (
            tracker.calculate_weekly_time(target_date)
        )
        week_start, _ = tracker.get_week_range(target_date)
        tracker.print_weekly_summary(
            total_active_hours, total_idle_hours, daily_breakdown, week_start
        )
    else:
        # Daily analysis
        active_hours, idle_hours = tracker.calculate_daily_time(target_date)
        tracker.print_summary(active_hours, idle_hours, target_date)


if __name__ == "__main__":
    main()
