"""Extract the three quantities we had never pulled out, from the SAVED Poisson
solutions of the 2026-09-12 lever-arm run. No Poisson solve is repeated.

  1. |F_z| in the dot            [Mohiyaddin IEDM 2019: ~200 kV/cm]
  2. lateral confinement barrier [Mohiyaddin: "several tens of meV"]
  3. dot footprint               [Loenders: 50 x 70 nm, area 3733 nm^2]

Inputs: data_leverarm_<V>.hdf5, written by qtcad.device.leverarm.Solver during
STAGE 2b of the re-run. phi is loaded and set on the device; only Schrodinger is
re-solved (~30 s per bias).

Footprint convention: `analysis.analyze_dot` defines size = 4*sigma (+-2 sigma) of
|psi_0|^2 per axis. That is the VENDOR's convention -- stated explicitly because the
records already note that dot-length metrics are convention-dependent (see docs/methodology.md).
A participation area A_eff = (integral |psi|^2)^2 / integral |psi|^4 is reported
alongside it as a convention-free cross-check.
"""

import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).parent.resolve()
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from imec_qd_3x3_device import (CENTRAL_PLUNGER, QD_REGIONS,  # noqa: E402
                                VALLEY_SPLITTING, make_device)
from qtcad.device import SubDevice  # noqa: E402
from qtcad.device import analysis as an  # noqa: E402
from qtcad.device import constants as ct  # noqa: E402
from qtcad.device import io  # noqa: E402
from qtcad.device.mesh3d import SubMesh  # noqa: E402
from qtcad.device.schrodinger import Solver as SchSolver  # noqa: E402
from qtcad.device.schrodinger import SolverParams as SchParams  # noqa: E402

WF, DOPING, SUB_BC = 4.70, 1e16, "ohmic"
MESH = ROOT / "meshes" / "imec_qd_3x3_t1_15nm.msh"
MVEMT_SLOPE = 0.1025          # meV per MV/m, our benchmark vs Gamble APL 2016

VOLTAGES = [2.850, 2.900, 2.950, 3.000, 3.050]

print("=" * 78)
print("EXTRACTION from saved Poisson solutions (no Poisson re-solve)")
print("targets: |F_z| ~200 kV/cm, barrier 'several tens of meV' [Mohiyaddin IEDM2019]")
print("         footprint 50 x 70 nm / 3733 nm^2                [Loenders]")
print("=" * 78)

