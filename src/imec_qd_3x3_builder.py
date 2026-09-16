"""imec SiMOS 3x3 quantum-dot array, geometry builder (REAL gate widths).

Replaces the single-cell builder, which used gate widths inflated 3x (110/90 nm instead
of 37/50) purely to grow the simulation domain. That suppressed C_P -- the one clean
calibration target -- because GL1 sits between the plunger and the channel, and it made
the cell an EDGE cell, which imec explicitly exclude from their own statistics.

Here the domain is obtained the honest way: by building MORE CELLS. The central dot then
has real neighbours on all four sides and is a genuine INTERIOR cell.

GEOMETRY -- CORRECTED 2026-09-13. See docs/device_spec.md and docs/validation.md.
The previous version derived the gate widths FROM the measured dot
(CONF_W = PITCH - DOT_X, BARRIER_W = PITCH - DOT_Y - 2*GAP), i.e. it assumed the dot
exactly fills the lithographic gap. It does not -- the dot is electrostatically defined
and is narrower than the gate opening. That made the gate widths circular (the dot size
was an INPUT to the layout, so it could never validate it) and it baked in GAP = 5.0 nm,
which was Li's *vertical* inter-layer dielectric misapplied as a *lateral* gap.

  pitch            110 nm both directions                      [Loenders, published]
  confinement gate 30 nm  -> gap = 80 nm                       [Li IEDM2020 Fig.4c TEM;
                   Fig.5 gives litho spacing 30 nm -> etched confinement gap 48 nm at
                   Li's ~78 nm pitch. At Loenders' 110 nm pitch the CD is process-limited
                   and the gap opens instead: the measured 73 nm dot fits an 80 nm gap
                   and could not fit a 48 nm one.]
  plunger          76 nm                                       [Loenders Fig.1C SEM,
                   measured against the 100 nm scale bar]
  barrier          30 nm                                       [Mohiyaddin IEDM2019 Fig.2
                   table: barrier gate width b < 30 nm; Li Fig.4c TEM ~26 nm]
  t1 / delta2 / delta3   15 / 4.6 / 0.8 nm                     [Loenders App., STEM]

CONSISTENCY CHECKS this set passes and the old one failed:
  plunger + barrier = 76 + 30 = 106 ~ pitch 110  -> the gates TILE, which is what an
      "overlapping-gate architecture" means. Old set: 50 + 50 = 100, a 10 nm ungated strip.
  dot 73 nm long in an 80 nm confinement gap; dot 50 nm wide under a 76 nm plunger
      -> electrostatically narrower than the lithography, as it must be.

DECLARED UNCERTAINTY: Li is a linear double dot at ~78 nm pitch patterned by EBL;
Loenders is a 7x7 array at 110 nm pitch patterned by EUV. Gate CDs transfer as process
capability, pitch does not. The TEM/SEM reads are +-20%. These are SOURCED INFERENCES,
not published values -- but strictly better than values reverse-engineered from the answer.

LAYOUT (central dot at the origin)
  GL1 confinement  C1..C4  stripes along y at x = -165, -55, +55, +165
                           -> 3 columns, gaps centred at x = -110, 0, +110
  GL2 plungers     P1..P3  stripes along x at y = -110, 0, +110   (P2 is central)
  GL3 barriers     B1..B4  stripes along x at y = -165, -55, +55, +165

MESHING -- deliberately COARSE here. The vendor workflow refines adaptively in the
linear-Poisson stage (docs/QTCAD_METHODOLOGY.md sec.2): their run went 4,496 -> 526,081
nodes automatically. Do NOT hand-build a fine uniform mesh; that is what caused our
convergence and RAM problems.

USAGE
    conda activate qtcad
    python imec_qd_3x3_builder.py --t1 15
"""

import argparse
import pathlib

import gmsh
from qtcad.builder import Builder, Mask, Polygon

