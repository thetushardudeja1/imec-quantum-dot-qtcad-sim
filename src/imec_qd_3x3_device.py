"""imec SiMOS 3x3 array — device definition and solve (INTERIOR cell).

Uses the corrected geometry (real 37 nm confinement gates, 50 nm barriers) built by
imec_qd_3x3_builder.py, and the published parameters:

  work function   4.70 eV   [Mohiyaddin IEDM 2019] (Beaudoin use intrinsic Si = 4.61)
  substrate       1e16 acceptors/cm^3, Ohmic     [Beaudoin]
  temperature     1.4 K (measured ELECTRON temperature; fridge is 200 mK) [Loenders App.]
  valley          g = gqc/2 WITH explicit valley splitting -- the two go together

Gate naming (central dot at the origin):
  C1..C4  confinement, x = -165 -55 +55 +165   (C2/C3 flank the central dot)
  P1..P3  plungers,    y = -110   0  +110      (P2 is the central plunger)
  B1..B4  barriers,    y = -165 -55 +55 +165   (B2/B3 flank the central dot)

TARGETS (revised 2026-09-12 -- see HANDOFF.md sec.8):
  C_P ~ 6.6 aF is OUR OWN parallel-plate estimate eps0*eps_r*A/t2, NOT a Loenders
  measurement, and Loenders say dot capacitance is dominated by source/drain coupling
  rather than the plunger. DOWNGRADED to an order-of-magnitude bound.
  Strongest surviving target: the ORBITAL spacing E2-E0 (computed, not supplied).
NOT targets: E_C / C_Sigma (array parasitics + reservoirs we do not model), V_th
(QTCAD has no threshold concept), dE = 0.7 meV (we inject it as valley splitting).
"""

import argparse
import pathlib
import time

import numpy as np

from qtcad.device import Device, SubDevice
from qtcad.device import constants as ct
from qtcad.device import materials as mt
from qtcad.device.mesh3d import Mesh, SubMesh
from qtcad.device.poisson import Solver as PoissonSolver
from qtcad.device.poisson import SolverParams as PoissonSolverParams
from qtcad.device.schrodinger import Solver as SchrodingerSolver
from qtcad.device.schrodinger import SolverParams as SchrodingerSolverParams

SCALING = 1e-9
TEMPERATURE = 1.4
ACCEPTOR_BINDING = 45e-3
VALLEY_SPLITTING = 0.7e-3       # eV, supplied as a known input -- NOT a prediction
QD_REGIONS = ["substrate.QD", "ox1.QD"]

CONF = ["C1", "C2", "C3", "C4"]
PLUNGERS = ["P1", "P2", "P3"]
BARRIERS = ["B1", "B2", "B3", "B4"]
CENTRAL_PLUNGER = "P2"


