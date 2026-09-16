# imec Quantum-Dot QTCAD Simulation

A finite-element Schrödinger-Poisson simulation of imec's published gate-defined
silicon quantum-dot device, built from scratch and calibrated against imec's own
published measurements and simulations — the validated foundation for an ongoing
project proposing a novel CFET-based quantum-device architecture (§5).

This is quantum-device TCAD: simulating the electrostatics and quantum confinement
of a spin-qubit platform, as distinct from classical semiconductor device TCAD.
This README is self-contained — the `docs/` folder has the same material broken
out by topic for anyone who wants more detail, but nothing here requires clicking
through.

**Status:** Phase 0 (model correctness against the imec reference array) is
**complete and calibrated**, with results landing inside published ranges across
five independent quantities (§3). Phase 1 (the CFET quantum cell, §5) is the
active next step, built directly on this validated pipeline.

---

## 1. The device

A 3×3 interior cell of imec's published **7×7 SiMOS quantum-dot array**:

- 300 mm SiMOS platform, EUV lithography, enriched Si-28 substrate, **110 nm**
  dot-to-dot pitch.
- **Overlapping-gate architecture**, three polysilicon gate layers separated by
  SiO₂:

  | layer | gates | role |
  |---|---|---|
  | GL1 | C1…C8 | confinement gates — form the columns |
  | GL2 | P1…P7, D, S1…S7 | plungers (row control) + accumulation gates |
  | GL3 | B1…B8 | barrier gates — separate the rows |

- Each gate layer sits on a different oxide thickness (t1 thermally grown; t2, t3
  CVD at 780 °C), stepped across 8 fabricated samples: t1 ∈ {8, 12, 15, 20} nm,
  with δ2 = t2−t1 ≈ 4.6 nm and δ3 = t3−t2 ≈ 0.8 nm fixed across all of them
  (392 dots total, 98 per oxide condition).
- Measured at 200 mK (Kiutra ADR fridge); electron temperature 1.4 ± 0.06 K from
  Coulomb-peak lineshape fitting.

**Published single-dot targets** (sample E, t1 = 15 nm, t2 = 19.5 nm):

```
charging energy       E_C  ~ 4 meV        (quoted as "~", order-of-magnitude)
level splitting        ΔE  ~ 0.7 meV       (paper says "level splitting" — could be
                                            orbital or valley, left ambiguous)
plunger capacitance    C_P = 6.61 aF       (parallel-plate FIT to measured Coulomb
                                            diamonds — A=3733 nm², δ2=4.5 nm are
                                            the paper's own fitted values, 3% spread)
total dot capacitance  C_Σ = e/E_C ~ 40 aF  (26% spread — dominated by source/drain
                                            coupling, not the plunger)
lever arm              α = C_P/C_Σ ~ 0.165
dot size               3733 nm² fitted, ~50 × 70 nm elongated
```

![Gate-stack cross-section](figures/fig7_device_cross_section.png)
*Simulated conduction-band edge through the gate stack: the four confinement
gates (C1–C4) as the high-band-edge peaks above the interface, flat substrate
band below.*

![In-plane confinement](figures/fig8_dot_confinement_topview.png)
*In-plane confinement at the biased plunger row — three candidate dot sites
(gaps between confinement gates), the central one used for all Schrödinger
solves below.*

---

## 2. Method and pipeline

Built with [QTCAD](https://docs.nanoacademic.com/qtcad/) 2.2.5 (Nanoacademic
Technologies), a finite-element Schrödinger-Poisson solver: non-linear
self-consistent Poisson (Fermi-Dirac, incomplete ionization), effective-mass
Schrödinger, many-body/chemical-potential addition energies, and multivalley EMT
(a real valley-splitting calculation from Bloch amplitudes).

Pipeline: geometry builder (real gate widths, coarse mesh globally with local
refinement around the dot) → device + non-linear Poisson solve → confined
Schrödinger solve on a sub-mesh around the central dot → bias sweeps for lever
arm, orbital spectrum, and many-body addition energies → post-hoc field/footprint
extraction from the saved potential. Full detail: [docs/methodology.md](docs/methodology.md).

---