# --- geometry, nm (published / TEM) ------------------------------------------
PITCH = 110.0       # [Loenders] published
CONF_W = 30.0       # [Li IEDM2020 Fig.4c TEM + Fig.5]  -> confinement gap 80 nm
PLUNGER_W = 76.0    # [Loenders Fig.1C SEM vs 100 nm bar]
BARRIER_W = 30.0    # [Mohiyaddin Fig.2 table b<30; Li Fig.4c TEM]
# NOTE: GAP is deleted. In an overlapping-gate stack the plunger (GL2) and barrier (GL3)
# sit in DIFFERENT layers and overlap; there is no lateral gap between them.

# The measured dot. These are OUTPUTS to compare the solve against -- they must NEVER
# re-enter the layout, or the geometry becomes circular again (standing rule 3).
DOT_X_MEAS = 73.0   # along the plunger stripe   [Loenders App., TEM]
DOT_Y_MEAS = 50.0   # across the plunger stripe  [Loenders App., TEM]
CONF_GAP = PITCH - CONF_W          # 80 nm  -- must exceed DOT_X_MEAS (73). It does.
BARRIER_GAP = PITCH - BARRIER_W    # 80 nm

T_SUB = 60.0        # silicon substrate depth in the domain
DELTA2 = 4.6        # ILD GL1 -> GL2
DELTA3 = 0.8        # ILD GL2 -> GL3

# 3x3: outermost gate centres at +-1.5*pitch; domain just clears them
CONF_X = [-1.5 * PITCH, -0.5 * PITCH, 0.5 * PITCH, 1.5 * PITCH]   # -165 -55 55 165
PLUNGER_Y = [-PITCH, 0.0, PITCH]                                   # -110 0 110
BARRIER_Y = [-1.5 * PITCH, -0.5 * PITCH, 0.5 * PITCH, 1.5 * PITCH]

DOMAIN_W = 2 * (1.5 * PITCH + CONF_W / 2)      # 367
DOMAIN_L = 2 * (1.5 * PITCH + BARRIER_W / 2)   # 380

# QD sub-region: the Schrodinger domain around the CENTRAL dot only.
# Must be large enough that the wavefunction decays before the wall
# (Tunnel_Falls_DAPS/2-energy_vs_detuning warns about artificial confinement).
QD_X, QD_Y = 110.0, 90.0
QD_DEPTH = 20.0     # below the Si/SiO2 interface

CHAR_LEN = 12.0     # COARSE base mesh -- adaptivity refines it later
DOT_CHAR_LEN = 2.5  # only inside the QD region


def _groups():
    out = {}
    for dim, tag in gmsh.model.getPhysicalGroups():
        out.setdefault(dim, []).append(gmsh.model.getPhysicalName(dim, tag))
    return out


