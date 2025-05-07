#!/usr/bin/env python3
"""
custom_capture.py

Demo script to control when the MID-40 spins up, when it captures data,
and when it spins down, with automatic conversion to LAS.
"""

import argparse
import datetime
import time

import openpylivox as opl


def parse_args():
    p = argparse.ArgumentParser(
        description="Custom Livox MID-40 capture: schedule spin-up, recording, spin-down, and conversion."
    )
    group = p.add_mutually_exclusive_group()
    group.add_argument(
        "--start-at",
        metavar="HH:MM:SS",
        help="Clock time to begin capture (today or tomorrow if that time has passed).",
    )
    group.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait from now before starting capture.",
    )
    p.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="How long (seconds) to record once streaming starts.",
    )
    p.add_argument(
        "--outfile",
        default="capture.bin",
        help="Base filename for the binary capture (and resulting .las).",
    )
    return p.parse_args()


def wait_until(start_at: str, delay: float):
    if start_at:
        now = datetime.datetime.now()
        target_time = datetime.datetime.combine(
            now.date(), datetime.datetime.strptime(start_at, "%H:%M:%S").time()
        )
        if target_time < now:
            target_time += datetime.timedelta(days=1)
        wait_secs = (target_time - now).total_seconds()
        print(f"[ Scheduler ] Waiting {wait_secs:.1f}s until {target_time.time()} …")
        time.sleep(wait_secs)
    elif delay > 0:
        print(f"[ Scheduler ] Waiting {delay:.1f}s from now …")
        time.sleep(delay)


def main():
    args = parse_args()

    # 1. Discover & connect (True turns on message-printing)
    sensor = opl.openpylivox(True)
    if not sensor.auto_connect():
        print("ERROR: Could not connect to a Livox sensor.")
        return

    # 2. Spin up
    print("[ Sensor ] Spinning up …")
    sensor.lidarSpinUp()

    # 3. Scheduler (either --start-at or --delay)
    wait_until(args.start_at, args.delay)

    # 4. Start real-time binary stream + file
    print("[ Capture ] Starting data stream …")
    sensor.dataStart_RT_B()
    sensor.saveDataToFile(args.outfile, secsToWait=0.0, duration=args.duration)

    # 5. Block until done
    while not sensor.doneCapturing():
        time.sleep(0.1)

    # 6. Stop & spin down
    print("[ Sensor ] Stopping stream & spinning down …")
    sensor.dataStop()
    sensor.lidarSpinDown()
    sensor.disconnect()

    # 7. Convert to LAS
    print("[ Convert ] Converting to LAS …")
    opl.convertBin2LAS(args.outfile, deleteBin=True)
    print(f"[ Done ] Output LAS: {args.outfile}.las")


if __name__ == "__main__":
    main()
