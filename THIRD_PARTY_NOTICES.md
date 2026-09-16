# Third-party notices

## QTCAD (required to run the simulation code)

This project's simulation scripts (`src/imec_qd_3x3_builder.py`,
`src/imec_qd_3x3_device.py`, `src/campaign_3x3.py`,
`src/extract_field_barrier_footprint.py`, `src/sweep_confinement.py`,
`src/check_new_geometry.py`, `src/make_device_figures.py`) depend on **QTCAD**, a
finite-element Schrödinger-Poisson solver developed and licensed by
**Nanoacademic Technologies Inc.** (<https://nanoacademic.com>).

QTCAD is **not included** in this repository. It is commercial, licensed software
and is not the author's to redistribute. To run any script that imports `qtcad`,
obtain a license directly from Nanoacademic Technologies
(<https://docs.nanoacademic.com/qtcad/>).

If you use QTCAD in your own work, Nanoacademic requests specific citation,
see <https://docs.nanoacademic.com/qtcad/citing/> for their current guidance.

## Data and geometry not included

Generated FEM meshes (`.msh`/`.xao`) and saved potential fields (`.hdf5`) are not
included in this repository: they are 150–550 MB per file (over GitHub's size
limits) and are regenerable from the shipped builder/device scripts given a QTCAD
license. `src/imec_qd_3x3_builder.py` regenerates the mesh; running the relevant
device script regenerates the potential field.

## Cited literature

Papers referenced in the documentation and code comments are cited (author, venue,
year), not reproduced. See [docs/references.md](docs/references.md).