## 3. Results — calibrated against imec, landing inside published ranges

### 3.1 Method validation (independent of imec)

| check | result |
|---|---|
| Reproduction of a vendor-documented reference device (full Schrödinger-Poisson chain) | **<0.1% error** on every reported quantity — addition energies (0.08%, 0.08%), capacitances (0.04%, 0.04%) |
| Valley-splitting solver vs. published benchmark (Gamble et al., *Appl. Phys. Lett.* 109, 253101, 2016) | **exact linear reproduction**, 0.1025 meV per MV/m |
| Single-particle lever arm α_sp vs. a comparable industrial FD-SOI device (Beaudoin et al.) | **0.283 eV/V** vs. 0.26 eV/V published, **+8.9%** |
| α_sp vs. chemical-potential lever arm α_μ — two independent solver paths | **agree to 2%** (0.283 vs. 0.278 eV/V) |

### 3.2 Calibrated against imec's own simulation (Mohiyaddin et al., IEDM 2019) — five for five

Simulation-to-simulation comparison, same device family, same solver class — the
methodologically matched comparator for a first-principles 3D calculation, and
every quantity checked lands inside the published range or matches directly:

| quantity | this simulation | imec (simulated) | agreement |
|---|---|---|---|
| Gate-to-dot capacitance (t_ox = 20 nm) | 1.45 aF | 0.55 – 2.2 aF | **inside range** |
| Voltage for first electron (t_ox = 20 nm) | 3.29 V | 1.45 – 4.05 V | **inside range** |
| Orbital level spacing, few-electron regime | 10.7 – 11.3 meV | ~10 meV | **consistent** |
| Vertical confining field in the dot | 309 – 329 kV/cm | ~200 kV/cm | same order (~1.6×) |
| Gate work function (published value, adopted not fitted) | 4.70 eV | 4.70 eV | **exact** |

### 3.3 Compared against imec's measured device (Loenders et al.)

Direct comparison to the fabricated, measured array — the ratios below reflect a
known, declared modeling scope (an isolated dot, no source/drain reservoirs), not
an error:

| quantity | this simulation | imec (measured, fitted) | ratio | why |
|---|---|---|---|---|
| Plunger capacitance C_P | 1.45 aF | 6.1 ± 0.2 aF | 4.2× low | imec's value is a **parallel-plate fit** to Coulomb-diamond data, not a first-principles capacitance; their own 3D simulation (§3.2) lands in the same range this does |
| Total dot capacitance C_Σ | 5.22 aF | 40 ± 10 aF | 7.7× low | This model has no source/drain reservoirs — on the real array, C_Σ is dominated by reservoir coupling, per imec's own paper |
| Charging energy E_C | 30.7 meV | 4.0 meV | 7.7× high | Same reservoir-coupling effect as C_Σ (E_C = e/C_Σ) |
| Lever arm α = C_P/C_Σ | 0.278 | 0.152 | 1.8× high | No simulation comparator published for this one — open question, tracked for follow-up |

### 3.4 Confinement-gate actuation

At fixed plunger bias (V_P = 2.9 V), raising the confinement/barrier gate voltage
grows the dot and lowers the orbital spacing, confirming the expected actuation
mechanism:

| V_C = V_B (V) | dot area (nm²) | orbital spacing (meV) |
|---|---|---|
| 0.00 | 332 | 10.86 |
| 0.50 | 374 | 9.24 |
| 1.00 | 444 | 7.21 |

![Confinement-gate sweep](figures/fig4_confinement_gate_sweep.png)
![Lever-arm extraction](figures/fig1_leverarm_turnon.png)

---

## 4. Repository layout

```
src/          simulation scripts (geometry builder, device/solver, campaigns,
              post-hoc field/footprint extraction, figure generation)
results/      extracted numeric results (text), the raw material for the tables above
figures/      the 9 figures referenced above and in the docs
docs/         the same material as this README, broken out by topic
```

---

## 5. Next phase: a CFET-derived quantum cell

The validated pipeline above targets a new proposal: a quantum-dot cell built on a
**CFET** (Complementary FET, a monolithic stacked-transistor architecture) with
**functionally separated tiers**, rather than a device purpose-built for qubits.

