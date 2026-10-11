"""Digitise report Figures 8/10 and render transparent portfolio SVGs.

Requires Pillow, numpy and matplotlib. The report embeds JPEGs, not numerical
data. These coordinates are display approximations, NOT recovered measurements.
Run with MPLCONFIGDIR in a writable directory. No network or curve fitting.
"""
from pathlib import Path
import csv
import hashlib
import json

import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "public/images/projects/phobos-deimos"
DATA = ROOT / "public/files/phobos-deimos"
QA = ROOT / "output/phobos-figures-2026-10-09"
for path in (DATA, QA):
    path.mkdir(parents=True, exist_ok=True)

IDS = ["more1", "1btw250", "less1", "less250", "less125", "less53", "CRISM Phobos red", "CRISM Phobos blue"]
LABELS = ["> 1 mm", "250 µm–1 mm", "< 1 mm", "< 250 µm", "< 125 µm", "< 53 µm", "Phobos · red unit", "Phobos · blue unit"]
# JPEG legend swatches: whitened antialiasing is removed by direction matching.
SOURCE_RGB = np.array([[28,108,109], [198,125,134], [122,101,181], [130,163,135], [209,176,143], [90,131,200], [198,99,70], [47,87,173]])
BANDS = np.array([.39, .48, .55, .65, .73, .86, .95])
BAND_NAMES = ["ul", "b", "v", "d", "e", "x", "p"]

def image_data(name):
    return np.asarray(Image.open(ART / f"{name}-report-full.jpg").convert("RGB"), dtype=float)

def colour_distance(rgb, reference):
    v = 255 - rgb
    d = 255 - np.array(reference)
    return np.linalg.norm(v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1) - d / np.linalg.norm(d), axis=-1)

def pick_y(image, x, seed, reference, radius=7):
    """Select a coloured trace near a visually identified source-pixel guide.

    A local guide prevents adjacent blue/red curves from exchanging identities.
    No point is invented when there is no coloured evidence in the search window.
    """
    ix = int(round(x))
    low, high = max(0, int(seed-radius)), min(image.shape[0], int(seed+radius+1))
    left, right = max(0, ix-2), min(image.shape[1], ix+3)
    block = image[low:high, left:right]
    dist = colour_distance(block, reference)
    valid = (np.ptp(block, axis=-1) > (12 if np.ptp(reference)<40 else 23)) & (dist < .25)
    yy, xx = np.mgrid[low:high, left:right]
    if not valid.any():
        return None
    score = dist + .012 * np.abs(yy-seed) + .008 * np.abs(xx-x)
    score[~valid] = np.inf
    best = np.unravel_index(np.argmin(score), score.shape)
    return float(yy[best])

# Pixel guides for the band-average lines, NOT estimates of underlying raw data.
# Nulls are the missing CRISM d-band; the original line breaks are retained.
OROCHI_GUIDES = {
    "absolute": [
        [399,394,391,394,393,384,374], [430,413,405,405,405,404,392],
        [373,363,355,348,343,329,307], [385,365,350,341,332,317,308],
        [371,363,355,348,344,327,300], [414,399,384,362,350,332,318],
        [343,400,368,None,284,199,159], [174,221,183,None,133,94,78],
    ],
    "normalised": [
        [347,337,332,335,335,321,309], [357,346,332,334,334,328,313],
        [369,347,332,325,317,297,278], [370,347,332,319,308,289,281],
        [364,347,332,330,326,293,270], [367,347,332,300,284,260,242],
        [302,380,332,None,230,122,68], [327,369,332,None,282,243,225],
    ],
}

