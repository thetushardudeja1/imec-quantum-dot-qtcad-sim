"""Does biasing the confinement/barrier gates close the footprint and orbital-spacing
gaps? Every run before 2026-09-13 used vc = vb = vpn = 0, i.e. an UNTUNED device.

This is not parameter fitting. Gate bias is an OPERATING POINT, not geometry --
imec tune these gates on every device (that is what their operating window is).
Standing rule 3 forbids tuning geometry; it does not forbid operating the device.

Targets:  footprint 50 x 70 nm / 3733 nm^2   [Loenders]
          s-p orbital separation "a few meV" [Mohiyaddin]
Baseline (vc = vb = 0): 22.2 x 15.1 nm, 336 nm^2, dE_orb = 10.86 meV at V_P = 2.9.

Watch for: the dot growing into the QD submesh walls. The box is 110 x 90 nm, so a
50 x 70 nm dot (+-2 sigma = +-25 x +-35 nm) still fits, but only just in y. sigma is
printed so the clipping can be seen coming.
"""

import pathlib
import sys
import time

import numpy as np

HERE = pathlib.Path(__file__).parent.resolve()
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from imec_qd_3x3_device import QD_REGIONS, make_device  # noqa: E402
from qtcad.device import SubDevice  # noqa: E402
from qtcad.device import analysis as an  # noqa: E402
from qtcad.device import constants as ct  # noqa: E402
from qtcad.device.mesh3d import SubMesh  # noqa: E402
from qtcad.device.poisson import Solver as PoissonSolver  # noqa: E402
from qtcad.device.poisson import SolverParams as PoissonSolverParams  # noqa: E402
from qtcad.device.schrodinger import Solver as SchSolver  # noqa: E402
from qtcad.device.schrodinger import SolverParams as SchParams  # noqa: E402

WF, DOPING, SUB_BC = 4.70, 1e16, "ohmic"
MESH = ROOT / "meshes" / "imec_qd_3x3_t1_15nm.msh"
VP = 2.9
SWEEP = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]

OUT = ROOT / "sweep_confinement_results.txt"
print("=" * 80)
print(f"CONFINEMENT SWEEP   V_C = V_B = {SWEEP}   at V_P = {VP} V")
print("target footprint 50 x 70 nm (3733 nm^2); baseline at 0 V is 22.2 x 15.1 (336)")
print("=" * 80, flush=True)

rows = []
for vcb in SWEEP:
    t0 = time.time()
    try:
        d = make_device(MESH, WF, VP, 0.0, vcb, vcb, DOPING, SUB_BC)
        pp = PoissonSolverParams()
        pp.tol = 1e-6
        pp.maxiter = 200
        PoissonSolver(d, solver_params=pp).solve()

        cb = np.asarray(d.cond_band_edge() / ct.e)
        cbmin = float(cb.min())

        d.set_V_from_phi()
        sm = SubMesh(d.mesh, QD_REGIONS)
        qd = SubDevice(d, sm)
        sp = SchParams()
        sp.num_states = 4
        sp.tol = 1e-8
        SchSolver(qd, solver_params=sp).solve()
        E = np.asarray(qd.energies) / ct.e * 1e3

        psi = np.asarray(qd.eigenfunctions)[:, 0]
        p = np.abs(psi) ** 2
        if p.ndim > 1:
            p = p.sum(axis=tuple(range(1, p.ndim)))
        X = np.asarray(sm.glob_nodes)
        N = float(an.integrate(sm, p))
        pos = np.array([float(an.integrate(sm, p * X[:, k])) / N for k in range(3)])
        std = np.array([np.sqrt(float(an.integrate(sm, p * (X[:, k] - pos[k]) ** 2)) / N)
                        for k in range(3)]) * 1e9
        size = 4.0 * std
        area = size[0] * size[1]
        dE = E[2] - E[0]

        # is the wavefunction still contained? fraction of |psi|^2 outside +-2 sigma
        # of the box centre in y, the tight direction
        print(f"  V_C=V_B={vcb:4.2f}  CBmin={cbmin:+7.4f}  E0={E[0]:+9.3f} meV  "
              f"size {size[0]:5.1f} x {size[1]:5.1f} nm  area {area:6.0f} nm^2  "
              f"dE_orb {dE:6.3f} meV   ({time.time() - t0:.0f}s)", flush=True)
        rows.append((vcb, cbmin, E[0], std[0], std[1], std[2], size[0], size[1],
                     area, dE))
    except Exception:
        import traceback
        print(f"  V_C=V_B={vcb:4.2f} FAILED\n" + traceback.format_exc(), flush=True)

if rows:
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("vcb\tcbmin_eV\tE0_meV\tsig_x\tsig_y\tsig_z\tsize_x\tsize_y\t"
                 "area_nm2\tdE_orb_meV\n")
        for r in rows:
            fh.write("\t".join(f"{v:.4f}" for v in r) + "\n")
    print(f"\nwrote {OUT}")
    a0, d0 = rows[0][8], rows[0][9]
    aN, dN = rows[-1][8], rows[-1][9]
    print(f"area  {a0:.0f} -> {aN:.0f} nm^2  (target 3733)   x{aN / a0:.2f}")
    print(f"dE    {d0:.2f} -> {dN:.2f} meV  (target 'a few')  x{dN / d0:.2f}")