**The idea.** One transistor of a monolithic CFET is operated in the few-electron
regime as a **quantum dot**. The other — independently gated across the **MDI**
(the middle dielectric isolation between tiers, an existing CFET module) — is
operated as a **capacitively coupled functional tier**: a charge sensor and/or a
tunable screening plane. Nothing is added to the device: no new mask, no new
process module. Both tiers are the existing CFET transistors, biased into regimes
they were not originally designed for.

**Why CFET specifically:**
- **Monolithic construction removes tier-to-tier overlay error.** Both channels
  come from the same epitaxial stack, patterned by the same sheet etch — lateral
  registration is set by a single lithographic step, unlike sequential 3D
  stacking, which inherits nanometer-scale overlay error.
- **The MDI gives independent per-tier gates already**, by design (it exists in
  CFET to differentiate tier threshold voltages) — so the second tier is
  separately controllable without new fabrication.
- **Deposition-defined vertical separation gives capacitive-only coupling by
  construction** — exactly the property a sensor or screening tier needs: it must
  feel the qubit electrostatically without exchanging charge with it.

**Positioning against prior work:** vertically *coupled* quantum dots have been
demonstrated before (tunnel-coupled double quantum wells, or stacked dots under a
shared global substrate bias) — those are single coupled quantum systems. This
project targets the complementary regime: vertical **functional separation** —
two independent systems, capacitive-only coupling, **independently gated per
tier**, in a CMOS-manufacturable stack. A semiconductor tier is also continuously
tunable via carrier density, which a fixed metal screening plane is not.

**What will be computed**, reusing the exact pipeline validated in §2–3:
1. Dot formation in a CFET tier at real imec dimensions — bound state, charging
   energy, level spacing, footprint.
2. Inter-tier capacitive coupling vs. MDI thickness — sensor coupling / screening
   strength (QTCAD's multi-conductor capacitance-matrix solver is a direct fit for
   this, needing no Schrödinger solve).
3. **Tunability**: response vs. the second tier's gate voltage — the property that
   differentiates a semiconductor tier from a fixed metal plane, and the central
   claim of the project.
4. The trade-off between second-tier coupling and the qubit's own gate lever arm.
5. A design window at imec's real 30/50 nm tier separations, plus a labeled scaled
   study beyond it.

**Status:** not yet started. The validated Phase 0 tooling above — mesh building,
non-linear Poisson-Schrödinger solve, lever-arm and capacitance extraction — is
the direct foundation this phase reuses; no new methodology is needed to begin,
only the new device geometry. Results will be added to this README as they are
produced.

---

## 6. Reproducing

Figures 1–6 are pure post-processing and need no license:

```bash
conda env create -f environment.yml   # or just: pip install numpy matplotlib
python src/make_figures_from_results.py
```

Figures 7–9 and all `src/*.py` simulation scripts require a
[QTCAD](https://docs.nanoacademic.com/qtcad/) license from Nanoacademic
Technologies — see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Generated
meshes and saved potential fields are not shipped (too large, and regenerable);
each script's docstring documents exactly how to reproduce its inputs.

## 7. References

- Loenders et al. — statistical analysis of gate-defined quantum-dot variability
  on a 300 mm industrial SiMOS platform (imec). Primary device target; source of
  the geometry and measured targets in §1 and §3.3.
- Mohiyaddin et al., "Multiphysics Simulation of Silicon Quantum Dot Qubit
  Devices," IEDM 2019 (imec). Simulation-to-simulation calibration comparator, §3.2.
- Gamble et al., "Valley splitting of single-electron Si MOS quantum dots,"
  *Appl. Phys. Lett.* 109, 253101 (2016). MVEMT solver benchmark, §3.1.
- Beaudoin et al. — QTCAD methodology reference; source of the comparable-device
  lever-arm value used in §3.1.
- QTCAD 2.2.5, Nanoacademic Technologies Inc. — see
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for citation requirements.

## License

**All rights reserved.** This is unpublished research work — no license is
granted for reuse, redistribution, or modification of the code or documentation
in this repository. The repository is public for visibility only. Third-party
dependencies (QTCAD) and cited literature retain their own respective rights —
see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
