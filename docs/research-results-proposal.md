# Research results proposal

The local Research page places the results after the Approach workflow and its comparison illustration.
All numbers come from the supplied `public/files/posters/VELLARD_PosterDPS58.pdf`, dated 28 October 2026.

- The selection graphic uses the exact counts in panel 2: 1,425 mass-matching interiors; 19 also match moment of inertia and core radius; 7 homogeneous, 5 layered and 7 FeO-rich mantles.
- The transparent tidal-response graphic redraws panel 6 from its original data: 19 elastic interiors × four orders. The GRAIL comparison uses Park et al.'s values and ±15 × formal uncertainty, as in the poster. Overlap by order is not a simultaneous fit by one model.
- The tidal summary uses the poster's stated range of 2.5–2.8× in k3m across the 19 interiors, and distinguishes the 2 GRAIL degree-1 matches from the absence of a joint match with Apollo heat flow.
- These statements describe this particular model grid and its assumptions. They are not a unique inference of the Moon's interior.

Figure provenance and source SHA-256 are recorded in `docs/dps-2026-figure-provenance.json`, kept out of the visitor interface.
The pinned CSV keeps the original model identifiers, orders, time-variable tidal responses and Park comparison values from `lunar-bsm-interior-models/results/dps_2026_followup/N4/G1_19_4PI/G1_APPARENT_K3M.csv` (`K_set=ELASTIC`), the same input used by `make_poster_v41_figures.py`.
Rebuild the figures with Node and Python with Matplotlib:

```sh
node scripts/build-lunar-results.mjs
python3 scripts/build-lunar-tides.py
```

The January SolarConflux section keeps its existing two figures. The duplicate slider demo was removed; the call to action now scrolls to the worked example.

The image preparation script is a one-off optimisation of the images referenced by a production build. It is deliberately not run as part of normal builds, to avoid repeated lossy re-encoding.
