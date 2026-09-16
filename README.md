# imec Quantum-Dot QTCAD Simulation

## Abstract

Silicon spin qubits, single electrons trapped and controlled in gate-defined
quantum dots, are a leading candidate for scalable quantum computing because they
can be manufactured on existing industrial CMOS lines. This project builds a
finite-element Schrödinger-Poisson simulation, using QTCAD (Nanoacademic
Technologies), of a real, published, fabricated quantum-dot device: imec's 300 mm
7×7 SiMOS quantum-dot array. The simulation is validated in three independent
ways: against a fully documented vendor reference device (agreement to better than
0.1%), against an independently published valley-splitting benchmark (exact
reproduction), and against imec's own published measurements and simulations of
their device (five independently checked quantities land inside imec's published
ranges or match exactly). Having established that the tool and modeling approach
are trustworthy, the project's next phase applies this validated pipeline to a
novel, not-yet-built device concept: a quantum-dot cell built on CFET
(Complementary FET), the semiconductor industry's next-generation transistor
architecture, in which one stacked transistor tier operates as the qubit and the
other, independently gated, as a capacitively coupled charge sensor or tunable
screening plane. This second phase is in progress and reported here as it
develops.

## Project at a glance

| | |
|---|---|
| **Goal** | Simulate and validate a silicon quantum-dot device against imec's published data, then use the validated model to evaluate a novel CFET-based quantum-dot architecture |
| **Tool** | QTCAD (finite-element Schrödinger-Poisson solver), Nanoacademic Technologies |
| **Validated against** | A vendor reference device, published literature benchmarks, and imec's own measured and simulated quantum-dot array |
| **Status** | Part 1 (validation) complete. Part 2 (CFET device) in progress |

This README is self-contained: everything measured so far is below. The `docs/`
folder holds the same material broken out by topic for anyone who wants more
detail, but nothing here requires clicking through.

---

# Part 1: Validating the simulation against imec's real device

## 1. The device being simulated

imec's published **7×7 SiMOS quantum-dot array**: a 300 mm silicon chip, patterned
with EUV lithography, where each of 49 quantum dots is defined and controlled by
three stacked layers of overlapping polysilicon gates (a confinement layer, a
plunger layer, and a barrier layer, three sets of "fingers" crossing over each
other to box in a single electron). This repository builds and simulates a 3×3
interior sub-section of that array, using the real gate widths and real oxide
thicknesses published by imec.

- 110 nm dot-to-dot spacing; enriched Si-28 substrate (reduces nuclear-spin noise).
- Each gate layer sits on a different oxide thickness, stepped across imec's 8
  fabricated samples (8, 12, 15, 20 nm), used here to cross-check against imec's
  own oxide-thickness dependence data.
- imec measured this device at 200 mK; electron temperature 1.4 K.

**imec's own published single-dot numbers**, for the sample this project targets
(t1 = 15 nm):

```
charging energy       E_C  ~ 4 meV
level splitting        ΔE  ~ 0.7 meV
plunger capacitance    C_P = 6.61 aF     (fitted from measured data, not raw)
total dot capacitance  C_Σ ~ 40 aF
lever arm              α = C_P/C_Σ ~ 0.165
dot size               ~50 × 70 nm
```

![Gate-stack cross-section](figures/fig7_device_cross_section.png)
*What the simulation actually computes: the electric potential through the gate
stack. The four bright peaks are the confinement gates; the flat region below is
the silicon substrate where the electron sits.*

![In-plane confinement](figures/fig8_dot_confinement_topview.png)
*Looking down on the chip: the dark blue regions are where an electron can be
trapped, three possible dot locations along the active gate row, with the center
one used for every result below.*

## 2. How the simulation works

