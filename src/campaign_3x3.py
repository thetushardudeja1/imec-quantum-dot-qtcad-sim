"""Detached overnight campaign on the imec 3x3 INTERIOR cell.

Runs unattended. Everything is appended to ../campaign_3x3.log with timestamps and to
../campaign_3x3_results.txt as machine-readable rows. One failure never kills the run.

Context: CB minimum falls ~0.316 eV per volt of plunger; at V_P = 2.8 it was +0.0101 eV,
so accumulation is just above 2.8 V.

STAGES
  1  plunger sweep (Poisson only, ~75 s each) -> find accumulation, then the
     first few volts beyond it
  2  Schrodinger at each accumulated bias -> spectrum, E1-E0
 2b  single-particle lever arm via the vendor leverarm.Solver  [ACCEPT 0.1-0.5 eV/V]
  3  many-body at the best bias -> chemical-potential lever arm, E_C, and C_P
  4  repeat stage 1-2 for the other three published oxide thicknesses (8/12/20 nm),
     with every parameter frozen -- a PREDICTION, not a fit

Published parameters, not fitted: wf 4.70 eV [Mohiyaddin], substrate 1e16 [Beaudoin],
T = 1.4 K electron temperature [Loenders App.].
"""

import datetime
import pathlib
import sys
import time
import traceback

import numpy as np

HERE = pathlib.Path(__file__).parent.resolve()
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

LOG = ROOT / "campaign_3x3.log"
RES = ROOT / "campaign_3x3_results.txt"


def log(msg=""):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}" if msg else ""
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()


def res(row):
    with open(RES, "a", encoding="utf-8") as f:
        f.write(row + "\n")
        f.flush()


log("#" * 72)
log("CAMPAIGN START, imec 3x3 interior cell")
log("#" * 72)

try:
    from imec_qd_3x3_device import (CENTRAL_PLUNGER, QD_REGIONS,  # noqa: E402
                                    VALLEY_SPLITTING, make_device)
    from qtcad.device.leverarm import Solver as LeverArmSolver  # noqa: E402
    from qtcad.device.leverarm import SolverParams as LeverArmParams  # noqa: E402
    from qtcad.device import SubDevice  # noqa: E402
    from qtcad.device import constants as ct  # noqa: E402
    from qtcad.device import materials as mt  # noqa: E402
    from qtcad.device.mesh3d import SubMesh  # noqa: E402
    from qtcad.device.poisson import Solver as PoissonSolver  # noqa: E402
    from qtcad.device.poisson import SolverParams as PoissonSolverParams  # noqa: E402
    from qtcad.device.schrodinger import Solver as SchSolver  # noqa: E402
    from qtcad.device.schrodinger import SolverParams as SchParams  # noqa: E402
    from qtcad.device.schrodinger_poisson import Solver as SPSolver  # noqa: E402
    from qtcad.device.schrodinger_poisson import SolverParams as SPParams  # noqa: E402
except Exception:
    log("IMPORT FAILED:\n" + traceback.format_exc())
    raise

WF, DOPING, SUB_BC = 4.70, 1e16, "ohmic"


def mesh_for(t1):
    return ROOT / "meshes" / f"imec_qd_3x3_t1_{t1:g}nm.msh"


def poisson(t1, vp, vc=0.0, vb=0.0, vpn=0.0, tol=1e-6):
    d = make_device(mesh_for(t1), WF, vp, vpn, vc, vb, DOPING, SUB_BC)
    p = PoissonSolverParams()
    p.tol = tol
    p.maxiter = 200
    PoissonSolver(d, solver_params=p).solve()
    return d, p


def spectrum(d, n=8):
    d.set_V_from_phi()
    qd = SubDevice(d, SubMesh(d.mesh, QD_REGIONS))
    s = SchParams()
    s.num_states = n
    s.tol = 1e-8
    SchSolver(qd, solver_params=s).solve()
    return qd, np.asarray(qd.energies) / ct.e * 1e3


# ---------------------------------------------------------------- STAGE 1 + 2
log("=== STAGE 1/2: plunger sweep + spectrum (t1 = 15 nm) ===")
accumulated = []
for vp in [2.85, 2.9, 3.0, 3.1, 3.2, 3.4, 3.6]:
    t0 = time.time()
    try:
        d, pp = poisson(15.0, vp)
        cb = d.cond_band_edge() / ct.e
        cbmin = float(cb.min())
        line = f"  vp={vp:<5g} CBmin={cbmin:+8.4f} eV"
        if cbmin < 0:
            qd, E = spectrum(d)
            # E[1]-E[0] is the injected valley splitting, not a result -- assert
            # it as a wiring check and report the orbital spacing E[2]-E[0].
            dv = E[1] - E[0]
            assert abs(dv - VALLEY_SPLITTING * 1e3) < 1e-6, \
                f"valley convention broken: E1-E0={dv} meV"
            dE_orb = E[2] - E[0]
            line += (f"  ACCUMULATED  E0={E[0]:+9.3f}  dE_orb={dE_orb:6.3f} meV"
                     f"  [{', '.join('%.2f' % x for x in E[:5])}]")
            accumulated.append(vp)
            res(f"S12\tt1=15\tvp={vp}\tcbmin={cbmin:.6f}\tE0={E[0]:.4f}"
                f"\tdE_orb={dE_orb:.4f}")
        else:
            line += "  empty"
            res(f"S12\tt1=15\tvp={vp}\tcbmin={cbmin:.6f}")
        log(line + f"   ({time.time() - t0:.0f}s)")
    except Exception:
        log(f"  vp={vp:g} FAILED\n" + traceback.format_exc())