rows = []
for vp in VOLTAGES:
    f = ROOT / f"data_leverarm_{vp:.3f}V.hdf5"
    if not f.exists():
        print(f"  {vp:.3f} V: {f.name} missing, skipping")
        continue

    d = make_device(MESH, WF, vp, 0.0, 0.0, 0.0, DOPING, SUB_BC)
    phi = io.load(str(f), var_name="var")
    d.set_potential(phi)

    XG = np.asarray(d.mesh.glob_nodes)                  # (nodes, 3), metres
    # cond_band_edge() is ALSO a local-node array (n_elements, 4) -- map it to
    # global nodes before indexing it with a node mask.
    cb = np.asarray(d.cond_band_edge() / ct.e)          # eV, referenced to E_F = 0
    if cb.shape[0] != XG.shape[0]:
        cb = np.asarray(d.mesh.toglobal(cb))

    # ---- electric field ------------------------------------------------------
    # an.gradient returns a LOCAL-node array (n_elements, 4, 3); mesh.toglobal()
    # averages it onto global nodes. Indexing it directly gives garbage.
    grad_phi = np.asarray(an.gradient(d.mesh, np.asarray(phi)))
    Ez = np.asarray(d.mesh.toglobal(-grad_phi[:, :, 2]))   # V/m, per global node

    # ---- Schrodinger -> wavefunction -> footprint ----------------------------
    d.set_V_from_phi()
    sm = SubMesh(d.mesh, QD_REGIONS)
    qd = SubDevice(d, sm)
    sp = SchParams()
    sp.num_states = 4
    sp.tol = 1e-8
    SchSolver(qd, solver_params=sp).solve()
    E = np.asarray(qd.energies) / ct.e * 1e3            # meV

    # NOTE: analysis.analyze_dot() cannot handle the valley axis that
    # set_valley_splitting() introduces -- eigenfunctions are (nodes, state, valley)
    # and it broadcasts (n,2) against (n,). So the moments are computed here instead,
    # on the valley-SUMMED density, which is the vendor's own convention
    # (double_dot_fdsoi.state_probability_density: "summing over that axis recovers
    # the scalar density used for ... charge-density calculations").
    psi = np.asarray(qd.eigenfunctions)[:, 0]           # (nodes,) or (nodes, valley)
    p = np.abs(psi) ** 2
    if p.ndim > 1:
        p = p.sum(axis=tuple(range(1, p.ndim)))         # sum over valley

    X = np.asarray(sm.glob_nodes)                       # (nodes, 3), metres
    N = float(an.integrate(sm, p))
    pos = np.array([float(an.integrate(sm, p * X[:, k])) / N for k in range(3)])
    var = np.array([float(an.integrate(sm, p * (X[:, k] - pos[k]) ** 2)) / N
                    for k in range(3)])
    std = np.sqrt(var) * 1e9                            # nm
    size = 4.0 * std                                    # nm, vendor's +-2 sigma
    pos = pos * 1e9                                     # nm

    # participation VOLUME, convention-free: V_eff = (int p)^2 / int p^2
    n4 = float(an.integrate(sm, (p / N) ** 2))
    vol_eff = 1.0 / n4                                  # m^3
    vol_eff_nm3 = vol_eff * 1e27

    # ---- |F_z| in the dot: average over a sphere of R_AVG about the dot centre
    # MEDIAN, not mean: a sphere wide enough to hold enough nodes also touches the
    # Si/SiO2 interface, where Ez jumps by the permittivity ratio and drags the mean
    # up. The median is flat at ~319 kV/cm for R = 2..10 nm; the mean is not.
    c = pos * 1e-9                                      # dot centre, metres
    R_AVG = 6e-9
    near = np.linalg.norm(XG - c, axis=1) < R_AVG
    Fz_dot = abs(float(np.median(Ez[near])))
    Fz_n = int(near.sum())

    # ---- lateral confinement barrier: CB along x and y through the dot, in Si,
    # at the dot depth. This is the barrier Mohiyaddin quote; the earlier version
    # wrongly picked up the 3.2 eV Si/SiO2 band offset instead.
    slab = np.abs(XG[:, 2] - c[2]) < 0.5e-9
    bar = {}
    for ax, other in ((0, 1), (1, 0)):
        m = slab & (np.abs(XG[:, other] - c[other]) < 3e-9)
        if m.sum() < 20:
            bar[ax] = float("nan"); continue
        xs, cbs = XG[m, ax], cb[m]
        o = np.argsort(xs); xs, cbs = xs[o], cbs[o]
        i0 = int(np.argmin(np.abs(xs - c[ax])))         # the dot, at the centre
        cmin = cbs[max(0, i0 - 3):i0 + 4].min()
        left = cbs[:i0].max() if i0 > 5 else np.nan
        right = cbs[i0:].max() if i0 < len(cbs) - 5 else np.nan
        bar[ax] = (float(np.nanmin([left, right])) - float(cmin)) * 1e3   # meV
    barrier_x, barrier_y = bar[0], bar[1]
    cb_dot_min = float(cb[near].min())

    Fz_kVcm = Fz_dot / 1e5
    Fz_MVm = Fz_dot / 1e6
    vs_pred = MVEMT_SLOPE * Fz_MVm                      # meV, from our MVEMT slope

    print(f"\n--- V_P = {vp:.3f} V " + "-" * 50)
    print(f"  CB min in dot      {cb_dot_min:+8.4f} eV")
    print(f"  lateral barrier     x {barrier_x:7.1f} meV   y {barrier_y:7.1f} meV"
          f"   [dot-to-BULK, C/B gates at 0 V -- NOT comparable to")
    print("                       Mohiyaddin's 'several tens of meV', which is a GATED"
          " inter-dot barrier]")
    print(f"  |F_z| in dot (median, {Fz_n:4d} nodes within {R_AVG * 1e9:.0f} nm)"
          f" {Fz_kVcm:8.1f} kV/cm  = {Fz_MVm:.2f} MV/m"
          f"   [Mohiyaddin ~200 kV/cm]")
    print(f"     -> valley splitting PREDICTED by our MVEMT slope: {vs_pred:.3f} meV"
          f"   [we INJECT {VALLEY_SPLITTING * 1e3:.2f} meV]")
    print(f"  dot centre (x,y,z)  {pos[0]:+7.2f} {pos[1]:+7.2f} {pos[2]:+7.2f} nm")
    print(f"  sigma  (x,y,z)      {std[0]:7.2f} {std[1]:7.2f} {std[2]:7.2f} nm")
    print(f"  size = 4 sigma      {size[0]:7.2f} {size[1]:7.2f} {size[2]:7.2f} nm"
          f"   [Loenders TEM: 50 x 70 nm]")
    print(f"  area (4sig x 4sig)  {size[0] * size[1]:8.0f} nm^2"
          f"   [Loenders fitted: 3733 nm^2]")
    print(f"  V_eff participation {vol_eff_nm3:8.0f} nm^3  (convention-free)")
    print(f"  spectrum (meV)      {', '.join('%.3f' % x for x in E)}")
    print(f"  orbital E2-E0       {E[2] - E[0]:.3f} meV")

    rows.append(dict(vp=vp, cb=cb_dot_min, barrier=barrier_x, barrier_y=barrier_y,
                     Fz=Fz_kVcm, vs_pred=vs_pred,
                     sx=size[0], sy=size[1], sz=size[2],
                     area=size[0] * size[1], A_eff=vol_eff_nm3,
                     dE=E[2] - E[0]))

if rows:
    out = ROOT / "extraction_field_barrier_footprint.txt"
    with open(out, "w", encoding="utf-8") as fh:
        hdr = ("vp\tCBmin_eV\tbarrier_meV\tFz_kVcm\tVS_pred_meV\t"
               "size_x_nm\tsize_y_nm\tsize_z_nm\tarea_nm2\tAeff_nm2\tdE_orb_meV\n")
        fh.write(hdr)
        for r in rows:
            fh.write(f"{r['vp']}\t{r['cb']:.6f}\t{r['barrier']:.2f}\t{r['Fz']:.1f}\t"
                     f"{r['vs_pred']:.4f}\t{r['sx']:.2f}\t{r['sy']:.2f}\t{r['sz']:.2f}\t"
                     f"{r['area']:.0f}\t{r['A_eff']:.0f}\t{r['dE']:.3f}\n")
    print(f"\nwrote {out}")
