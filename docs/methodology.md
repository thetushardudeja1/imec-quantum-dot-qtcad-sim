# Methodology

## Tool

Simulation uses [QTCAD](https://docs.nanoacademic.com/qtcad/) 2.2.5 (Nanoacademic
Technologies), a finite-element Schrödinger-Poisson solver for gated semiconductor
quantum devices. It is licensed software — see
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

**What QTCAD can do, used here:** non-linear (self-consistent) Poisson with
Fermi-Dirac statistics and incomplete ionization; effective-mass Schrödinger;
self-consistent Schrödinger-Poisson; many-body / chemical-potential addition
energies; multivalley EMT (a real valley-splitting calculation from Bloch
amplitudes, not a fitted constant).

**What it cannot do:** drift-diffusion transport, mobility models, self-heating,
band tails. There is no "threshold voltage" concept in the tool — any comparison
to a measured V_th needs a declared proxy, never presented as literally the
threshold.

## Pipeline

1. **Geometry** (`src/imec_qd_3x3_builder.py`) — builds a 3×3 interior cell of the
   imec array (real gate widths, not the isolated single-cell shortcut used
   early on) via QTCAD's `Builder`/`Mask`/`Polygon` API, meshed coarsely
   everywhere except a refined region around the central dot.
2. **Device + solve** (`src/imec_qd_3x3_device.py`) — defines materials, dopants,
   gate boundary conditions and the dot region, then solves the non-linear
   Poisson equation followed by the confined Schrödinger equation on a sub-mesh
   around the central dot.
3. **Campaigns** (`src/campaign_3x3.py`, `src/sweep_confinement.py`,
   `src/check_new_geometry.py`) — sweep plunger/confinement bias, extracting
   lever arm, orbital spectrum, and many-body addition energies at each point.
4. **Post-hoc extraction** (`src/extract_field_barrier_footprint.py`) — reloads a
   saved Poisson solution (no re-solve) to compute the vertical confining field,
   lateral barrier height, and dot footprint from the wavefunction.

## Two independently-defined lever arms

QTCAD documents these as genuinely different quantities, and conflating them is a
known pitfall: `leverarm.Solver` fits **single-particle energies** vs. gate bias;
the Coulomb-peak route fits **chemical potentials** vs. gate bias. Both are
reported here, under different names (`α_sp`, `α_μ`), and only compared to
literature values computed the same way. See [validation.md](validation.md) for
where an earlier version of this project got that wrong.

## Verified pitfalls worth recording

A few QTCAD API behaviors cost real debugging time and are worth flagging for
anyone using the same tool:

- **`set_dot_region()` must be called before any non-linear Poisson solve that
  contains a dot.** It zeroes the classical (Thomas-Fermi) charge density inside
  the dot region so those electrons are treated quantum-mechanically. Omitting it
  lets a classical electron gas form inside the dot and screen the gate — the
  solve still converges, and everything downstream is quietly wrong. See
  [debugging_notes.md](debugging_notes.md) for the full story.
- **Mesh physical-group selection must use a lambda predicate, not an indexed
  literal string.** Selecting `"boundary[3]"` by name silently no-ops (no error)
  when the `[n]` hull-surface indices aren't assigned yet at selection time.
  `merge_groups(lambda g: ...)` is the reliable pattern.
- **`analysis.gradient()` and `cond_band_edge()` return per-element/local-node
  arrays**, not per-global-node. They must be passed through `mesh.toglobal()`
  before being indexed with a node mask, or indexing silently returns garbage
  values with no error.
- **`analysis.analyze_dot()` breaks when valley splitting is set** — eigenfunctions
  gain a valley axis `(nodes, state, valley)` that the function doesn't expect.
  Sum over the valley axis before computing wavefunction moments.
- **`set_valley_splitting(v)` makes `E[1] - E[0]` equal to `v` by construction.**
  That difference is an input readback, not a computed splitting — the first real
  *orbital* spacing is `E[2] - E[0]`.
- **Two Poisson solvers exist and only one is physical.** The linear solver
  neglects free carriers entirely (fine for driving adaptive mesh refinement, never
  for physics with an occupied dot).

## Reproducing the figures

- `src/make_figures_from_results.py` — figures 1–6, pure post-processing of the
  numbers in `results/*.txt`. Runs anywhere with matplotlib, no QTCAD required.
- `src/make_device_figures.py` — figures 7–9, device cross-sections and band
  diagrams sliced from a saved Poisson solution. Requires a QTCAD installation, a
  built mesh, and a saved potential field, none of which are shipped here (mesh
  files run 150–550 MB, and QTCAD is licensed software). See the script's
  docstring for exact regeneration steps.