# ------------------------------------------------------------------ STAGE 2b
# Measure the SINGLE-PARTICLE lever arm with the vendor's own solver
# (template: GaAs_gated/4-lever_arm.py). ACCEPTANCE: |alpha_sp| in 0.1-0.5 eV/V
# (Beaudoin report 0.26 eV/V on a comparable device, single-particle definition).
if accumulated:
    log("")
    log("=== STAGE 2b: single-particle lever arm (vendor leverarm.Solver) ===")
    log("    ACCEPTANCE: |alpha_sp| in 0.1-0.5 eV/V   [Beaudoin: 0.26 eV/V]")
    try:
        t0 = time.time()
        vlo = min(accumulated)
        V_la = np.linspace(vlo, vlo + 0.20, 5)
        d_la = make_device(mesh_for(15.0), WF, vlo, 0.0, 0.0, 0.0, DOPING, SUB_BC)
        p_la = PoissonSolverParams()
        p_la.tol = 1e-6
        p_la.maxiter = 200
        la = LeverArmSolver(
            d_la, CENTRAL_PLUNGER, V_la, dot_region=QD_REGIONS,
            solver_params=LeverArmParams({"pot_solver_params": p_la}),
            out_path=str(ROOT / "data_leverarm"),
        )
        coeffs = la.solve()                       # slope is -e*alpha, in J/V
        alpha_sp = float(abs(coeffs[0]) / ct.e)
        E_la = np.asarray(la.energies) / ct.e * 1e3
        log(f"    alpha_sp = {alpha_sp:.4f} eV/V   over V_P = "
            f"{V_la[0]:.2f}..{V_la[-1]:.2f} V   ({time.time() - t0:.0f}s)")
        log(f"    E0 across the sweep (meV): "
            f"{', '.join('%.3f' % x for x in E_la[:, 0])}")
        verdict = "PASS" if 0.1 <= alpha_sp <= 0.5 else "*** OUT OF EXPECTED RANGE ***"
        log(f"    {verdict}")
        res(f"S2b\tt1=15\talpha_sp={alpha_sp:.4f}\tverdict={verdict.split()[0]}")
    except Exception:
        log("  STAGE 2b FAILED\n" + traceback.format_exc())

