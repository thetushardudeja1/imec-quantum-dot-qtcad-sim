"""
Figures 1-6: built from the numbers in results/campaign_3x3_results.txt and
results/extraction_field_barrier_footprint.txt (reproduced below as arrays so the
script has no external data dependency). No simulation is run here -- this is
pure post-processing of already-solved results. matplotlib only.

Run from anywhere; paths are resolved relative to this file.
"""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "figures"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titleweight": "bold",
    "axes.titlesize": 13,
    "axes.labelweight": "bold",
    "axes.labelsize": 11,
    "legend.fontsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})


def bold_legend(ax, **kw):
    leg = ax.legend(prop={"weight": "bold", "size": kw.pop("fontsize", 9)}, **kw)
    return leg

# ---------------------------------------------------------------------------
# Fig 1: single-particle turn-on / lever-arm fit
# from campaign_3x3_results.txt (S12 t1=15 rows) -- POST-FIX, validated numbers
vp = np.array([2.85, 2.9, 3.0, 3.1, 3.2, 3.4, 3.6])
E0 = np.array([128.6181, 114.4709, 86.1641, 57.8414, 25.5080, -31.4976, -88.2336])  # meV

# linear fit over the near-linear window used for the reported alpha_sp (2.85-3.05 V band
# is what the vendor leverarm.Solver used); here we fit the reported 7-point sweep and
# annotate BOTH the vendor-solver value (0.2831, -- see docs/validation.md) and our own fit.
fit = np.polyfit(vp, E0, 1)  # meV/V
alpha_ownfit = -fit[0] / 1000.0  # eV/V  (E = -e*alpha*V + const)
alpha_vendor = 0.2831

fig, ax = plt.subplots(figsize=(5.2, 4))
ax.plot(vp, E0, "o", color="#2166ac", ms=7, label="computed $E_0$ (Schrödinger-Poisson)")
vp_line = np.linspace(vp.min(), vp.max(), 100)
ax.plot(vp_line, np.polyval(fit, vp_line), "--", color="#2166ac", lw=1.3, alpha=0.7,
        label=f"linear fit: $\\alpha$ = {alpha_ownfit:.3f} eV/V")
ax.axhline(0, color="gray", lw=0.8)
ax.set_xlabel("Plunger voltage $V_P$ (V)")
ax.set_ylabel("Ground-state energy $E_0$ (meV)")
ax.set_title("Single-electron loading: lever-arm extraction")
ax.text(0.03, 0.05,
        f"vendor leverarm.Solver: $\\alpha_{{sp}}$ = {alpha_vendor:.4f} eV/V\n"
        f"Beaudoin (comparable device): 0.26 eV/V  (+8.9%)",
        transform=ax.transAxes, fontsize=8.5, va="bottom",
        bbox=dict(boxstyle="round", fc="white", ec="0.8"))