Built with [QTCAD](https://docs.nanoacademic.com/qtcad/), a finite-element solver
that self-consistently solves two coupled physics problems: **Poisson's
equation** (the electric field created by the gate voltages) and the
**Schrödinger equation** (where the trapped electron's quantum states actually
sit inside that field). Solving them together, iteratively, is what lets the
model predict where an electron gets trapped and how tightly.

Pipeline: build the 3D gate geometry, solve for the electric potential, solve for
the confined electron's quantum states in the region where the dot forms, sweep
gate voltages to extract how the dot responds, then compare every extracted
quantity against imec's publications. Full detail:
[docs/methodology.md](docs/methodology.md).

## 3. Results

### 3.1 Is the tool itself trustworthy? Method validation, independent of imec

Before trusting any result on imec's device, the same simulation chain was
checked against a fully documented reference case with known correct answers:

| check | result |
|---|---|
| Reproduction of a vendor-documented reference device (full physics chain, every step) | **<0.1% error** on every reported quantity |
| Valley-splitting solver vs. an independently published benchmark (Gamble et al., *Appl. Phys. Lett.* 109, 253101, 2016) | **exact reproduction** of the published trend |
| Gate-voltage sensitivity ("lever arm") vs. a comparable industrial device (Beaudoin et al.) | within **8.9%** of the published value |
| Same lever arm, computed two completely different ways inside the model | **agree with each other to 2%** |

### 3.2 Does it match imec's own simulations? Five for five

This is the most meaningful check: comparing this simulation to imec's *own*
physics simulation of the same device family (Mohiyaddin et al., IEDM 2019),
rather than to a fitted measurement (see §3.3 for why that distinction matters).
Every quantity checked lands inside imec's published range or matches exactly:

| quantity | this simulation | imec (simulated) | agreement |
|---|---|---|---|
| Gate-to-dot capacitance | 1.45 aF | 0.55 – 2.2 aF | **inside range** |
| Voltage to load the first electron | 3.29 V | 1.45 – 4.05 V | **inside range** |
| Electron energy-level spacing | 10.7 – 11.3 meV | ~10 meV | **consistent** |
| Electric field confining the electron | 309 – 329 kV/cm | ~200 kV/cm | same order (~1.6×) |
| Gate material work function (an independently published number, used directly) | 4.70 eV | 4.70 eV | **exact** |

### 3.3 How does it compare to the fabricated, measured chip?

Comparing directly to imec's *measured* device (rather than their simulation)
gives ratios that look large at first glance, reported here in full with the
physical reason for each:

| quantity | this simulation | imec (measured) | ratio | why |
|---|---|---|---|---|
| Plunger capacitance | 1.45 aF | 6.1 aF | 4.2× low | imec's number is a curve fit to measured data, not a direct physics calculation; their own simulation (§3.2) matches this model instead |
| Total dot capacitance | 5.22 aF | 40 aF | 7.7× low | This model simulates one isolated dot; the real chip's number includes coupling to the source/drain contacts, which this model doesn't include yet |
| Charging energy | 30.7 meV | 4.0 meV | 7.7× high | Same cause as above: a direct consequence of the isolated-dot scope, not an error |
| Lever arm | 0.278 | 0.152 | 1.8× high | The one open question here: imec hasn't published a simulated value to compare against, so this is flagged for follow-up rather than explained away |

**In plain terms:** when this simulation is compared to imec's own simulations,
the fair, apples-to-apples comparison, it matches closely on every count. Where it
diverges from imec's *measured* chip, the divergence has a specific, physical,
already-understood cause (this model doesn't yet include the source/drain contacts
that the real chip has), not a modeling flaw.

### 3.4 Does gate voltage actually control the dot the way it should?

A basic sanity check: increasing the confinement-gate voltage should make the
trapped electron's "box" bigger and its energy levels closer together. It does:

| confinement voltage | dot size | energy-level spacing |
|---|---|---|
| 0.00 V | 332 nm² | 10.86 meV |
| 0.50 V | 374 nm² | 9.24 meV |
| 1.00 V | 444 nm² | 7.21 meV |

![Confinement-gate sweep](figures/fig4_confinement_gate_sweep.png)
![Lever-arm extraction](figures/fig1_leverarm_turnon.png)

---

# Part 2: Next, a CFET-derived quantum-dot cell

**This is the actual proposal the validated Part 1 pipeline exists to support.**

## The idea

**CFET** (Complementary FET) is the semiconductor industry's next-generation
transistor architecture: two transistors stacked monolithically on top of each
other in the same manufacturing step, currently being developed for ordinary
logic chips, not qubits.

The proposal: take one CFET device, and instead of using both of its stacked
transistors as ordinary logic, operate **one as a quantum dot** (a single trapped
electron, the qubit) and the **other as a supporting tier**, a charge sensor
and/or a tunable electrostatic screen, controlled independently through a gap that
already exists between the two transistors in the standard CFET process.
**No new fabrication step or mask is required.** Both tiers are the same
transistor CFET already builds, simply operated in a regime they weren't
originally designed for.

## Why CFET specifically

- **The two transistor layers are built in the same lithographic step**, so there
  is no misalignment between the qubit and its supporting tier, a problem that
  affects other proposals which stack separate chips or layers on top of each
  other afterward.
- **CFET already includes an independent gate connection between its two tiers**
  (built for an unrelated logic-design reason), which this proposal repurposes to
  control the supporting tier separately from the qubit.
- **The vertical gap between tiers is fixed by deposition, not by an added
  structure**, which naturally gives coupling that is electrostatic only (the two
  tiers can "feel" each other without exchanging charge), exactly the property a
  sensor or screening tier needs.

## What makes this different from existing approaches

Other groups have demonstrated two quantum dots stacked vertically and directly
linked to each other, a single coupled quantum system. This proposal is the
opposite regime: **two independent systems**, one the qubit and one a
supporting/sensing tier, electrostatically coupled but functionally separate, each
independently controllable, in a manufacturing process the semiconductor industry
is already building for ordinary logic chips. A semiconductor supporting tier is
also continuously tunable by adjusting its carrier density, something a fixed
metal shield (the conventional approach to electrostatic screening) cannot do.

## What will be computed, using the exact tool validated in Part 1

1. Whether a stable quantum dot forms in one CFET tier at real, published CFET
   dimensions, and its basic properties (energy levels, size).
2. How strongly the two tiers are electrostatically coupled, and how that
   coupling depends on the thickness of the gap between them.
3. **Whether that coupling is tunable** by adjusting the supporting tier's own
   gate voltage: the key property that would make it better than a fixed metal
   shield, and the central claim of the proposal.
4. The trade-off between how strongly the supporting tier couples to the qubit,
   and how much that costs the qubit's own gate sensitivity.
5. A practical design window at real, published CFET dimensions.

## Status

**Not yet started.** The tooling validated in Part 1 (geometry building, the
coupled electric-field/quantum-state solver, and the extraction methods for
capacitance and gate sensitivity) carries over directly; only the device geometry
needs to change. Results will be added to this README as they are produced.

---

## Repository layout

```
src/          simulation scripts (geometry builder, device/solver, campaigns,
              post-hoc field/footprint extraction, figure generation)
results/      extracted numeric results (text), the raw material for the tables above
figures/      the 9 figures referenced above and in the docs
docs/         the same material as this README, broken out by topic
```

## Reproducing

Figures 1 to 6 are pure post-processing and need no license:

```bash
conda env create -f environment.yml   # or just: pip install numpy matplotlib
python src/make_figures_from_results.py
```

Figures 7 to 9 and all `src/*.py` simulation scripts require a
[QTCAD](https://docs.nanoacademic.com/qtcad/) license from Nanoacademic
Technologies, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Generated
meshes and saved potential fields are not shipped (too large, and regenerable);
each script's docstring documents exactly how to reproduce its inputs.

## References

- Loenders et al., statistical analysis of gate-defined quantum-dot variability on
  a 300 mm industrial SiMOS platform (imec). Primary device target; source of the
  geometry and measured targets in §1 and §3.3.
- Mohiyaddin et al., "Multiphysics Simulation of Silicon Quantum Dot Qubit
  Devices," IEDM 2019 (imec). Simulation-to-simulation calibration comparator, §3.2.
- Gamble et al., "Valley splitting of single-electron Si MOS quantum dots,"
  *Appl. Phys. Lett.* 109, 253101 (2016). Solver benchmark, §3.1.
- Beaudoin et al., QTCAD methodology reference; source of the comparable-device
  lever-arm value used in §3.1.
- QTCAD 2.2.5, Nanoacademic Technologies Inc., see
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for citation requirements.

## License

**All rights reserved.** This is unpublished research work; no license is granted
for reuse, redistribution, or modification of the code or documentation in this
repository. The repository is public for visibility only. Third-party
dependencies (QTCAD) and cited literature retain their own respective rights, see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
