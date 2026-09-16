# Methodology

## Tool

Simulation uses [QTCAD](https://docs.nanoacademic.com/qtcad/) 2.2.5 (Nanoacademic
Technologies), a finite-element Schrödinger-Poisson solver for gated semiconductor
quantum devices. It is licensed software, see
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

**What QTCAD can do, used here:** non-linear (self-consistent) Poisson with
Fermi-Dirac statistics and incomplete ionization; effective-mass Schrödinger;
self-consistent Schrödinger-Poisson; many-body / chemical-potential addition
energies; multivalley EMT (a real valley-splitting calculation from Bloch
amplitudes, not a fitted constant).

**What it cannot do:** drift-diffusion transport, mobility models, self-heating,
band tails. There is no "threshold voltage" concept in the tool, any comparison
to a measured V_th needs a declared proxy, never presented as literally the
threshold.

## Pipeline

1. **Geometry** (`src/imec_qd_3x3_builder.py`), builds a 3×3 interior cell of the
   imec array (real gate widths, not the isolated single-cell shortcut used
   early on) via QTCAD's `Builder`/`Mask`/`Polygon` API, meshed coarsely
   everywhere except a refined region around the central dot.
2. **Device + solve** (`src/imec_qd_3x3_device.py`), defines materials, dopants,
   gate boundary conditions and the dot region, then solves the non-linear
   Poisson equation followed by the confined Schrödinger equation on a sub-mesh
   around the central dot.
3. **Campaigns** (`src/campaign_3x3.py`, `src/sweep_confinement.py`,
   `src/check_new_geometry.py`), sweep plunger/confinement bias, extracting
   lever arm, orbital spectrum, and many-body addition energies at each point.
4. **Post-hoc extraction** (`src/extract_field_barrier_footprint.py`), reloads a
   saved Poisson solution (no re-solve) to compute the vertical confining field,
   lateral barrier height, and dot footprint from the wavefunction.

## Two independently-defined lever arms

QTCAD documents these as genuinely different quantities, and conflating them is a
known pitfall: `leverarm.Solver` fits **single-particle energies** vs. gate bias;
the Coulomb-peak route fits **chemical potentials** vs. gate bias. Both are
reported here, under different names (`α_sp`, `α_μ`), and only compared to
literature values computed the same way.

## Implementation notes

- **Mesh physical-group selection uses a lambda predicate, not an indexed literal
  string** (`merge_groups(lambda g: ...)`), since the `[n]` hull-surface indices
  are not guaranteed to be stable across builds.
- **`analysis.gradient()` and `cond_band_edge()` return per-element/local-node
  arrays**, mapped to per-global-node via `mesh.toglobal()` before use.
- **`analysis.analyze_dot()`** is applied to the valley-summed density, since
  eigenfunctions carry a valley axis `(nodes, state, valley)` once
  `set_valley_splitting()` is used.
- **`set_valley_splitting(v)` sets `E[1] - E[0] = v` by construction**, that
  difference is the input valley splitting, not a computed quantity; the reported
  orbital spacing is `E[2] - E[0]`.
- **The non-linear Poisson solver is used for all physics results**; the linear
  solver (which neglects free carriers) is reserved for driving adaptive mesh
  refinement only.

## Reproducing the figures

- `src/make_figures_from_results.py`, figures 1–6, pure post-processing of the
  numbers in `results/*.txt`. Runs anywhere with matplotlib, no QTCAD required.
- `src/make_device_figures.py`, figures 7–9, device cross-sections and band
  diagrams sliced from a saved Poisson solution. Requires a QTCAD installation, a
  built mesh, and a saved potential field, none of which are shipped here (mesh
  files run 150–550 MB, and QTCAD is licensed software). See the script's
  docstring for exact regeneration steps.
