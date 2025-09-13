#!/usr/bin/env python3
"""Activity Tracker Data Profiling Example.

This example demonstrates profiling multi-dimensional time-series data from
activity trackers with multiple users, activities, and sensor readings.

Features demonstrated:
- Global profiling across all data
- Per-user profiling
- Per-user-activity profiling
- Sampling rate detection
- Gap analysis with locations
- Multi-sensor data analysis
"""

import json
from pathlib import Path

import pandas as pd

from tsp import Config, ProfileReport


def load_or_generate_data():
    """Load existing data or generate new activity tracker dataset."""
    data_file = Path("activity_tracker.csv")

    if data_file.exists():
        print("Loading existing activity tracker data...")
        df = pd.read_csv(data_file, parse_dates=["timestamp"])
    else:
        print("Generating new activity tracker data...")
        from activity_tracker_data import generate_activity_data

        df = generate_activity_data()
        df.to_csv(data_file, index=False)
        print(f"Saved to {data_file}")

    return df


def profile_activity_data():
    """Comprehensive profiling of activity tracker data."""

    df = load_or_generate_data()

    print("\n=== DATASET OVERVIEW ===")
    print(f"Shape: {df.shape}")
    print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Users: {sorted(df['user_id'].unique())}")
    print(f"Activities: {sorted(df['activity'].unique())}")
    print(f"Sessions: {df['session_id'].nunique()}")

    metrics = ["basic_stats", "gaps_sampling", "categorical_profile"]

    results = {}

    print("\n=== GLOBAL ANALYSIS ===")
    print("Analyzing entire dataset...")

    global_config = Config(time_col="timestamp", metrics=metrics)

    global_report = ProfileReport(df, global_config)
    results["global"] = global_report.results

    global_gaps = results["global"]["groups"]["()"]["gaps_sampling"]
    print(f"Detected sampling rate: {global_gaps.get('detected_rate_hz', 'N/A')} Hz")
    print(f"Total gaps: {global_gaps['n_gaps']}")
    print(f"Data coverage: {global_gaps['gaps']['data_coverage_ratio']:.2%}")

    print("\n=== PER-USER ANALYSIS ===")

    user_config = Config(
        time_col="timestamp", entity_cols=("user_id",), metrics=metrics
    )

    user_report = ProfileReport(df, user_config)
    results["per_user"] = user_report.results

    for group_key, group_data in results["per_user"]["groups"].items():
        user_id = group_key.strip("()").strip("'\"") if group_key != "()" else "Global"
        gaps_info = group_data["gaps_sampling"]
        basic_info = group_data["basic_stats"]

        print(f"\nUser: {user_id}")
        print(f"  Observations: {basic_info['n_rows']:,}")
        print(f"  Sampling rate: {gaps_info.get('detected_rate_hz', 'N/A')} Hz")
        print(f"  Gaps: {gaps_info['n_gaps']}")
        print(f"  Coverage: {gaps_info['gaps']['data_coverage_ratio']:.2%}")

        # Show first few gaps if any
        if gaps_info["gaps"]["gap_details"]:
            print(
                f"  First gap: {gaps_info['gaps']['gap_details'][0]['gap_start_time']} "
                f"({gaps_info['gaps']['gap_details'][0]['gap_duration_seconds']:.2f}s)"
            )

    print("\n=== PER-USER-ACTIVITY ANALYSIS ===")

    user_activity_config = Config(
        time_col="timestamp", entity_cols=("user_id", "activity"), metrics=metrics
    )

    user_activity_report = ProfileReport(df, user_activity_config)
    results["per_user_activity"] = user_activity_report.results

    # Display detailed per-user-activity summary
    for group_key, group_data in results["per_user_activity"]["groups"].items():
        if group_key == "()":
            continue

        # Parse group key (user_id, activity)
        group_parts = group_key.strip("()").split(", ")
        user_id = group_parts[0].strip("'\"")
        activity = group_parts[1].strip("'\"")

        gaps_info = group_data["gaps_sampling"]
        basic_info = group_data["basic_stats"]

        print(f"\n{user_id} - {activity}:")
        print(f"  Observations: {basic_info['n_rows']:,}")
        print(f"  Duration: {gaps_info['total_timespan_seconds']/60:.1f} minutes")
        print(f"  Sampling rate: {gaps_info.get('detected_rate_hz', 'N/A')} Hz")
        print(f"  Gaps: {gaps_info['n_gaps']}")
        print(f"  Coverage: {gaps_info['gaps']['data_coverage_ratio']:.2%}")
        print(f"  Regularity: {gaps_info.get('regularity_score', 0):.2%}")

        # Sensor quality summary
        x_stats = basic_info["columns"].get("x_accel", {})
        y_stats = basic_info["columns"].get("y_accel", {})
        z_stats = basic_info["columns"].get("z_accel", {})

        print(
            f"  Sensor ranges: X[{x_stats.get('min', 0):.1f}, {x_stats.get('max', 0):.1f}] "
            f"Y[{y_stats.get('min', 0):.1f}, {y_stats.get('max', 0):.1f}] "
            f"Z[{z_stats.get('min', 0):.1f}, {z_stats.get('max', 0):.1f}]"
        )

    print("\n=== DETAILED GAP ANALYSIS ===")

    total_gaps = 0
    for group_key, group_data in results["per_user_activity"]["groups"].items():
        if group_key == "()":
            continue

        gaps_info = group_data["gaps_sampling"]
        n_gaps = gaps_info["n_gaps"]
        total_gaps += n_gaps

        if n_gaps > 0:
            group_parts = group_key.strip("()").split(", ")
            user_id = group_parts[0].strip("'\"")
            activity = group_parts[1].strip("'\"")

            print(f"\n{user_id} - {activity} ({n_gaps} gaps):")

            for i, gap in enumerate(gaps_info["gaps"]["gap_details"][:3]):
                print(f"  Gap {i+1}: {gap['gap_start_time']} -> {gap['gap_end_time']}")
                print(
                    f"    Duration: {gap['gap_duration_seconds']:.2f}s "
                    f"(~{gap['expected_samples_missing']} missing samples)"
                )

    print(f"\nTotal gaps across all user-activities: {total_gaps}")

    print("\n=== SAVING REPORTS ===")

    with open("activity_global_report.json", "w") as f:
        json.dump(results["global"], f, indent=2, default=str)

    with open("activity_user_report.json", "w") as f:
        json.dump(results["per_user"], f, indent=2, default=str)

    with open("activity_detailed_report.json", "w") as f:
        json.dump(results["per_user_activity"], f, indent=2, default=str)

    global_report.to_html("activity_global_report.html")
    user_report.to_html("activity_user_report.html")
    user_activity_report.to_html("activity_detailed_report.html")

    print("Saved reports:")
    print("  - activity_global_report.json/html")
    print("  - activity_user_report.json/html")
    print("  - activity_detailed_report.json/html")

    return results