def make_device(mesh_file, wf_eV, vp, vpn, vc, vb, doping_cm3, sub_bc="ohmic"):
    d = Device(Mesh(SCALING, mesh_file), conf_carriers="e")
    d.set_temperature(TEMPERATURE)
    d.new_region("substrate", mt.Si, pdoping=doping_cm3 * 1e6)
    d.new_region("substrate.QD", mt.Si, pdoping=doping_cm3 * 1e6)
    for ox in ("ox1", "ox1.QD", "ox2", "ox3"):
        d.new_region(ox, mt.SiO2)
    d.set_valley_splitting(VALLEY_SPLITTING * ct.e)

    wf = wf_eV * ct.e
    for g in CONF:
        d.new_gate_bnd(g, vc, wf)
    for g in PLUNGERS:
        d.new_gate_bnd(g, vp if g == CENTRAL_PLUNGER else vpn, wf)
    for g in BARRIERS:
        d.new_gate_bnd(g, vb, wf)

    if sub_bc == "frozen":
        d.new_frozen_bnd("substrate_bnd", 0.0, mt.Si, doping_cm3 * 1e6, "p",
                         ACCEPTOR_BINDING * ct.e)
    else:
        d.new_ohmic_bnd("substrate_bnd")     # Beaudoin use Ohmic at 100 mK

    # FIX 1 (2026-09-12) -- THE missing call. Zeroes the CLASSICAL (Thomas-Fermi)
    # charge density inside the dot region, so the electrons there are described
    # quantum-mechanically instead of as a classical gas. Without it an accumulation
    # layer forms exactly where the dot should be and screens the plunger: the solve
    # still converges and every number downstream is quietly wrong.
    #   API     : qtcad.device.device.set_dot_region
    #   vendor  : called in GaAs_gated/2,3,4, Ge_hole/2,3,4, adaptive_schrodinger.py,
    #             poisson_negf_master.py, sym_dqdfdsoi.py, helper/double_dot_fdsoi.py
    #   Beaudoin: "a region of strong quantum confinement is created ... in which we
    #             set the classical electron density to zero to model electrons
    #             quantum-mechanically"
    # See HANDOFF.md sec.6b defect 1 and trap 15.
    d.set_dot_region(QD_REGIONS)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--t1", type=float, default=15.0)
    ap.add_argument("--wf", type=float, default=4.70)
    ap.add_argument("--vp", type=float, default=2.0, help="central plunger P2")
    ap.add_argument("--vpn", type=float, default=0.0, help="neighbour plungers P1,P3")
    ap.add_argument("--vc", type=float, default=0.0, help="confinement C1..C4")
    ap.add_argument("--vb", type=float, default=0.0, help="barriers B1..B4")
    ap.add_argument("--doping", type=float, default=1e16)
    ap.add_argument("--sub-bc", default="ohmic", choices=["ohmic", "frozen"])
    ap.add_argument("--nstates", type=int, default=8)
    ap.add_argument("--poisson-only", action="store_true")
    a = ap.parse_args()

    root = pathlib.Path(__file__).parent.parent.resolve()
    mf = root / "meshes" / f"imec_qd_3x3_t1_{a.t1:g}nm.msh"
    if not mf.exists():
        raise SystemExit(f"mesh not found: {mf}\nrun imec_qd_3x3_builder.py --t1 {a.t1:g}")

    print("=" * 78)
    print(f"imec SiMOS 3x3 INTERIOR cell   t1={a.t1:g} nm   T={TEMPERATURE} K")
    print(f"  PUBLISHED : wf {a.wf:.2f} eV, substrate {a.doping:g} cm^-3 ({a.sub_bc})")
    print(f"  BIAS      : P2={a.vp:g}  P1,P3={a.vpn:g}  C={a.vc:g}  B={a.vb:g}")
    print("=" * 78, flush=True)

    t0 = time.time()
    d = make_device(mf, a.wf, a.vp, a.vpn, a.vc, a.vb, a.doping, a.sub_bc)
    print(f"[{time.time() - t0:6.1f}s] device built", flush=True)

    p = PoissonSolverParams()
    p.tol = 1e-6
    p.maxiter = 200
    PoissonSolver(d, solver_params=p).solve()
    print(f"[{time.time() - t0:6.1f}s] nonlinear Poisson done", flush=True)

    cb = d.cond_band_edge() / ct.e
    print(f"  CB edge: min {cb.min():+.4f} eV   max {cb.max():+.4f} eV")

    if a.poisson_only:
        print("(--poisson-only: stopping here)")
        return

    d.set_V_from_phi()
    qd = SubDevice(d, SubMesh(d.mesh, QD_REGIONS))
    s = SchrodingerSolverParams()
    s.num_states = a.nstates
    s.tol = 1e-8
    SchrodingerSolver(qd, solver_params=s).solve()
    E = np.asarray(qd.energies) / ct.e * 1e3
    print(f"[{time.time() - t0:6.1f}s] Schrodinger done", flush=True)

    print("\n--- single-particle spectrum (meV) ---")
    for i, e in enumerate(E):
        gap = f"   +{E[i] - E[i - 1]:6.3f}" if i else ""
        print(f"  E{i} = {e:+10.4f}{gap}")

    # FIX 3 (2026-09-12) -- E1-E0 is IDENTICALLY the valley splitting we injected via
    # set_valley_splitting(); it is an input, not a result. Assert it (a live check that
    # the valley convention is still wired correctly) and report the ORBITAL spacing.
    # See HANDOFF.md sec.6b defect 2 and trap 16.
    dv_readback = E[1] - E[0]
    assert abs(dv_readback - VALLEY_SPLITTING * 1e3) < 1e-6, (
        f"valley convention broken: E1-E0 = {dv_readback} meV, "
        f"expected {VALLEY_SPLITTING * 1e3} meV")
    print(f"\n  valley splitting  = {VALLEY_SPLITTING * 1e3:.4f} meV   <-- INPUT "
          f"(set_valley_splitting), verified by readback")
    print(f"  orbital E2-E0     = {E[2] - E[0]:.4f} meV   <-- COMPUTED "
          f"[Mohiyaddin: s-p 'a few meV']")


if __name__ == "__main__":
    main()