def build(t1: float, out_dir: pathlib.Path) -> pathlib.Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    t2, t3 = t1 + DELTA2, t1 + DELTA2 + DELTA3
    tag = f"3x3_t1_{t1:g}nm"

    # ---- masks -------------------------------------------------------------
    foot = Mask("footprint")
    foot.add_shape(Polygon.box(DOMAIN_W, DOMAIN_L, name="footprint").centered())

    gl1 = Mask("gl1")
    gl1.add_shapes([
        Polygon.box(CONF_W, DOMAIN_L, name=f"C{i + 1}").centered().translated(x, 0)
        for i, x in enumerate(CONF_X)
    ])

    gl2 = Mask("gl2")
    gl2.add_shapes([
        Polygon.box(DOMAIN_W, PLUNGER_W, name=f"P{i + 1}").centered().translated(0, y)
        for i, y in enumerate(PLUNGER_Y)
    ])

    gl3 = Mask("gl3")
    gl3.add_shapes([
        Polygon.box(DOMAIN_W, BARRIER_W, name=f"B{i + 1}").centered().translated(0, y)
        for i, y in enumerate(BARRIER_Y)
    ])

    dots = Mask("dots")
    dots.add_shape(Polygon.box(QD_X, QD_Y, name="QD").centered())

    # ---- build -------------------------------------------------------------
    b = Builder(name="imec SiMOS 3x3 array")
    b.set_mesh_size(CHAR_LEN)
    for m in (foot, gl1, gl2, gl3, dots):
        b.add_mask(m)

    b.use_mask("footprint")
    b.set_z(-T_SUB)
    b.set_group_name("substrate").extrude(T_SUB)
    b.set_group_name("ox1").extrude(t1)

    # GL1, then the ILD that FILLS AROUND it (fill_mode -- without it the next
    # extrusion buries and destroys the gate surfaces)
    b.use_mask("gl1").group_from_shape().add_surface()
    b.fill_mode()
    b.use_mask("footprint").set_group_name("ox2").extrude(DELTA2)
    b.displace_mode()

    b.use_mask("gl2").group_from_shape().add_surface()
    b.fill_mode()
    b.use_mask("footprint").set_group_name("ox3").extrude(DELTA3)
    b.displace_mode()

    b.use_mask("gl3").group_from_shape().add_surface()

    # QD sub-region around the CENTRAL dot, refined
    b.overlay_mode()
    b.set_mesh_size(DOT_CHAR_LEN).minimum_mesh_size()
    b.set_z(-QD_DEPTH)
    b.use_mask("dots").group_from_shape().extrude(QD_DEPTH + t1)

    # substrate contact (lambda form -- rename_group silently no-ops here)
    b.merge_groups(lambda g: g.dim == 2 and g.name == "substrate_bottom", "substrate_bnd")

    # ---- mesh, verify, write ----------------------------------------------
    b.mesh()
    g = _groups()
    print("\n" + "=" * 78)
    print(f"imec SiMOS 3x3   t1={t1:g}  t2={t2:.1f}  t3={t3:.1f} nm")
    print(f"  domain {DOMAIN_W:g} x {DOMAIN_L:g} nm   QD box {QD_X:g} x {QD_Y:g} nm")
    print(f"  gates: conf {CONF_W:g} nm (x{len(CONF_X)}), plunger {PLUNGER_W:g} nm "
          f"(x{len(PLUNGER_Y)}), barrier {BARRIER_W:g} nm (x{len(BARRIER_Y)})")
    print(f"  gaps : confinement {CONF_GAP:g} nm, barrier {BARRIER_GAP:g} nm")
    print(f"  tiling: plunger + barrier = {PLUNGER_W + BARRIER_W:g} nm vs pitch {PITCH:g}")
    print(f"  TARGET dot (NOT an input) = {DOT_X_MEAS:g} x {DOT_Y_MEAS:g} nm  [Loenders TEM]")
    print("=" * 78)
    for dim in sorted(g):
        print(f"  dim {dim}: {', '.join(sorted(g[dim]))}")

    required = ([f"C{i + 1}" for i in range(len(CONF_X))]
                + [f"P{i + 1}" for i in range(len(PLUNGER_Y))]
                + [f"B{i + 1}" for i in range(len(BARRIER_Y))]
                + ["substrate_bnd"])
    got2d = g.get(2, [])
    missing = [r for r in required if not any(r == n or r in n for n in got2d)]
    print("\nREQUIRED BOUNDARIES:",
          "ALL PRESENT" if not missing else f"MISSING {missing}")
    if missing:
        raise SystemExit("geometry incomplete - fix before solving")

    mesh_path = out_dir / f"imec_qd_{tag}.msh"
    b.write(mesh_path).write(out_dir / f"imec_qd_{tag}.xao")
    print("mesh ->", mesh_path)
    return mesh_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--t1", type=float, default=15.0)
    args = ap.parse_args()
    build(args.t1, pathlib.Path(__file__).parent.parent.resolve() / "meshes")
