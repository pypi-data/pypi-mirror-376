#!/usr/bin/env python3
"""
Time Series Profiler - Quick Start Example

This script demonstrates the basic usage of the time-series-profiler library
with pandas data, showing how to profile accelerometer data from multiple users.
"""

import json
from pathlib import Path

import pandas as pd

from tsp import Config, ProfileReport


def main():
    print("Time Series Profiler - Quick Start Example")
    print("=" * 50)

    # Load sample data
    print("\nLoading sample data...")
    sample_file = Path(__file__).parent / "sample.csv"
    df = pd.read_csv(sample_file, parse_dates=["time"])

    print(f"Loaded data with shape: {df.shape}")
    print(f"Time range: {df['time'].min()} to {df['time'].max()}")
    print(f"Users: {sorted(df['user_id'].unique())}")
    print(f"Activities: {sorted(df['activity'].unique())}")

    print("\nFirst few rows:")
    print(df.head())

    # Create profile report
    print("\nCreating profile report...")
    config = Config(
        time_col="time",
        entity_cols=("user_id",),
        metrics=["basic_stats", "gaps_sampling", "categorical_profile"],
    )

    report = ProfileReport(df, config)

    # Generate and display JSON report
    print("\nGenerating JSON report...")
    json_report = report.to_json()

    # Parse and display key metrics
    data = json.loads(json_report)

    print("\nProfile generated successfully.")
    print(f"Number of groups: {data.get('summary', {}).get('n_groups', 1)}")
    print(f"Backend: {data['metadata']['config']['backend']}")
    print(f"Metrics computed: {', '.join(data['metadata']['config']['metrics'])}")

    # Display summary for each group
    for group_key, group_data in data["groups"].items():
        print(f"\nGroup {group_key}:")

        if "basic_stats" in group_data:
            basic = group_data["basic_stats"]
            print(f"  Rows: {basic['n_rows']}, Columns: {basic['n_cols']}")
            print(f"  Time monotonic: {basic['is_time_monotonic']}")

            # Show stats for ax column
            if "ax" in basic["columns"]:
                ax_stats = basic["columns"]["ax"]
                print(
                    f"  ax values: mean={ax_stats['mean']:.2f}, std={ax_stats['std']:.2f}"
                )

        if "gaps_sampling" in group_data:
            gaps = group_data["gaps_sampling"]
            print(f"  Sampling interval: {gaps['median_delta_seconds']:.0f}s")
            print(f"  Gaps detected: {gaps['n_gaps']}")
            print(f"  Total timespan: {gaps['total_timespan_seconds']:.0f}s")

        if (
            "categorical_profile" in group_data
            and "activity" in group_data["categorical_profile"]
        ):
            cat = group_data["categorical_profile"]["activity"]
            if "error" not in cat:
                print(
                    f"  Activities: {cat['cardinality']} unique, {cat['total_count']} total"
                )

    # Generate HTML report
    print("\nGenerating HTML report...")
    html_report = report.to_html(title="Sample Accelerometer Data Profile")

    # Save HTML report to file
    html_file = Path(__file__).parent / "profile_report.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_report)

    print(f"HTML report saved to: {html_file}")

    # Save JSON report to file
    json_file = Path(__file__).parent / "profile_report.json"
    with open(json_file, "w", encoding="utf-8") as f:
        f.write(json_report)

    print(f"JSON report saved to: {json_file}")

    print("\nExample completed successfully.")
    print("\nNext steps:")
    print("- Open profile_report.html in your browser")
    print("- Examine profile_report.json for programmatic access")
    print("- Try with your own time-series data")


if __name__ == "__main__":
    main()