rows = []
orochi = image_data("orochi")
for panel, guides in OROCHI_GUIDES.items():
    x0 = 89 if panel == "absolute" else 676
    # Grid calibration: .4/.9 µm at x=89/534 and 676/1121.
    for series, seeds in enumerate(guides):
        for wavelength, seed in zip(BANDS, seeds):
            if seed is None:
                continue
            x = x0 + (wavelength-.4)*890
            y = pick_y(orochi, x, seed, SOURCE_RGB[series])
            if y is None:
                # At overlapping band markers JPEG colour mixing can obscure a
                # trace. Retain its visually digitised pixel guide, flag it below.
                y = float(seed)
                kind = "band-average-manual-overlap"
            else:
                kind = "band-average"
            value = 4.5 - (y-33)/200 if panel == "absolute" else 1.4-(y-33)/748
            rows.append(dict(instrument="orochi", panel=panel, series=IDS[series], wavelength_um=float(wavelength), reflectance=value, pixel_x=x, pixel_y=y, kind=kind))

# Figure 10 left-panel guides. Interpolation is only a search corridor in the
# source image; every exported value must still have a matching coloured pixel.
MIRS_X = np.array([56,74,167,259,351,370,380,384,388,392,396,400,408,425,444,463,482,500,518,536,553])
MIRS_GUIDES = np.array([
    [326,321,306,298,296,296,301,310,371,368,345,344,338,325,315,307,304,298,301,298,297],
    [329,324,315,314,314,314,319,326,378,373,367,355,351,345,343,339,334,324,330,326,320],
    [311,301,275,264,258,258,262,280,368,365,353,335,326,317,309,297,282,273,277,273,254],
    [312,298,269,256,246,245,253,270,361,357,350,328,319,312,304,290,274,264,269,265,249],
    [308,295,265,254,243,241,246,264,356,353,349,325,317,306,298,285,268,259,264,260,240],
    [313,300,275,259,247,246,249,266,358,356,352,328,321,311,303,289,273,265,269,266,245],
])
mirs = image_data("mirs")
for series in range(6):
    for x in range(57,554,3):
        seed = np.interp(x, MIRS_X, MIRS_GUIDES[series])
        y = pick_y(mirs, x, seed, SOURCE_RGB[series], radius=6)
        if y is None:
            continue
        rows.append(dict(instrument="mirs", panel="absolute", series=IDS[series], wavelength_um=1+(x-74)/184.8, reflectance=8-(y-38)/54.6, pixel_x=x, pixel_y=y, kind="trace"))

# CRISM points use coral/blue crosses in Fig. 10, unlike Fig. 8's red/blue lines.
# They lie above the laboratory traces in the absolute panel, allowing extraction
# without confusing them with the similarly coloured laboratory fractions.
for series, reference in [(6, SOURCE_RGB[1]), (7, SOURCE_RGB[5])]:
    for x in range(57,447,3):
        top_lab = min(np.interp(x, MIRS_X, g) for g in MIRS_GUIDES)
        block = mirs[11:int(top_lab-12), x-1:x+2]
        dist = colour_distance(block, reference)
        mask = (np.ptp(block, axis=-1)>36) & (dist<.17)
        yy = np.flatnonzero(mask.any(axis=1)) + 11
        if not len(yy):
            continue
        # Keep separated outliers instead of replacing the cloud with a smooth fit.
        for group in np.split(yy, np.flatnonzero(np.diff(yy)>4)+1):
            y = float(np.median(group))
            rows.append(dict(instrument="mirs", panel="absolute", series=IDS[series], wavelength_um=1+(x-74)/184.8, reflectance=8-(y-38)/54.6, pixel_x=x, pixel_y=y, kind="scatter"))

# Digitise the right panel independently rather than imposing a new numerical
# normalisation on Fig. 10. Its guides use the left-panel shape for identification.
for series in range(8):
    source = [r for r in rows if r["instrument"] == "mirs" and r["panel"] == "absolute" and r["series"] == IDS[series]]
    anchor = min(source, key=lambda r: abs(r["wavelength_um"]-2.5))["reflectance"]
    for r in source:
        x = 659+(r["wavelength_um"]-1)*185.2
        seed = 10+(1.3-r["reflectance"]/anchor)*450
        reference = SOURCE_RGB[series] if series<6 else SOURCE_RGB[1 if series==6 else 5]
        y = pick_y(mirs, x, seed, reference, radius=8 if series<6 else 12)
        if y is None:
            continue
        rows.append(dict(instrument="mirs", panel="normalised", series=IDS[series], wavelength_um=r["wavelength_um"], reflectance=1.3-(y-10)/450, pixel_x=x, pixel_y=y, kind=r["kind"]))

