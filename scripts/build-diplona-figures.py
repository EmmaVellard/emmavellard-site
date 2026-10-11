"""Replot the reported curves of Diplona Fig. 4.21 by pixel digitisation.

Pillow/numpy/matplotlib required. The source JPEG is embedded on PDF page 49.
This does not reproduce/validate the radar calculation or its dB conversion.
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
ART = ROOT / "public/images/projects/ceres"
DATA = ROOT / "public/files/diplona"
QA = ROOT / "output/diplona-2026-10-09"
DATA.mkdir(parents=True, exist_ok=True)
SOURCE = ART / "snr-report-original.jpg"
im = np.asarray(Image.open(SOURCE).convert("RGB"), dtype=float)
assert im.shape == (262,389,3)
rows = []
references = [[116,146,157],[218,170,128],[127,161,128]]
for altitude, reference in zip([24,28,32],references):
    direction = 255-np.array(reference,dtype=float)
    direction /= np.linalg.norm(direction)
    for x in range(63,368):
        block = im[9:224,x]
        v = 255-block
        distance = np.linalg.norm(v/np.maximum(np.linalg.norm(v,axis=1,keepdims=True),1)-direction,axis=1)
        ys = np.flatnonzero((distance<.18)&(np.ptp(block,axis=1)>20))+9
        # The legend is above y=61 at x>279. Curves there are near y=190.
        ys = ys[(ys>64) | (x<279)]
        if not len(ys):
            continue
        y=float(np.median(ys))
        rows.append(dict(altitude_km=altitude,rms_slope_deg=(x-62)/12.2,reported_snr_db=10+(215-y)*120/199,pixel_x=x,pixel_y=y))
# JPEG antialiasing can make a neighbour's trace match a palette swatch. Use a
# local median only to define a source-pixel search corridor. Export actual
# coloured pixels, not the filtered coordinates, and omit ambiguous columns.
refined=[]
for altitude,reference in zip([24,28,32],references):
    trace=[r for r in rows if r['altitude_km']==altitude]
    direction=255-np.array(reference,dtype=float);direction/=np.linalg.norm(direction)
    for i,r in enumerate(trace):
        guide=np.median([p['pixel_y'] for p in trace[max(0,i-4):min(len(trace),i+5)]])
        x=r['pixel_x'];block=im[9:224,x];v=255-block
        distance=np.linalg.norm(v/np.maximum(np.linalg.norm(v,axis=1,keepdims=True),1)-direction,axis=1)
        yy=np.arange(9,224);valid=(distance<.23)&(np.ptp(block,axis=1)>20)&(np.abs(yy-guide)<3)
        if not valid.any():continue
        score=distance+.06*np.abs(yy-guide);score[~valid]=np.inf
        y=float(yy[np.argmin(score)])
        refined.append(dict(altitude_km=altitude,rms_slope_deg=r['rms_slope_deg'],reported_snr_db=10+(215-y)*120/199,pixel_x=x,pixel_y=y))
rows=refined
assert len(rows)>800
for altitude in [24,28,32]:
    trace=[r for r in rows if r['altitude_km']==altitude]
    assert len(trace)>250
    assert trace[0]['reported_snr_db']>trace[-1]['reported_snr_db']
with (DATA/'snr-digitised.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader()
    for row in rows:
        writer.writerow({k:round(v,4) if isinstance(v,float) else v for k,v in row.items()})
provenance={
    "status":"Approximate digitisation of reported model curves, NOT raw simulation output or flight measurements.",
    "report":"/files/cerereport.pdf", "pdf_page":49,"printed_page":37,"figure":"4.21",
    "source_image":"/images/projects/ceres/snr-report-original.jpg",
    "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "method":"JPEG colour traces sampled by image column. A nine-column median defines a narrow search corridor to avoid neighbouring traces; all exported coordinates are matching source pixels, not the median-filtered guide. Calibrated ticks: x=62/367 at slope 0/25 degrees; y=215/16 at SNR 10/130 dB. No fitted or extrapolated curves.",
    "limitations":"JPEG compression, overlaps and finite pixel resolution prevent exact recovery. The original radar-equation implementation, dB conversion, stretch-processing assumptions and noise budget were not independently reproduced. This redraw does not validate the reported SNR magnitudes or flight feasibility. Near-zero slope behaviour belongs to the reported idealised model.",
    "resolution":"Approximately 0.082 degrees horizontally and 0.603 dB vertically per source pixel. This is image resolution, not a scientific uncertainty estimate.",
    "model_context":"Table 4.4 uses 1 W emitted power, gain 1.5, wavelength 10 m, transmissivity 0.9, reflectivity 0.1, 60 m depth, attenuation 0.14, refractive index sqrt(3), noise temperature 290 K, noise factor 10, and altitudes 24/28/32 km. These are study assumptions, not observed properties.",
    "renderer":"scripts/build-diplona-figures.py",
}
(DATA/'snr-provenance.json').write_text(json.dumps(provenance,indent=2)+"\n")
plt.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Arial","DejaVu Sans"],"font.size":12,"svg.fonttype":"none","svg.hashsalt":"diplona-snr","axes.linewidth":.6})
for theme,p in {
    "light":dict(ink="#0d2140",muted="#44597a",grid="#b8cce2",colours=["#2a62b8","#287b80","#8567b0"]),
    "dark":dict(ink="#e6eef9",muted="#9fb2cc",grid="#33455e",colours=["#8fc6e3","#77cbc5","#baa1dd"]),
}.items():
    for mobile in [False,True]:
        fig,ax=plt.subplots(figsize=(4.4,4.2) if mobile else (7.2,4.6))
        fig.subplots_adjust(left=.19 if mobile else .12,right=.97,bottom=.2,top=.92)
        ax.set_facecolor('none');ax.set_axisbelow(True)
        ax.grid(axis='y',color=p['grid'],alpha=.65,lw=.65)
        for spine in ['top','right']:ax.spines[spine].set_visible(False)
        for spine in ['left','bottom']:ax.spines[spine].set_color(p['grid'])
        for index,altitude in enumerate([24,28,32]):
            pts=[r for r in rows if r['altitude_km']==altitude]
            ax.plot([r['rms_slope_deg'] for r in pts],[r['reported_snr_db'] for r in pts],color=p['colours'][index],lw=1.7,linestyle=['-','--','-.'][index])
        ax.tick_params(colors=p['muted'],labelsize=11,length=3,pad=7)
        ax.set_xlim(0,25);ax.set_ylim(0,140);ax.set_xticks([0,5,10,15,20,25]);ax.set_yticks([0,20,40,60,80,100,120,140])
        ax.set_xlabel('Surface RMS slope · °',color=p['muted'],labelpad=12)
        ax.set_ylabel('Reported SNR · dB',color=p['muted'],labelpad=12)
        suffix=f'{theme}-mobile' if mobile else theme
        fig.savefig(ART/f'snr-surface-slope-{suffix}.svg',transparent=True,metadata={"Date":None,"Description":"Approximate digitisation of Diplona report Fig. 4.21; not independently validated radar performance."})
        fig.savefig(QA/f'snr-{suffix}.png',transparent=True,dpi=150);plt.close(fig)
# Source-pixel overlay for visual QA.
fig,ax=plt.subplots(figsize=(10,7));ax.imshow(im.astype(np.uint8))
for altitude,colour in zip([24,28,32],['#2a62b8','#287b80','#8567b0']):
    pts=[r for r in rows if r['altitude_km']==altitude]
    ax.scatter([r['pixel_x'] for r in pts],[r['pixel_y'] for r in pts],s=8,facecolors='none',edgecolors=colour,lw=.5)
ax.axis('off');fig.savefig(QA/'snr-source-overlay.png',dpi=150,bbox_inches='tight');plt.close(fig)
print(f'{len(rows)} digitised coordinates; three reported altitude curves; four transparent SVGs.')
