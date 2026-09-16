"""
Device figures (fig7-9), rendered with full matplotlib control to avoid the
title/legend clipping produced by QTCAD's own plot_slice()/plot_bands() (which
manage their own figure and savefig call internally). Data comes from QTCAD's own
analysis API (get_slice for exact-plane mesh interpolation, linecut for the band
diagram) -- see qtcad.device.analysis in the QTCAD API reference -- just plotted
by hand here.

NOT RUNNABLE OUT OF THE BOX: it loads a saved Poisson solution (an .hdf5 potential
field) on a specific 3D mesh (.msh), neither of which is shipped in this repo --
the mesh is ~550 MB and the mesh format/solver both require a licensed QTCAD
installation (see THIRD_PARTY_NOTICES.md). This script is included for
transparency/reproducibility of HOW figures 7-9 were made, not for turnkey re-run.
To reproduce: build the mesh with src/imec_qd_3x3_builder.py using the GATE WIDTHS
documented in docs/validation.md (37/50/50 nm -- the geometry this particular run
used, since revised; see docs/validation.md for why), solve a Poisson iteration at
V_P=2.9 V with src/imec_qd_3x3_device.py, save phi, then point MESH/HDF5 below at
the results.
"""
import os
os.environ.setdefault("MKL_THREADING_LAYER", "TBB")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "figures"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(REPO / "src"))

from imec_qd_3x3_device import make_device  # noqa: E402
from qtcad.device import analysis as an  # noqa: E402
from qtcad.device import constants as ct  # noqa: E402
from qtcad.device import io  # noqa: E402

MESH = REPO / "meshes" / "imec_qd_3x3_t1_15nm_GEOMv1_derived.msh"   # not shipped, see docstring
HDF5 = REPO / "data_leverarm_2.900V.hdf5"                           # not shipped, see docstring
WF, DOPING, SUB_BC = 4.70, 1e16, "ohmic"
VP = 2.900

plt.rcParams.update({
    "font.size": 11,
    "axes.titleweight": "bold",
    "axes.titlesize": 13,
    "axes.labelweight": "bold",
    "axes.labelsize": 11,
    "legend.fontsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.2,
})
CMAP = "RdYlBu_r"


def bold_legend(ax, **kw):
    return ax.legend(prop={"weight": "bold", "size": kw.pop("fontsize", 9)}, **kw)


print("building device on", MESH.name, "...")
d = make_device(str(MESH), WF, VP, 0.0, 0.0, 0.0, DOPING, SUB_BC)
phi = io.load(str(HDF5), var_name="var")
d.set_potential(phi)

cb = np.asarray(d.cond_band_edge()) / ct.e   # eV
vb = np.asarray(d.vlnce_band_edge()) / ct.e  # eV

# ---------------------------------------------------------------------------
# Fig 7: vertical cross-section (y=0) -- exact plane/mesh interpolation via get_slice
X, Z, V = an.get_slice(d.mesh, cb, normal=(0, 1, 0), origin=(0, 0, 0),
                        resolution=(500, 300), length_unit="nm", coords=True)

fig, ax = plt.subplots(figsize=(9.5, 5.8))
pcm = ax.pcolormesh(X, Z, V, cmap=CMAP, shading="auto", vmin=0, vmax=4.0)
cbar = fig.colorbar(pcm, ax=ax, pad=0.02)
cbar.set_label("Conduction-band edge (eV)", fontweight="bold")
for zline in (0, 15.0, 19.6, 20.4):
    ax.axhline(zline, color="k", lw=0.5, ls=":")
for xg, lab in zip([-165, -55, 55, 165], ["C1", "C2", "C3", "C4"]):
    ax.annotate(lab, (xg, 13), ha="center", fontsize=9, fontweight="bold", color="k",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))
ax.set_xlim(-190, 190)
ax.set_ylim(-40, 25)
ax.set_xlabel("x (nm), along the plunger stripe")
ax.set_ylabel("z (nm), depth (0 = Si/oxide interface)")
ax.set_title(f"Gate-stack cross-section through the central dot ($V_P$ = {VP:.2f} V)",
             fontsize=13, pad=12)
fig.tight_layout()
fig.savefig(OUT / "fig7_device_cross_section.png")
plt.close(fig)
print("wrote fig7_device_cross_section.png")

# ---------------------------------------------------------------------------
# Fig 8: in-plane confinement map, z = -2 nm
X2, Y2, V2 = an.get_slice(d.mesh, cb, normal=(0, 0, 1), origin=(0, 0, -2e-9),
                           resolution=(400, 400), length_unit="nm", coords=True)

fig, ax = plt.subplots(figsize=(7.2, 7.6))
pcm = ax.pcolormesh(X2, Y2, V2, cmap=CMAP, shading="auto")
cbar = fig.colorbar(pcm, ax=ax, pad=0.02, shrink=0.85)
cbar.set_label("Conduction-band edge (eV)", fontweight="bold")
ax.plot(0, 0, "k+", ms=16, mew=2)
ax.annotate("central dot\n(band-edge minimum)", (0, 0), xytext=(40, 55),
            fontsize=9, fontweight="bold",
            arrowprops=dict(arrowstyle="->", lw=1.0))
for xg, lab in zip([-165, -55, 55, 165], ["C1", "C2", "C3", "C4"]):
    if abs(xg) < 185:
        ax.text(xg, 172, lab, ha="center", fontsize=9, fontweight="bold")
ax.set_xlim(-190, 190)
ax.set_ylim(-190, 190)
ax.set_xlabel("x (nm)")
ax.set_ylabel("y (nm)")
ax.set_aspect("equal")
ax.set_title(f"In-plane electrostatic confinement, z = -2 nm ($V_P$ = {VP:.2f} V)",
             fontsize=12.5, pad=12)
fig.tight_layout()
fig.savefig(OUT / "fig8_dot_confinement_topview.png")
plt.close(fig)
print("wrote fig8_dot_confinement_topview.png")

# ---------------------------------------------------------------------------
# Fig 9: band diagram along a vertical linecut through the dot
begin, end = (0, 0, 20.4e-9), (0, 0, -40e-9)
dist, Ec_line = an.linecut(d.mesh, cb, begin, end)
_, Ev_line = an.linecut(d.mesh, vb, begin, end)
dist_nm = dist * 1e9

fig, ax = plt.subplots(figsize=(7.5, 5.6))
ax.plot(dist_nm, Ec_line, color="#b2182b", lw=2.2, label="$E_C$")
ax.plot(dist_nm, Ev_line, color="#2166ac", lw=2.2, ls="--", label="$E_V$")
ax.axhline(0, color="k", lw=1.0, ls=":", label="$E_F$")
ax.set_xlabel("Distance along z (nm), surface \u2192 substrate")
ax.set_ylabel("Energy (eV)")
ax.set_title(f"Band diagram through the central dot ($V_P$ = {VP:.2f} V)", fontsize=13, pad=12)
bold_legend(ax, loc="center right", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "fig9_band_diagram_linecut.png")
plt.close(fig)
print("wrote fig9_band_diagram_linecut.png")

print("done.")