bold_legend(ax, loc="upper right", fontsize=8.5)
fig.tight_layout()
fig.savefig(OUT / "fig1_leverarm_turnon.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 2: orbital spacing vs plunger bias (dot tightens under bias)
dE_orb = np.array([10.7306, 10.8615, 11.1216, 11.3792, 11.4699, 11.8858, 12.4004])  # meV

fig, ax = plt.subplots(figsize=(5.2, 4))
ax.plot(vp, dE_orb, "s-", color="#b2182b", ms=6)
ax.set_xlabel("Plunger voltage $V_P$ (V)")
ax.set_ylabel("First orbital spacing  $E_2-E_0$  (meV)")
ax.set_title("Orbital-level spacing vs. bias")
ax.text(0.03, 0.92,
        "Mohiyaddin (IEDM 2019, imec sim.): ~10 meV\nat the few-electron end \u2192 consistent",
        transform=ax.transAxes, fontsize=8.5, va="top",
        bbox=dict(boxstyle="round", fc="white", ec="0.8"))
fig.tight_layout()
fig.savefig(OUT / "fig2_orbital_spacing.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 3: vertical field and dot footprint vs bias (from extraction_field_barrier_footprint.txt)
vp3 = np.array([2.85, 2.9, 2.95, 3.0, 3.05])
Fz = np.array([309.6, 314.4, 319.1, 323.8, 328.5])       # kV/cm
Lx = np.array([22.24, 22.13, 22.02, 21.91, 21.81])
Ly = np.array([15.09, 15.03, 14.96, 14.90, 14.84])

fig, axes = plt.subplots(1, 2, figsize=(9.5, 4))

ax = axes[0]
ax.plot(vp3, Fz, "o-", color="#4d9221", ms=6)
ax.axhline(200, color="gray", ls=":", lw=1.2)
ax.text(vp3[0], 205, "Mohiyaddin ~200 kV/cm", fontsize=8, color="gray")
ax.set_xlabel("$V_P$ (V)")
ax.set_ylabel("$|F_z|$ in the dot (kV/cm)")
ax.set_title("Vertical confining field")

ax = axes[1]
ax.plot(vp3, Lx, "o-", label="$L_x$ (along plunger)", color="#2166ac")
ax.plot(vp3, Ly, "s-", label="$L_y$ (along confinement)", color="#b2182b")
ax.set_xlabel("$V_P$ (V)")
ax.set_ylabel("Dot extent, 4$\\sigma$ (nm)")
ax.set_title("Dot footprint vs. bias")
bold_legend(ax, fontsize=8.5)

fig.suptitle("Extracted field and confinement, $t_1$ = 15 nm",
             fontsize=14, fontweight="bold", y=1.04)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(OUT / "fig3_field_and_footprint.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 4: confinement-gate (screening/actuation) sweep from check_new_geometry_results.txt
vc = np.array([0.00, 0.50, 1.00])
cbmin = np.array([-0.0215, -0.1168, -0.2085])
E0c = np.array([114.471, 15.445, -80.122])
area = np.array([332, 374, 444])

fig, ax1 = plt.subplots(figsize=(5.8, 4.6))
ax1.plot(vc, area, "o-", color="#762a83", ms=7)
ax1.set_xlabel("Confinement-gate voltage $V_C = V_B$ (V)")
ax1.set_ylabel("Dot area (nm$^2$)", color="#762a83", fontweight="bold")
ax1.tick_params(axis="y", labelcolor="#762a83")
fig.suptitle("Confinement-gate actuation of the dot", fontsize=13, fontweight="bold", y=0.99)
ax1.set_title("$V_P$ fixed at 2.9 V \u2014 confounded by filling above $V_C$=1 V",
              fontsize=9.5, fontweight="normal", style="italic", pad=8)

ax2 = ax1.twinx()
ax2.plot(vc, E0c, "s--", color="#1b7837", ms=6)
ax2.set_ylabel("$E_0$ (meV)", color="#1b7837", fontweight="bold")
ax2.tick_params(axis="y", labelcolor="#1b7837")
ax2.axhline(0, color="0.6", lw=0.8)

fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT / "fig4_confinement_gate_sweep.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 5: honest calibration comparison -- ours vs imec MEASURED vs imec SIMULATED
# numbers from docs/validation.md
labels = ["$C_P$ (aF)", "$E_C$ (meV)", "lever arm $\\alpha$"]
ours   = [1.45, 30.68, 0.278]
imec_measured = [6.1, 4.01, 0.152]
imec_sim_range = [(0.55, 2.2), None, None]  # only C_P has a published simulated range

x = np.arange(len(labels))
w = 0.35
fig, ax = plt.subplots(figsize=(6.2, 4.2))
b1 = ax.bar(x - w/2, ours, w, label="ours (isolated-dot QTCAD sim.)", color="#2166ac")
b2 = ax.bar(x + w/2, imec_measured, w, label="imec measured (Loenders, fitted)", color="#b2182b")

# overlay the imec simulated Mohiyaddin range for C_P only
ax.errorbar(x[0]+w/2 - w, np.mean(imec_sim_range[0]),
            yerr=[[np.mean(imec_sim_range[0]) - imec_sim_range[0][0]],
                  [imec_sim_range[0][1] - np.mean(imec_sim_range[0])]],
            fmt="none", ecolor="black", elinewidth=1.5, capsize=5)
ax.annotate("imec SIMULATED\nrange (Mohiyaddin)", xy=(x[0]-w, np.mean(imec_sim_range[0])),
            xytext=(x[0]-0.85, 12), fontsize=7.5, ha="center",
            arrowprops=dict(arrowstyle="->", lw=0.8))

ax.set_yscale("log")
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("value (log scale)")
ax.set_title("Calibration: simulation-vs-measurement\nis not apples-to-apples")
bold_legend(ax, fontsize=8, loc="upper right")
fig.tight_layout()
fig.savefig(OUT / "fig5_calibration_comparison.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 6: energy-level diagram at V_P = 2.9V, t1=15nm  (see docs/validation.md)
levels = [
    (114.471, 115.171, "$n=0$"),
    (125.332, 126.032, "$n=1$"),
    (134.920, 135.620, "$n=2$"),
    (137.707, 138.407, "$n=3$"),
]
fig, ax = plt.subplots(figsize=(4.6, 5.5))
xw = 0.6
for i, (elo, ehi, lab) in enumerate(levels):
    ax.hlines(elo, i - xw/2, i + xw/2, color="#2166ac", lw=2.5)
    ax.hlines(ehi, i - xw/2, i + xw/2, color="#b2182b", lw=2.5)
    ax.annotate("", xy=(i, ehi), xytext=(i, elo),
                arrowprops=dict(arrowstyle="<->", color="gray", lw=0.8))
    ax.text(i + xw/2 + 0.05, (elo+ehi)/2, "0.700\nmeV\n(valley)", fontsize=6.5, va="center")
    if i > 0:
        prev_mid = np.mean(levels[i-1][:2])
        this_mid = np.mean([elo, ehi])
        ax.annotate("", xy=(i - xw/2 - 0.05, elo), xytext=(i-1+xw/2+0.05, levels[i-1][1]),
                    arrowprops=dict(arrowstyle="->", color="0.4", lw=0.6, ls=":"))
ax.set_xticks(range(len(levels)))
ax.set_xticklabels([lab for *_, lab in levels])
ax.set_ylabel("Energy (meV)")
ax.set_title("Valley-split orbital spectrum\n$V_P$=2.9 V, $t_1$=15 nm (post-fix)")
ax.text(0.02, 0.02,
        "orbital gaps: 10.16 / 8.89 / 2.09 meV\n(blue = lower valley, red = upper valley)",
        transform=ax.transAxes, fontsize=7.5, va="bottom",
        bbox=dict(boxstyle="round", fc="white", ec="0.8"))
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT / "fig6_energy_level_diagram.png")
plt.close(fig)

print("wrote 6 figures to", OUT)
for f in sorted(p.name for p in OUT.glob("*.png")):
    print(" -", f)