for instrument in ("orochi", "mirs"):
    selected = [r for r in rows if r["instrument"] == instrument]
    with (DATA / f"{instrument}-digitised.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        for r in selected:
            writer.writerow({k: f"{v:.6f}" if isinstance(v,float) else v for k,v in r.items()})

provenance = {
    "status": "Approximate pixel digitisation; NOT original numerical measurements or uncertainty estimates.",
    "source": "/files/phobosreport.pdf", "figure_pages": {"orochi":21,"mirs":23},
    "source_sha256": {name: hashlib.sha256((ART/f"{name}-report-full.jpg").read_bytes()).hexdigest() for name in ("orochi","mirs")},
    "method": "Calibrated JPEG axes; colour-matched source pixels within visually identified trace corridors. OROCHI overlapping markers use manual pixel guides where JPEG colour matching fails, flagged in CSV kind. Both panels digitised independently. No spectral fit or invented missing values.",
    "OROCHI": "Seven nominal band centres. Only band-average lines are redrawn; faint underlying spectra are omitted. CRISM has no d-band value; no connection is drawn across it.",
    "MIRS": "Laboratory trace sampled every 3 image pixels (about 0.016 micrometres), not a fresh 20 nm instrument simulation. CRISM source-pixel clusters retained as approximate scatter, including visible outliers. No extrapolation beyond the observed coverage.",
    "resolution": "One vertical pixel is 0.005 reflectance percentage points for OROCHI absolute, 0.00134 for OROCHI normalised, 0.0183 percentage points for MIRS absolute and 0.00222 for MIRS normalised. Extraction/overlap may introduce larger errors; pixel resolution is not measurement uncertainty.",
    "limitations": "JPEG compression, antialiasing, overlapping traces and finite source resolution prevent exact recovery. Marker count and coordinates may differ from original data. Do not use these CSVs for scientific inference or band-depth calculations; consult original measurements.",
    "renderer": "scripts/build-phobos-figures.py", "series_labels": dict(zip(IDS,LABELS)),
}
(DATA / "digitisation-provenance.json").write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+"\n")

plt.rcParams.update({"font.family":"sans-serif", "font.sans-serif":["Arial","DejaVu Sans"], "font.size":12, "svg.fonttype":"none", "svg.hashsalt":"phobos-report-digitisation", "axes.linewidth":.6})
PALETTES = {
    "light": dict(ink="#0d2140",muted="#44597a",grid="#b8cce2",colours=["#287b80","#b86777","#8567b0","#628566","#a77a42","#5d83bf","#c05c3f","#2a55a1"]),
    "dark": dict(ink="#e6eef9",muted="#9fb2cc",grid="#33455e",colours=["#77cbc5","#e39aa9","#baa1dd","#a4c69d","#dbb17d","#9bbbe5","#f3a086","#7ca6ee"]),
}

