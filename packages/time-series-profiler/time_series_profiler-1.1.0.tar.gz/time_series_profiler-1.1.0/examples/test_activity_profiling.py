#!/usr/bin/env python3
"""Quick test of activity tracker profiling functionality."""

import pandas as pd

from tsp import Config, ProfileReport

# Load a small sample of the data
print("Loading sample data...")
df = pd.read_csv("activity_tracker.csv", parse_dates=["timestamp"], nrows=10000)

print(f"Sample data shape: {df.shape}")
print(f"Users: {df['user_id'].unique()}")
print(f"Activities: {df['activity'].unique()}")
print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")

# Test 1: Global profiling
print("\n=== GLOBAL PROFILING ===")
config = Config(time_col="timestamp", metrics=["gaps_sampling"])
report = ProfileReport(df, config)

results = report.compute()
gaps_info = results["groups"]["()"]["gaps_sampling"]
print(f"Detected sampling rate: {gaps_info.get('detected_rate_hz', 'N/A')} Hz")
print(f"Total observations: {len(df)}")
print(f"Gaps detected: {gaps_info['n_gaps']}")
print(f"Data coverage: {gaps_info['gaps']['data_coverage_ratio']:.2%}")

# Test 2: Per-user profiling
print("\n=== PER-USER PROFILING ===")
user_config = Config(
    time_col="timestamp", entity_cols=("user_id",), metrics=["gaps_sampling"]
)
user_report = ProfileReport(df, user_config)

user_results = user_report.compute()
for group_key, group_data in user_results["groups"].items():
    if group_key == "()":
        continue
    user_id = group_key.strip("()").strip("'\"")
    gaps_info = group_data["gaps_sampling"]
    print(
        f"User {user_id}: {gaps_info['n_gaps']} gaps, {gaps_info.get('detected_rate_hz', 'N/A')} Hz"
    )

# Test 3: Per-user-activity profiling
print("\n=== PER-USER-ACTIVITY PROFILING ===")
detailed_config = Config(
    time_col="timestamp", entity_cols=("user_id", "activity"), metrics=["gaps_sampling"]
)
detailed_report = ProfileReport(df, detailed_config)

detailed_results = detailed_report.compute()
for group_key, group_data in detailed_results["groups"].items():
    if group_key == "()":
        continue
    group_parts = group_key.strip("()").split(", ")
    user_id = group_parts[0].strip("'\"")
    activity = group_parts[1].strip("'\"")
    gaps_info = group_data["gaps_sampling"]

    print(
        f"{user_id}-{activity}: {gaps_info['n_gaps']} gaps, "
        f"{gaps_info.get('detected_rate_hz', 'N/A')} Hz, "
        f"{gaps_info['gaps']['data_coverage_ratio']:.2%} coverage"
    )

print("\n=== TEST COMPLETED SUCCESSFULLY ===")
