"""Redraw DPS poster panel 6 from its original values, with transparent theme variants.

Run with Python and Matplotlib. No model rerun, interpolation or plot digitisation.
"""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

ROOT = Path(__file__).resolve().parents[1]
ROWS = list(csv.DictReader((ROOT / "data/lunar/dps-2026-tides.csv").open()))
OUT = ROOT / "public/images/research"
OUT.mkdir(parents=True, exist_ok=True)

assert len(ROWS) == 76
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13,
    "svg.fonttype": "path",
    "svg.hashsalt": "emmavellard-dps-tides",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

for theme, ink, muted, line, teal in [
    ("light", "#0d2140", "#44597a", "#b8cce2", "#397b83"),
    ("dark", "#e6eef9", "#9fb2cc", "#33455e", "#7acec8"),
]:
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    fig.subplots_adjust(left=.13, right=.98, bottom=.13, top=.78)
    for m in range(4):
        group = [r for r in ROWS if int(r["m"]) == m]
        assert len(group) == 19 and len({r["model"] for r in group}) == 19
        values = [float(r["k_ts_PM+XM_intercept"]) for r in group]
        measurement = float(group[0]["park_case2"])
        uncertainty = float(group[0]["park_reported_unc_15x_formal"])
        assert min(values) <= measurement <= max(values)
        ax.plot([m - .12] * 2, [min(values), max(values)], color=teal,
                linewidth=13, alpha=.3, solid_capstyle="butt")
        ax.plot([m - .12] * 19, values, "o", color=teal, markersize=3.7,
                label="19 model interiors" if m == 0 else None)
        ax.errorbar(m + .12, measurement, yerr=uncertainty, fmt="D", color=ink,
                    markersize=6, capsize=4, linewidth=1.5, zorder=5,
                    label="GRAIL · Park et al. (2025)" if m == 0 else None)
    ax.set_xticks(range(4), [f"$k_{{3{m}}}$" for m in range(4)])
    ax.set_xlim(-.5, 3.5)
    ax.set_ylim(0, .034)
    ax.set_yticks([0, .01, .02, .03])
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    ax.set_ylabel("Apparent $k_{3m}$ · elastic", color=muted, labelpad=10)
    ax.tick_params(axis="x", length=0, pad=8, colors=ink, labelsize=16)
    ax.tick_params(axis="y", colors=muted, labelsize=12)
    ax.grid(axis="y", color=line, alpha=.6, linewidth=.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(line)
    ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.19), ncol=2,
              frameon=False, labelcolor=ink, fontsize=11, columnspacing=1.6,
              handletextpad=.6, borderaxespad=0)
    ax.text(.5, 1.09, "GRAIL error bars: ±15 × formal uncertainty", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=10, color=muted)
    fig.savefig(OUT / f"grail-tidal-response-{theme}.svg", transparent=True,
                metadata={"Date": None, "Title": "Modelled tides span the GRAIL measurements",
                          "Description": "DPS poster panel 6: 19 elastic interiors, time-variable tide, 2012 GRAIL orbit."})
    plt.close(fig)
print("Built transparent light and dark tidal-response figures from 76 original values.")