# ------------------------------------------------------------------- STAGE 3
if accumulated:
    vp_best = accumulated[min(1, len(accumulated) - 1)]   # just past turn-on
    log("")
    log(f"=== STAGE 3: many-body at vp={vp_best:g} -> lever arm, E_C, C_P ===")
    log("    C_P compared against imec's simulated C_gate-QD (Mohiyaddin IEDM 2019),")
    log("    not the parallel-plate-fitted measurement -- see docs/validation.md")
    try:
        d, pp = poisson(15.0, vp_best, tol=1e-8)
        d.set_V_from_phi()
        qd = SubDevice(d, SubMesh(d.mesh, QD_REGIONS))

        sp = SPParams()
        sp.tol = 1e-5
        sp.maxiter = 2000
        sp.bound_state_charges_only = True
        sp.sc_method = "underrelax"
        sp.initialization = False
        sp.mixing_algo = "adaptive_linear"
        sp.mixing_param = 0.4          # 0.1 is tuned for N~12; far too slow at N=1-3
        sch = SchParams()
        sch.tol = 1e-8
        sch.num_states = 12
        sp.poisson_solver_params = pp
        sp.schrod_solver_params = sch

        g = int(mt.Si.gqc / 2)         # valley factor removed; splitting set explicitly
        dvp = 0.05
        mus = {}
        for vv in (vp_best, vp_best + dvp):
            d.set_applied_potential(CENTRAL_PLUNGER, vv)
            mb = []
            for n in (1, 2, 3):
                t0 = time.time()
                SPSolver(d, subdevice=qd, solver_params=sp).solve(N=n, g=g)
                e = float(np.sum(g * qd.population_factors * qd.energies))
                mb.append(e)
                log(f"    vp={vv:.3f} N={n}  E_mb={e / ct.e * 1e3:11.4f} meV"
                    f"   ({time.time() - t0:.0f}s)")
            # E_mb(0) = 0, so mu(1) = E_mb(1). Keeping mu(1) lets us form E_add(1),
            # where the 2nd electron is the SPIN PARTNER in the same valley-resolved
            # orbital => dE = 0 => E_add(1) IS E_C, no correction needed.
            mus[vv] = [mb[0] / ct.e,
                       (mb[1] - mb[0]) / ct.e,
                       (mb[2] - mb[1]) / ct.e]          # mu(1), mu(2), mu(3), in V

        mu0 = np.array(mus[vp_best])
        mu1 = np.array(mus[vp_best + dvp])
        alphas = (mu1 - mu0) / dvp                      # eV/V per transition
        alpha_mu = float(alphas[1])                     # the mu(2) transition

        # An addition energy is NOT a charging energy: E_add(N) = E_C + dE(N)
        # (vendor reference: practical_application/FDSOI/3-coulomb_peaks sec.5.4.2).
        E_add1 = float((mu0[1] - mu0[0]) * 1e3)         # meV -- dE = 0 (spin partner)
        E_add2 = float((mu0[2] - mu0[1]) * 1e3)         # meV -- dE = valley splitting
        E_C = E_add1                                    # clean: no correction term
        E_C_check = E_add2 - VALLEY_SPLITTING * 1e3     # same quantity, other route
        C_P = abs(alpha_mu) / (E_C * 1e-3) * ct.e * 1e18   # aF, vendor sec.5.4.3
        log("")
        log(f"    E_add(1) = {E_add1:8.4f} meV   = E_C   (dE = 0, spin partner)")
        log(f"    E_add(2) = {E_add2:8.4f} meV   = E_C + valley splitting")
        log(f"    E_C      = {E_C:8.4f} meV   [cross-check via E_add(2): "
            f"{E_C_check:.4f} meV]")
        spread = abs(E_C - E_C_check) / max(abs(E_C), 1e-9) * 100
        if spread > 5:
            log(f"    *** the two E_C routes differ by {spread:.1f}% -- the dot is NOT")
            log("        in the constant-interaction regime at N = 1-3. Declare the N")
            log("        used beside every E_C and C_P. ***")
        log(f"    alpha_mu = {alpha_mu:8.4f} eV/V  [chemical-potential lever arm --")
        log("                                   NOT comparable to Beaudoin's 0.26,")
        log("                                   which is single-particle: see S2b]")
        log(f"    per-transition alphas: "
            f"{', '.join('%.4f' % x for x in alphas)}")
        log(f"    C_P      = {C_P:8.4f} aF     [6.6 aF is our own parallel-plate")
        log("                                   estimate, not an imec measurement]")
        res(f"S3\tt1=15\tvp={vp_best}\tE_C={E_C:.4f}\tE_C_check={E_C_check:.4f}"
            f"\talpha_mu={alpha_mu:.4f}\tC_P={C_P:.4f}")
    except Exception:
        log("  STAGE 3 FAILED\n" + traceback.format_exc())
else:
    log("no accumulated bias found in stage 1 -- skipping many-body")

# ------------------------------------------------------------------- STAGE 4
log("")
log("=== STAGE 4: oxide series 8/12/20 nm, ALL PARAMETERS FROZEN (prediction) ===")
for t1 in (8.0, 12.0, 20.0):
    if not mesh_for(t1).exists():
        log(f"  t1={t1:g}: mesh absent -- build with imec_qd_3x3_builder.py --t1 {t1:g}")
        continue
    for vp in (accumulated[:2] or [3.0]):
        t0 = time.time()
        try:
            d, _ = poisson(t1, vp)
            cb = d.cond_band_edge() / ct.e
            cbmin = float(cb.min())
            if cbmin < 0:
                qd, E = spectrum(d)
                dE_orb = E[2] - E[0]                     # orbital spacing, not the injected valley splitting
                log(f"  t1={t1:g} vp={vp:g}  CBmin={cbmin:+8.4f}  E0={E[0]:+9.3f}"
                    f"  dE_orb={dE_orb:6.3f} meV   ({time.time() - t0:.0f}s)")
                res(f"S4\tt1={t1}\tvp={vp}\tcbmin={cbmin:.6f}"
                    f"\tE0={E[0]:.4f}\tdE_orb={dE_orb:.4f}")
            else:
                log(f"  t1={t1:g} vp={vp:g}  CBmin={cbmin:+8.4f}  empty"
                    f"   ({time.time() - t0:.0f}s)")
                res(f"S4\tt1={t1}\tvp={vp}\tcbmin={cbmin:.6f}")
        except Exception:
            log(f"  t1={t1:g} vp={vp:g} FAILED\n" + traceback.format_exc())

log("")
log("#" * 72)
log("CAMPAIGN COMPLETE")
log("#" * 72)
