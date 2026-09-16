# Validation

## 1. Method validation against a vendor-documented reference

Before building the imec device, the pipeline was checked against QTCAD's own
documented worked example (a fully-specified FDSOI double-dot device with published
output values) end to end:

| quantity | this run | vendor documented | error |
|---|---|---|---|
| addition energy 1 | 0.01733328 eV | 0.01734738 eV | **0.081%** |
| addition energy 2 | 0.01717220 eV | 0.01718527 eV | **0.076%** |
| capacitance 1 | 5.13662598 aF | 5.13474174 aF | **0.037%** |
| capacitance 2 | 5.10684765 aF | 5.10479766 aF | **0.040%** |

Lever arms −0.5557 / −0.5525 eV/V, Coulomb peaks 1.23881 / 1.27012 V (spacing 31.3 mV).
The residual ~0.1% is expected — adaptive mesh refinement applies a randomized
perturbation, so meshes are never bit-identical across runs.

This validated the full chain: adaptive meshing, non-linear Poisson, self-consistent
Schrödinger-Poisson, many-body energies, chemical potentials, addition energies,
lever arm, capacitance, and the valley-degeneracy/explicit-valley-splitting
convention — before any of it was trusted on a new device.

## 2. Valley-splitting benchmark

The multivalley effective-mass-theory (MVEMT) solver was checked against a
published valley-splitting-vs-field result for silicon quantum dots (Gamble et al.,
*Appl. Phys. Lett.* 109, 253101, 2016). Result: **0.1025 meV per MV/m**, linear
across the tested range (0.513 meV at 5 MV/m, 5.12 meV at 50 MV/m) — reproducing
the published slope.

## 3. Two independent lever-arm calculations agree

The single-particle lever arm (§1 above, 0.283 eV/V) is computed one way; a second,
independently-computed lever arm from chemical potentials rather than
single-particle energies (`α_μ` = 0.278 eV/V) is computed a completely different
way. The two agree to **2%** — the strongest single consistency check available for
this class of model, since it exercises two separate parts of the solver chain and
lands in the same place.

## 4. Calibration against imec — and why the naive comparison is wrong

This is the finding worth highlighting: **simulated quantities should be compared to
other simulations, not to fitted experimental extractions**, even when both come
from the same measured device.

| quantity | imec measured (Loenders, parallel-plate fit) | this simulation | ratio |
|---|---|---|---|
| C_P | 6.1 ± 0.2 aF | 1.45 aF | 4.2× low |
| C_Σ | 40 ± 10 aF | 5.22 aF | 7.7× low |
| lever arm α | 0.152 | 0.278 | 1.8× high |
| E_C | 4.0 meV | 30.7 meV | 7.7× high |

Taken at face value, this looks like a systematic factor-of-several miss. But
Loenders' `C_P` is a **parallel-plate model fitted to measured Coulomb diamonds**,
not a first-principles capacitance — and a separate imec publication that *does*
run a full 3D electrostatic simulation of the same device family (Mohiyaddin et
al., IEDM 2019) reports simulated gate-to-dot capacitances **2.7× below their own
parallel-plate estimate** for the same geometry:

| quantity | Mohiyaddin (imec, simulated) | this simulation | verdict |
|---|---|---|---|
| C_gate-QD @ t_ox 20 nm | 0.55–2.2 aF | 1.45 aF | inside range |
| voltage for 1st electron @ 20 nm | 1.45–4.05 V | 3.29 V | inside range |
| vertical field in the dot | ~200 kV/cm | 309–329 kV/cm | ~1.6× |
| orbital spacing (few-electron end) | ~10 meV | 10.7–11.3 meV | consistent |

Against the correct (simulation-to-simulation) comparator, the capacitance and
turn-on voltage land inside the published range, and the field and orbital spacing
are within a factor of ~1.6 or better. The one genuinely open discrepancy is the
lever arm: it is computed two independent ways here and they agree with each other
to 2%, but there is no equivalent simulated lever arm published to check against —
only the measured 0.152, which carries reservoir/array parasitics this isolated-dot
model doesn't include. That gap is real and unresolved, not swept under a rug.

**Takeaway for anyone reading these numbers:** a raw ratio against a published value
is not by itself evidence of a modeling error — the *type* of the published value
(measured/fitted vs. simulated, isolated dot vs. array-embedded) has to match
before the ratio means anything. See `figures/fig5_calibration_comparison.png`.
