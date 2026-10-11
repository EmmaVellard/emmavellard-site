"""Build portfolio figures from the pinned SolarConflux bundled ephemerides.

Requires numpy and matplotlib. Run from any directory with MPLCONFIGDIR pointing
to a writable cache. No network retrieval, orbit fitting, or data interpolation.
"""

from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public/files/solarconflux"
ART = ROOT / "public/images/projects/solarconflux"
PREVIEW = ROOT / "output/solarconflux-2026-10-09"
REVISION = "bcca574095b0a95733295e1937775e6380dd36d8"
SOURCE = f"https://github.com/EmmaVellard/SolarConflux/blob/{REVISION}/web/example.json"
AU_KM = 149597870.7
CONE_DEG = 15.0
LATITUDE_DEG = 10.0

raw = (DATA / "january-2025-trajectories.json").read_bytes()
bundle = json.loads(raw)
assert bundle["frame"] == "HeliocentricInertial"
assert bundle["time_scale"] == "UTC"
trajectories = bundle["trajectories"]
bodies = ["Earth", "Solar Orbiter", "BepiColombo"]
times = [datetime.fromisoformat(s["time"].replace("Z", "+00:00")) for s in trajectories["Earth"]]
assert len(times) == 57
assert all((b - a).total_seconds() == 21600 for a, b in zip(times, times[1:]))
for name in bodies:
    samples = trajectories[name]
    assert [s["time"] for s in samples] == [s["time"] for s in trajectories["Earth"]]
    assert all(math.isfinite(s[k]) for s in samples for k in ["lon_deg", "lat_deg", "radius_km"])
    assert all(s["radius_km"] > 0 and abs(s["lat_deg"]) <= 90 for s in samples)

earth = trajectories["Earth"]
orbiter = trajectories["Solar Orbiter"]
separation = np.array([abs((a["lon_deg"] - b["lon_deg"] + 180) % 360 - 180) for a, b in zip(earth, orbiter)])
latitude_span = np.array([abs(a["lat_deg"] - b["lat_deg"]) for a, b in zip(earth, orbiter)])
matches = (separation <= CONE_DEG) & (latitude_span <= LATITUDE_DEG)
indices = np.flatnonzero(matches)
assert len(indices) and np.all(np.diff(indices) == 1)
first, last = times[int(indices[0])], times[int(indices[-1])]
assert first.isoformat() == "2025-01-01T00:00:00+00:00"
assert last.isoformat() == "2025-01-07T18:00:00+00:00"
duration = (last - first).total_seconds() / 3600
assert duration == 162

DATA.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)
PREVIEW.mkdir(parents=True, exist_ok=True)
with (DATA / "january-2025-samples.csv").open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["time_utc", "circular_longitude_separation_deg", "latitude_span_deg", "cone_match"])
    for t, gap, lat, matched in zip(times, separation, latitude_span, matches):
        writer.writerow([t.isoformat().replace("+00:00", "Z"), f"{gap:.8f}", f"{lat:.8f}", str(bool(matched)).lower()])
with (DATA / "january-2025-window.csv").open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["geometry", "bodies", "start_time_utc", "end_time_utc", "duration_hours", "cone_width_deg", "latitude_span_limit_deg", "sampling_hours"])
    writer.writerow(["cone", "Earth;Solar Orbiter", first.isoformat(), last.isoformat(), duration, CONE_DEG, LATITUDE_DEG, 6])
provenance = {
    "source_url": SOURCE,
    "source_revision": REVISION,
    "source_sha256": hashlib.sha256(raw).hexdigest(),
    "source_description": bundle["source"],
    "retrieved_at": bundle["retrieved_at"],
    "frame": bundle["frame"],
    "time_scale": "UTC",
    "requested_start": bundle["requested_start"],
    "requested_end": bundle["requested_end"],
    "samples_per_body": 57,
    "sample_step_hours": 6,
    "bodies_in_dataset": bodies,
    "pair_screened_in_figure": ["Earth", "Solar Orbiter"],
    "geometry": "cone",
    "cone_width_deg": CONE_DEG,
    "latitude_span_limit_deg": LATITUDE_DEG,
    "matching_samples": int(matches.sum()),
    "window_start": first.isoformat(),
    "window_end": last.isoformat(),
    "duration_hours": duration,
    "next_nonmatching_sample": times[int(indices[-1]) + 1].isoformat(),
    "formula": "abs((longitude_Earth - longitude_SolarOrbiter + 180) % 360 - 180) <= 15; abs(latitude_Earth - latitude_SolarOrbiter) <= 10",
    "position_plot": "HCI XY projection: cylindrical radius = spherical radius * cos(latitude). Dots are the first sample; lines join retrieved samples only.",
    "public_app_check": "The published browser app reproduced the same 162 h cone window with the bundled data on 2026-10-09. Cone and Parker modes selected; 15 degree cone, 10 degree angular tolerance, 10 degree group latitude span, 400 km/s wind. No Parker window was returned.",
    "interpretation": "Illustrative geometric screening, not verified physical or magnetic connectivity. Window boundaries are the first and last matching samples; no interpolation or earlier entry time is inferred.",
}
(DATA / "january-2025-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")

plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"], "font.size": 12, "svg.fonttype": "none", "svg.hashsalt": "solarconflux-portfolio", "axes.linewidth": 0.6})
palettes = {
    "light": {"ink": "#0d2140", "muted": "#44597a", "grid": "#b8cce2", "accent": "#2a62b8", "orbiter": "#297b86", "bepi": "#8966a5", "sun": "#fbf6e8"},
    "dark": {"ink": "#e6eef9", "muted": "#9fb2cc", "grid": "#33455e", "accent": "#8fc6e3", "orbiter": "#7acec8", "bepi": "#c5a7e8", "sun": "#fbf6e8"},
}

def save(fig, stem, theme):
    fig.savefig(ART / f"{stem}-{theme}.svg", transparent=True, metadata={"Date": None, "Description": SOURCE})
    fig.savefig(PREVIEW / f"{stem}-{theme}.png", transparent=True, dpi=180)
    plt.close(fig)

for theme, p in palettes.items():
    fig = plt.figure(figsize=(6.5, 4.6), facecolor="none")
    ax = fig.add_axes([0.19, 0.15, 0.62, 0.78], projection="polar", facecolor="none")
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.set_ylim(0, 1.1)
    ax.set_xticks(np.deg2rad([0, 90, 180, 270]))
    ax.set_xticklabels(["0°", "90°", "180°", "270°"])
    ax.set_yticks([0.5, 1.0])
    ax.set_yticklabels(["0.5 AU", "1.0 AU"])
    ax.set_rlabel_position(225)
    ax.tick_params(colors=p["muted"], labelsize=10, pad=6)
    ax.grid(color=p["grid"], linewidth=0.6, alpha=0.7)
    ax.spines["polar"].set_color(p["grid"])
    low = min(earth[0]["lon_deg"], orbiter[0]["lon_deg"])
    sector = np.deg2rad(np.linspace(low, low + CONE_DEG, 50))
    ax.fill_between(sector, 0, 1.07, color=p["accent"], alpha=0.11)
    ax.scatter([0], [0], s=90, color=p["sun"], edgecolor=p["accent"], linewidth=1, zorder=5)
    ax.text(np.deg2rad(250), 0.15, "Sun", ha="center", color=p["muted"], fontsize=10)
    for name, color, marker in zip(bodies, [p["accent"], p["orbiter"], p["bepi"]], ["o", "^", "s"]):
        samples = trajectories[name]
        lon = np.deg2rad([s["lon_deg"] for s in samples])
        radius = np.array([s["radius_km"] * math.cos(math.radians(s["lat_deg"])) / AU_KM for s in samples])
        ax.plot(lon, radius, color=color, linewidth=1.5, alpha=0.8)
        ax.scatter([lon[0]], [radius[0]], s=50, marker=marker, color=color, edgecolor="none", label=name, zorder=6)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.23), ncol=3, frameon=False, labelcolor=p["ink"], fontsize=9.5, columnspacing=1.2, handletextpad=0.3)
    save(fig, "january-2025-positions", theme)

    fig, ax = plt.subplots(figsize=(6.5, 4.6), facecolor="none")
    fig.subplots_adjust(left=0.13, right=0.95, top=0.91, bottom=0.21)
    ax.set_facecolor("none")
    ax.axvspan(first, last, color=p["accent"], alpha=0.10, linewidth=0)
    ax.axhline(CONE_DEG, color=p["accent"], linewidth=1, linestyle=(0, (4, 4)))
    ax.plot(times, separation, color=p["accent"], linewidth=1.6, marker="o", markersize=2.8)
    ax.set_xlim(times[0], times[-1])
    ax.set_ylim(0, 30)
    ax.set_yticks([0, 10, 15, 20, 30])
    ax.set_xticks([times[0], times[16], times[32], times[56]])
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d Jan", tz=timezone.utc))
    ax.set_ylabel("Longitude separation (°)", color=p["muted"], labelpad=12)
    ax.set_xlabel("January 2025 · UTC", color=p["muted"], labelpad=14)
    ax.text(times[2], 4.1, "Candidate window", color=p["accent"], fontsize=10)
    ax.text(times[2], 1.7, "162 h · 28 matching samples", color=p["muted"], fontsize=9)
    ax.text(times[-1], 14.2, "15° cone criterion", ha="right", va="top", color=p["muted"], fontsize=10)
    ax.tick_params(colors=p["muted"], labelsize=10, length=0, pad=8)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(p["grid"])
    ax.grid(axis="y", color=p["grid"], linewidth=0.6, alpha=0.7)
    save(fig, "january-2025-separation", theme)

print(f"57 samples/body; {matches.sum()} matching samples; {first.isoformat()} to {last.isoformat()}; {duration:g} h")
print("Saved four theme-aware SVG figures, sample/window CSVs and provenance.")
