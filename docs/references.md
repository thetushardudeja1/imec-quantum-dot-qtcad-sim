# References

Papers cited throughout the docs and code comments. No PDFs are included in this
repository — copyrighted material is cited, not redistributed.

- Loenders et al., "Statistical analysis of gate-defined quantum dot variability in
  a 300 mm industrial SiMOS platform" (imec) — the primary device target; source of
  the geometry in [device_spec.md](device_spec.md) and the measured targets in
  [validation.md](validation.md).
- Mohiyaddin et al., "Multiphysics Simulation of Silicon Quantum Dot Qubit Devices,"
  IEDM 2019 (imec) — the simulation-to-simulation calibration comparator used in
  [validation.md](validation.md).
- Gamble et al., "Valley splitting of single-electron Si MOS quantum dots," *Appl.
  Phys. Lett.* 109, 253101 (2016) — benchmark for the multivalley effective-mass
  (MVEMT) solver.
- Beaudoin et al. — QTCAD methodology reference; source of the comparable-device
  lever-arm value (0.26 eV/V) used to sanity-check the single-particle lever arm,
  and of the `set_dot_region()` guidance discussed in
  [debugging_notes.md](debugging_notes.md).

## Software

- **QTCAD** 2.2.5, Nanoacademic Technologies Inc. — see
  [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
