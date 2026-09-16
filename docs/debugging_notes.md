# A debugging story: the missing `set_dot_region()` call

This is worth writing up on its own because every part of it was found by reading
documentation and vendor examples, not by running more simulations — and because
the failure mode (silent, self-consistent, and physically plausible-looking) is the
kind that's easy to miss.

## The symptom

An early full campaign on the imec device geometry produced a single-particle lever
arm of **0.0089 eV/V**. A comparable industrial FD-SOI device, reported in
independent methodology literature (Beaudoin et al.), has a lever arm of **0.26
eV/V** — roughly 30× larger. The Poisson solve converged cleanly in both cases; there
was no error, no warning, nothing in the log to flag a problem.

## Finding the cause

Re-reading QTCAD's own worked examples line by line (rather than re-running
anything) showed that every vendor example placing a quantum dot under the
non-linear Poisson solver calls `d.set_dot_region(region)` before solving. The
device script in this project didn't call it anywhere — confirmed by grep across
every script in the project.

`set_dot_region()` tells the non-linear Poisson solver to zero the classical
(Thomas-Fermi) charge density inside the specified region, so that the electrons
there are described quantum-mechanically instead of as a classical electron gas.
Without it, a classical accumulation layer forms exactly where the quantum dot is
supposed to be and electrostatically screens the plunger gate — which is why the
conduction-band minimum stayed pinned near a fixed value across a wide bias range,
and why the ground-state energy barely moved with gate voltage.

The tool's own methodology reference states this in prose: *"a region of strong
quantum confinement is created ... in which we set the classical electron density
to zero to model electrons quantum-mechanically."* It just hadn't been acted on.

## The fix, and verifying it actually worked

The fix is one line, added before the device object is returned from its
constructor:

```python
d.set_dot_region(QD_REGIONS)
```

Verification was done in a specific order, deliberately not skipping straight to a
full campaign re-run:

1. Re-solve Poisson at a single bias point. The conduction-band minimum should stop
   being pinned — it did, moving from −0.0699 eV to −0.0215 eV at the same bias.
2. Re-solve Schrödinger at two nearby bias points and check the ground-state energy
   moves far more per volt than before. It moved by **25×**: the single-particle
   lever arm went from 0.0112 eV/V to **0.2831 eV/V**, landing within **8.9%** of
   the 0.26 eV/V reference value.
3. Cross-check against a second, independently-computed lever arm (from
   chemical potentials rather than single-particle energies, a genuinely different
   calculation in QTCAD's own API). Pre-fix, the two lever arms differed by 25×,
   which is itself a strong signal something was wrong even before the root cause
   was known. Post-fix, they agree to **2%** — the strongest single piece of
   evidence that the corrected model is physically sound.

## The scope check that avoided overcorrecting

A natural assumption after finding a bug this consequential is that it invalidated
everything computed before the fix. Rather than assume that, the many-body
(chemical-potential) results were directly compared, pre-fix vs. post-fix, at
several bias points — and they matched to 5 significant figures. The reason: a
separate solver flag (`bound_state_charges_only = True`) already excluded the
classical continuum from that particular calculation, so `set_dot_region()` was
redundant there specifically, even though it was essential for the single-particle
path. Declaring a bug's *exact* scope, rather than its plausible worst-case scope,
avoided discarding valid results.

## Two smaller pitfalls found the same way

- An early version of the analysis code computed the "orbital spacing" as
  `E[1] - E[0]`. But the device also calls `set_valley_splitting(v)`, which replaces
  every energy level `E` by `E ± v/2` — so `E[1] - E[0]` is *identically* the valley
  splitting supplied as an input, not a computed quantity, at any bias, in any
  geometry. A suspiciously constant number across otherwise-varying conditions was
  the tell. The real first orbital spacing is `E[2] - E[0]`.
- An addition energy was mislabeled as a charging energy without accounting for the
  valley structure. With valley splitting explicit, `E_add(2) = E_C + Δ_valley` (the
  third electron enters the upper valley partner) — quoting `E_add(2)` directly as
  `E_C` overstates it by exactly the injected valley splitting.

None of these were caught by inspecting output plots or checking convergence — all
three were caught by asking "does this number behave the way the underlying physics
requires," which is a cheaper and more reliable check than it sounds.
