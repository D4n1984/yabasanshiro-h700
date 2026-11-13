#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# H700 / muOS utilities by D4n1984.
"""Sample an already-running emulator; frame counter address comes from its ELF."""

import argparse
import glob
import json
import os
import struct
import sys
import time

def read_text(path):
    with open(path, encoding="utf-8") as source:
        return source.read().strip()

def optional_text(path):
    try:
        return read_text(path)
    except OSError:
        return None

def process_stat(pid):
    # comm may contain spaces and parentheses: all fields follow its last ')'.
    stat = read_text("/proc/{}/stat".format(pid))
    end = stat.rfind(")")
    if end < 0:
        raise ValueError("invalid /proc stat")
    fields = stat[end + 1:].split()  # starts at field 3 (state)
    if len(fields) < 20:
        raise ValueError("short /proc stat")
    return int(fields[11]) + int(fields[12]), int(fields[19])

def rss_kib(pid):
    for line in read_text("/proc/{}/status".format(pid)).splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return None


def sensors():
    result = {"cpu0_cur_freq_khz": optional_text(
        "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"),
        "thermal_zones": [], "devfreq": []}
    for path in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
        result["thermal_zones"].append({
            "zone": os.path.basename(path), "type": optional_text(path + "/type"),
            "temp_millicelsius": optional_text(path + "/temp")})
    # Device names identify GPU domains where the firmware exposes them.
    for path in sorted(glob.glob("/sys/class/devfreq/*/cur_freq")):
        result["devfreq"].append({"device": os.path.basename(os.path.dirname(path)),
                                  "cur_freq_hz": optional_text(path)})
    return result


def percentile(values, fraction):
    values = sorted(values)
    if not values:
        return None
    position = (len(values) - 1) * fraction
    lo = int(position)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def sample(pid, memory, address, expected_start, gauges):
    ticks, start = process_stat(pid)
    if expected_start is not None and start != expected_start:
        raise RuntimeError("PID now refers to a different process")
    memory.seek(address)
    data = memory.read(4)
    if len(data) != 4:
        raise RuntimeError("cannot read complete frame counter")
    result = {"monotonic": time.monotonic(), "cpu_ticks": ticks,
              "start_ticks": start, "frames_u32": struct.unpack("=I", data)[0],
              "rss_kib": rss_kib(pid), "sensors": sensors()}
    if gauges:
        result["gauges"] = {}
        for name, gauge_address in gauges.items():
            memory.seek(gauge_address)
            value = memory.read(4)
            if len(value) != 4:
                raise RuntimeError("cannot read gauge {}".format(name))
            result["gauges"][name] = struct.unpack("=I", value)[0]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--frame-counter-address", type=lambda value: int(value, 0), required=True,
                        help="address of the uint32 counter, e.g. 0x123456")
    parser.add_argument("--seconds", type=float, default=30.0)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--gauge", action="append", default=[], metavar="NAME=ADDRESS",
                        help="read an instantaneous uint32 at ADDRESS; may be repeated")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.pid <= 0 or args.frame_counter_address < 0 or args.seconds <= 0 or args.interval <= 0:
        parser.error("pid, seconds and interval must be positive; address must be non-negative")
    gauges = {}
    for entry in args.gauge:
        name, separator, address = entry.partition("=")
        try:
            parsed_address = int(address, 0)
        except ValueError:
            parser.error("gauge must be NAME=ADDRESS (for example fps=0x1234)")
        if not separator or not name or name in gauges or parsed_address < 0:
            parser.error("gauge names must be unique and addresses non-negative")
        gauges[name] = parsed_address

    ticks_per_second = os.sysconf("SC_CLK_TCK")
    samples = []
    with open("/proc/{}/mem".format(args.pid), "rb", buffering=0) as memory:
        first = sample(args.pid, memory, args.frame_counter_address, None, gauges)
        samples.append(first)
        deadline = first["monotonic"] + args.seconds
        next_sample = first["monotonic"] + args.interval
        while True:
            target = min(next_sample, deadline)
            remaining = target - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
            current = sample(args.pid, memory, args.frame_counter_address, first["start_ticks"], gauges)
            samples.append(current)
            if current["monotonic"] >= deadline:
                break
            next_sample += args.interval
            if next_sample <= current["monotonic"]:
                next_sample = current["monotonic"] + args.interval

    periods = []
    frames_total = 0
    for previous, current in zip(samples, samples[1:]):
        elapsed = current["monotonic"] - previous["monotonic"]
        frames = (current["frames_u32"] - previous["frames_u32"]) & 0xffffffff
        cpu_seconds = (current["cpu_ticks"] - previous["cpu_ticks"]) / ticks_per_second
        if cpu_seconds < 0 or elapsed <= 0:
            raise RuntimeError("invalid process sample")
        frames_total += frames
        periods.append({"wall_seconds": elapsed, "frames": frames,
                        "frames_per_second": frames / elapsed,
                        "cpu_seconds": cpu_seconds,
                        "cpu_ms_per_frame": cpu_seconds * 1000 / frames if frames else None})
    wall = samples[-1]["monotonic"] - first["monotonic"]
    cpu = (samples[-1]["cpu_ticks"] - first["cpu_ticks"]) / ticks_per_second
    frame_cpu_periods = [p["cpu_ms_per_frame"] for p in periods if p["cpu_ms_per_frame"] is not None]
    rates = [p["frames_per_second"] for p in periods]
    summary = {"wall_seconds": wall, "cpu_seconds": cpu, "emulated_frames": frames_total,
               "emulated_frames_per_second": frames_total / wall,
               "cpu_ms_per_emulated_frame": cpu * 1000 / frames_total if frames_total else None,
               "interval_fps_mean": sum(rates) / len(rates), "interval_fps_p95": percentile(rates, 0.95),
               "interval_cpu_ms_per_frame_mean": sum(frame_cpu_periods) / len(frame_cpu_periods) if frame_cpu_periods else None,
               "interval_cpu_ms_per_frame_p95": percentile(frame_cpu_periods, 0.95),
               "note": "Percentiles describe sampled intervals, not individual frame times."}
    if gauges:
        summary["gauges"] = {}
        for name in gauges:
            values = [item["gauges"][name] for item in samples]
            summary["gauges"][name] = {"min": min(values), "max": max(values),
                                       "mean": sum(values) / len(values)}
    report = {"pid": args.pid, "frame_counter_address": hex(args.frame_counter_address),
              "clock_ticks_per_second": ticks_per_second, "requested_seconds": args.seconds,
              "requested_interval_seconds": args.interval, "samples": samples,
              "periods": periods, "summary": summary}
    if gauges:
        report["gauge_addresses"] = {name: hex(address) for name, address in gauges.items()}
    with open(args.output, "w", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    if not frames_total:
        raise RuntimeError("no emulated frames observed")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print("sampling failed: {}".format(error), file=sys.stderr)
        sys.exit(1)
