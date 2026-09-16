# Device specification: imec 7×7 SiMOS quantum-dot array

This is the published device the simulation targets. Every number below has a
source; nothing here is inferred or fitted. Primary source: Loenders et al. (imec),
industrial 300 mm quantum-dot variability study (see [references.md](references.md)).

## 1. Architecture

- **7 × 7 array = 49 quantum dots**, dot-to-dot pitch **110 nm**.
- 300 mm SiMOS, **EUV** lithography, enriched **Si-28** substrate.
- **Overlapping-gate architecture**, three highly doped polysilicon gate layers,
  deposited and patterned sequentially, separated by SiO₂:

| layer | gates | role |
|---|---|---|
| GL1 | C1…C8 | confinement gates — form the columns |
| GL2 | P1…P7 | plungers — each controls a row of 7 dots |
| GL2 | D, S1…S7 | accumulation gates — bring the 2DEG from drain/source implants |
| GL3 | B1…B8 | barrier gates — separate the rows |

- Measurement pattern: dots form under Px, with Bx/Bx+1 acting as source/drain
  barriers — seven confinement-gate columns give seven-fold parallel readout.

## 2. Oxides

- GL1 oxide is thermally grown; GL2/GL3 oxides are high-temperature CVD (780 °C) —
  different quality, relevant to defect density.
- Each gate layer sits on a different net oxide thickness (t1, t2, t3); post-etch
  over-etch means effective thickness is below nominal.
- From HAADF-STEM: δ2 = t2 − t1 ≈ 4.6 nm, δ3 = t3 − t2 ≈ 0.8 nm, taken as constant
  across all samples.

| sample | wafer | t1 (nm) | t2 (nm) | t3 (nm) |
|---|---|---|---|---|
| A, B | 1 | 8.0 | 13.0 | 18.0 |
| C, D | 2 | 12.0 | 17.0 | 22.0 |
| E, F | 3 | 15.0 | 20.0 | 25.0 |
| G, H | 4 | 20.0 | 25.0 | 30.0 |

392 dots total, 98 per oxide-thickness condition.

## 3. Measurement conditions

- Kiutra ADR fridge, sample temperature 200 mK.
- Electron temperature extracted from Coulomb-peak lineshape
  (`G = G_max cosh⁻²(ΔE / 2 k_B T)`): T < 3 K, quoted as 1.4 ± 0.06 K.
- Statistics from the central 5×5 sub-array (outer rows/columns excluded — they
  have asymmetric neighbouring gates and imec explicitly excludes them from their
  own statistics).

## 4. Single-dot validation targets

```
charging energy       E_C  ~ 4 meV        [quoted as "~", order-of-magnitude]
level splitting        ΔE  ~ 0.7 meV       [paper says "level splitting", not
                                            necessarily orbital — ambiguous]
plunger capacitance    C_P = 6.61 aF       [parallel-plate fit to measured Coulomb
                       (sample E, t2=19.5)  diamonds: A=3733 nm², δ2=4.5 nm are the
                                            paper's own FITTED values, 3% spread]
total dot capacitance  C_Σ = e/E_C ~ 40 aF  [26% spread — dominated by S/D coupling]
lever arm              α = C_P/C_Σ ~ 0.165
dot size               3733 nm² fitted, ~50 × 70 nm elongated
dot pitch              110 nm
```

**Provenance grades:** `C_P`, the dot area, and δ2 are the hardest numbers here —
fitted to 392 dots with a 3% spread. `E_C` and `ΔE` are quoted with a "~" in a
thermometry-focused appendix, so treat them as order-of-magnitude only. `C_Σ` and
`α` are derived from `E_C` and `C_P`, not quoted directly by the paper.

**Not stated in the paper** (must be assumed and declared in any simulation):
polysilicon gate doping/work function, substrate doping, interface trap density,
individual gate widths/lengths (only the dot footprint and pitch are published).

See [validation.md](validation.md) for how this project's simulated quantities
compare against these targets — and against imec's own simulation literature.
