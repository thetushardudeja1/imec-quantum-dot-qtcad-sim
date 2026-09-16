"""Corrected geometry (30 / 76 / 30 nm) vs the old derived one (37 / 50 / 50 nm).

Same solver settings, same bias points, so the comparison is clean. The prediction from
the geometry notes below is that ALL THREE changes push the dot bigger:
  plunger  50 -> 76 nm   : should widen the dot in y (old sigma_y = 3.76 nm)
  conf gap 73 -> 80 nm   : should widen it slightly in x (old sigma_x = 5.53 nm)
  barrier  50 -> 30 nm   : less depletion between rows, also widens y

OLD geometry reference, V_P = 2.900 V:
  CBmin -0.0215 eV   E0 +114.471 meV   sigma (5.53, 3.76, 0.71) nm
  size 22.1 x 15.0 nm   area 332 nm^2   dE_orb 10.862 meV
TARGET (Loenders TEM, an OUTPUT not an input): 73 x 50 nm.
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
BIASES = [2.3, 2.6, 2.9, 3.2]

print("=" * 82)
print("CORRECTED GEOMETRY  conf 30 / plunger 76 / barrier 30 nm   (gaps 80 / 80)")
print("old: conf 37 / plunger 50 / barrier 50 -> at 2.9 V gave 22.1 x 15.0 nm, "
      "dE_orb 10.862")
print("=" * 82, flush=True)

rows = []
for vp in BIASES:
    t0 = time.time()
    try:
        d = make_device(MESH, WF, vp, 0.0, 0.0, 0.0, DOPING, SUB_BC)
        pp = PoissonSolverParams(); pp.tol = 1e-6; pp.maxiter = 200
        PoissonSolver(d, solver_params=pp).solve()
        cb = np.asarray(d.cond_band_edge() / ct.e)
        cbmin = float(cb.min())

        d.set_V_from_phi()
        sm = SubMesh(d.mesh, QD_REGIONS)
        qd = SubDevice(d, sm)
        sp = SchParams(); sp.num_states = 6; sp.tol = 1e-8
        SchSolver(qd, solver_params=sp).solve()
        E = np.asarray(qd.energies) / ct.e * 1e3

        pr = np.abs(np.asarray(qd.eigenfunctions)[:, 0]) ** 2
        if pr.ndim > 1:
            pr = pr.sum(axis=tuple(range(1, pr.ndim)))
        X = np.asarray(sm.glob_nodes)
        N = float(an.integrate(sm, pr))
        cen = np.array([float(an.integrate(sm, pr * X[:, k])) / N for k in range(3)])
        sig = np.array([np.sqrt(float(an.integrate(sm, pr * (X[:, k] - cen[k]) ** 2)) / N)
                        for k in range(3)]) * 1e9
        size = 4.0 * sig
        dE = E[2] - E[0]
        print(f"  V_P={vp:4.2f}  CBmin={cbmin:+8.4f}  E0={E[0]:+9.3f} meV  "
              f"sigma=({sig[0]:5.2f},{sig[1]:5.2f},{sig[2]:4.2f})  "
              f"size {size[0]:5.1f} x {size[1]:5.1f} nm  area {size[0]*size[1]:6.0f}  "
              f"dE_orb {dE:6.3f}   ({time.time()-t0:.0f}s)", flush=True)
        rows.append((vp, cbmin, E[0], sig[0], sig[1], sig[2],
                     size[0], size[1], size[0] * size[1], dE))
    except Exception:
        import traceback
        print(f"  V_P={vp:4.2f} FAILED\n" + traceback.format_exc(), flush=True)

if rows:
    out = ROOT / "check_new_geometry_results.txt"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("vp\tcbmin_eV\tE0_meV\tsig_x\tsig_y\tsig_z\tsize_x\tsize_y\t"
                 "area_nm2\tdE_orb_meV\n")
        for r in rows:
            fh.write("\t".join(f"{v:.4f}" for v in r) + "\n")
    print(f"\nwrote {out}")
    a = np.array([r for r in rows])
    # first-electron voltage: where E0 crosses E_F = 0
    if (a[:, 2] > 0).any() and (a[:, 2] < 0).any():
        c = np.polyfit(a[:, 0], a[:, 2], 1)
        print(f"E0 crosses E_F at V_P = {-c[1]/c[0]:.3f} V   "
              f"(old geometry: 3.292 V)")
    print("\nCOMPARE at V_P = 2.9:  old 22.1 x 15.0 nm, area 332, dE_orb 10.862")
    print("TARGET (Loenders TEM):  73 x 50 nm")
