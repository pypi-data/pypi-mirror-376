#!/usr/bin/env python3
"""Generate activity tracker dataset for profiling demonstration."""

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_activity_data():
    """Generate activity tracker dataset with gaps and varying sampling rates."""

    users = ["user_001", "user_002", "user_003"]
    activities = ["walking", "running", "cycling", "stationary"]
    base_time = datetime(2024, 1, 1, 8, 0, 0)

    all_data = []

    for user in users:
        for activity in activities:
            sampling_rates = {
                "walking": 50,
                "running": 100,
                "cycling": 25,
                "stationary": 10,
            }

            freq_ms = 1000 // sampling_rates[activity]

            sessions = random.randint(2, 4)

            for session in range(sessions):
                duration_minutes = random.randint(5, 15)
                session_start = base_time + timedelta(
                    days=session,
                    hours=random.randint(0, 16),
                    minutes=random.randint(0, 59),
                )

                n_points = duration_minutes * 60 * sampling_rates[activity]
                timestamps = pd.date_range(
                    session_start, periods=n_points, freq=f"{freq_ms}ms"
                )

                if activity == "walking":
                    x_base, y_base, z_base = 0.2, 0.1, 9.8
                    noise_scale = 2.0
                elif activity == "running":
                    x_base, y_base, z_base = 0.5, 0.3, 9.5
                    noise_scale = 4.0
                elif activity == "cycling":
                    x_base, y_base, z_base = 1.0, 0.2, 9.0
                    noise_scale = 3.0
                else:  # stationary
                    x_base, y_base, z_base = 0.0, 0.0, 9.8
                    noise_scale = 0.5

                t_norm = np.arange(len(timestamps)) / len(timestamps)
                x_values = x_base + noise_scale * np.random.normal(
                    0, 0.3, len(timestamps)
                )
                y_values = y_base + noise_scale * np.random.normal(
                    0, 0.3, len(timestamps)
                )
                z_values = z_base + noise_scale * np.random.normal(
                    0, 0.2, len(timestamps)
                )

                if activity in ["walking", "running"]:
                    freq = 2.0 if activity == "walking" else 3.5
                    x_values += 0.8 * np.sin(
                        2 * np.pi * freq * t_norm * duration_minutes
                    )
                    y_values += 0.6 * np.cos(
                        2 * np.pi * freq * t_norm * duration_minutes
                    )

                session_data = pd.DataFrame(
                    {
                        "timestamp": timestamps,
                        "user_id": user,
                        "activity": activity,
                        "session_id": f"{user}_{activity}_{session:02d}",
                        "x_accel": x_values,
                        "y_accel": y_values,
                        "z_accel": z_values,
                        "magnitude": np.sqrt(x_values**2 + y_values**2 + z_values**2),
                    }
                )

                if random.random() < 0.3:  # 30% chance of gaps
                    gap_start = random.randint(
                        len(session_data) // 4, 3 * len(session_data) // 4
                    )
                    gap_duration = random.randint(50, 200)  # 50-200 samples
                    session_data = session_data.drop(
                        session_data.index[gap_start : gap_start + gap_duration]
                    ).reset_index(drop=True)

                if random.random() < 0.2:  # 20% chance
                    n_missing = random.randint(5, 20)
                    missing_indices = random.sample(range(len(session_data)), n_missing)
                    for idx in missing_indices:
                        col = random.choice(["x_accel", "y_accel", "z_accel"])
                        session_data.loc[idx, col] = np.nan

                all_data.append(session_data)

    df = pd.concat(all_data, ignore_index=True)
    df = df.sort_values("timestamp").reset_index(drop=True)

    print(f"Generated {len(df):,} data points")
    print(f"Users: {df['user_id'].nunique()}")
    print(f"Activities: {df['activity'].nunique()}")
    print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Sessions: {df['session_id'].nunique()}")

    return df


if __name__ == "__main__":
    df = generate_activity_data()
    df.to_csv("activity_tracker.csv", index=False)
    print("\nSaved to activity_tracker.csv")
    print(f"Dataset shape: {df.shape}")
    print("\nSample data:")
    print(df.head(10))