def draw(instrument, panel, theme, mobile=False):
    palette = PALETTES[theme]
    fig, ax = plt.subplots(figsize=(4.4,4.1) if mobile else (6.4,4.6))
    fig.subplots_adjust(left=.19 if mobile else .14,right=.97,bottom=.19 if mobile else .17,top=.85 if mobile else .88)
    ax.set_facecolor("none")
    for spine in ("top","right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left","bottom"):
        ax.spines[spine].set_color(palette["grid"])
    ax.tick_params(colors=palette["muted"],labelsize=11,length=3,pad=7)
    ax.grid(axis="y",color=palette["grid"],lw=.65,alpha=.6)
    ax.set_axisbelow(True)
    for series in range(8):
        pts = sorted([r for r in rows if r["instrument"]==instrument and r["panel"]==panel and r["series"]==IDS[series]],key=lambda r:r["wavelength_um"])
        assert len(pts)>3, (instrument,panel,IDS[series])
        x = np.array([r["wavelength_um"] for r in pts]); y = np.array([r["reflectance"] for r in pts])
        colour = palette["colours"][series]
        if instrument=="mirs":
            ax.plot(x,y,"+" if series>=6 else ".",ms=4 if series>=6 else 3,mew=.9,color=colour,alpha=.8)
        else:
            # No joining missing intervals in the source image.
            threshold = .15 if instrument=="orochi" else .045
            breaks = np.flatnonzero(np.diff(x)>threshold)+1
            for indices in np.split(np.arange(len(x)),breaks):
                ax.plot(x[indices],y[indices],color=colour,lw=1.55 if series<6 else 2,
                        linestyle="--" if series in (1,3,5) else "-",
                        marker="o" if instrument=="orochi" else None,ms=3.2)
    ax.set_xlabel("Wavelength · µm",color=palette["muted"],labelpad=12)
    ax.set_ylabel("Reflectance · %" if panel=="absolute" else "Normalised reflectance",color=palette["muted"],labelpad=10)
    if instrument=="orochi":
        ax.set_xlim(.38,.96); ax.set_xticks(np.arange(.4,1,.1))
        ax.set_ylim((2.45,4.5) if panel=="absolute" else (.85,1.4))
        for wavelength,name in zip(BANDS,BAND_NAMES):
            ax.axvline(wavelength,color=palette["grid"],lw=.6,alpha=.65)
            ax.text(wavelength,1.035,name,transform=ax.get_xaxis_transform(),ha="center",color=palette["muted"],fontsize=11)
    else:
        ax.set_xlim(.9,3.6); ax.set_xticks(np.arange(1,3.6,.5))
        ax.set_ylim((1.5,8.5) if panel=="absolute" else (.45,1.3))
    if panel=="normalised":
        anchor = .55 if instrument=="orochi" else 2.5
        ax.axhline(1,color=palette["muted"],lw=.7,alpha=.6,ls=(0,(2,4)))
        ax.axvline(anchor,color=palette["muted"],lw=.7,alpha=.6,ls=(0,(2,4)))
    suffix = f"{theme}-mobile" if mobile else theme
    fig.savefig(ART / f"{instrument}-{panel}-{suffix}.svg",transparent=True,metadata={"Date":None,"Description":f"Approximate digitisation of report Figure {8 if instrument=='orochi' else 10}; see /files/phobos-deimos/digitisation-provenance.json"})
    fig.savefig(QA / f"{instrument}-{panel}-{suffix}.png",dpi=150,transparent=True)
    plt.close(fig)

for instrument in ("orochi","mirs"):
    for panel in ("absolute","normalised"):
        for theme in PALETTES:
            draw(instrument,panel,theme)
            draw(instrument,panel,theme,mobile=True)

# Inspectable source-pixel overlays expose misidentified or missing traces.
for instrument in ("orochi","mirs"):
    fig, ax = plt.subplots(figsize=(14,6))
    ax.imshow(image_data(instrument).astype(np.uint8))
    for series in range(8):
        pts=[r for r in rows if r["instrument"]==instrument and r["series"]==IDS[series]]
        ax.scatter([r["pixel_x"] for r in pts],[r["pixel_y"] for r in pts],s=9,facecolors="none",edgecolors=PALETTES["light"]["colours"][series],linewidths=.7)
    ax.axis("off")
    fig.savefig(QA/f"{instrument}-digitisation-overlay.png",dpi=170,bbox_inches="tight")
    plt.close(fig)
print(json.dumps({name:{panel:{series:sum(r['instrument']==name and r['panel']==panel and r['series']==series for r in rows) for series in IDS} for panel in ('absolute','normalised')} for name in ('orochi','mirs')},indent=2))