def analyze_sampling_patterns(results):
    """Analyze sampling patterns across different groupings."""

    print("\n=== SAMPLING PATTERN ANALYSIS ===")

    sampling_rates = {}

    # Extract sampling rates by user-activity
    for group_key, group_data in results["per_user_activity"]["groups"].items():
        if group_key == "()":
            continue

        group_parts = group_key.strip("()").split(", ")
        activity = group_parts[1].strip("'\"")  # Only need activity for this analysis

        gaps_info = group_data["gaps_sampling"]
        rate = gaps_info.get("detected_rate_hz", 0)

        if activity not in sampling_rates:
            sampling_rates[activity] = []
        sampling_rates[activity].append(rate)

    print("Sampling rates by activity:")
    for activity, rates in sampling_rates.items():
        avg_rate = sum(rates) / len(rates) if rates else 0
        print(
            f"  {activity}: {avg_rate:.1f} Hz (range: {min(rates):.1f}-{max(rates):.1f})"
        )

    return sampling_rates


if __name__ == "__main__":
    print("Activity Tracker Data Profiling")
    print("=" * 50)

    results = profile_activity_data()

    sampling_patterns = analyze_sampling_patterns(results)

    print("\n=== SUMMARY ===")
    print("Activity tracker profiling completed successfully!")
    print("Check the generated HTML reports for detailed visualizations.")
