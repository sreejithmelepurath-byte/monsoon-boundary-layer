"""Monsoon Boundary Layer Analysis.

Compares Convective Boundary Layer (CBL) height and Low-Level Jet (LLJ)
strength at Trivandrum and Mangalore between an active (8-13 July 2001) and a
weak/break (18-23 July 2001) phase of the Indian summer monsoon.

Usage:
    python src/analysis.py            # prints summary tables, writes figures/
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGURES = ROOT / "figures"

STATION_COLORS = {"Trivandrum": "#2a6f97", "Mangalore": "#e07a5f"}
STATION_MARKERS = {"Trivandrum": "s", "Mangalore": "x"}


def load_cbl() -> pd.DataFrame:
    df = pd.read_csv(DATA / "cbl_heights.csv", parse_dates=["date"])
    df["phase"] = pd.Categorical(df["phase"], ["active", "weak"], ordered=True)
    return df


def summarise_cbl(df: pd.DataFrame) -> pd.DataFrame:
    """Mean CBL per station and phase, excluding days with no θe-q reversal."""
    valid = df.dropna(subset=["cbl_height_m"])
    means = valid.pivot_table(index="station", columns="phase", values="cbl_height_m", aggfunc="mean", observed=True)
    counts = valid.pivot_table(index="station", columns="phase", values="cbl_height_m", aggfunc="count", observed=True)
    out = means.round(0).astype(int)
    out.columns = [f"mean_{c}_m" for c in out.columns]
    out["valid_days_active"] = counts["active"]
    out["valid_days_weak"] = counts["weak"]
    out["pct_increase"] = ((means["weak"] - means["active"]) / means["active"] * 100).round(1)
    return out.loc[["Trivandrum", "Mangalore"]]


def terrain_ratio(summary: pd.DataFrame) -> pd.Series:
    """How much deeper Mangalore's CBL runs than Trivandrum's, per phase."""
    return (summary.loc["Mangalore", ["mean_active_m", "mean_weak_m"]]
            / summary.loc["Trivandrum", ["mean_active_m", "mean_weak_m"]]).round(2)


def plot_daily_cbl(df: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, phase in zip(axes, ["active", "weak"]):
        sub = df[df["phase"] == phase]
        for station, grp in sub.groupby("station"):
            ax.plot(grp["date"].dt.day, grp["cbl_height_m"], marker=STATION_MARKERS[station],
                    color=STATION_COLORS[station], label=station, linewidth=1.8)
        ax.set_title(f"{phase.capitalize()} phase")
        ax.set_xlabel("Day of July 2001")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("CBL height (m)")
    axes[0].legend(frameon=False)
    fig.suptitle("Daily Convective Boundary Layer height")
    fig.tight_layout()
    path = FIGURES / "cbl_daily.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_mean_cbl(summary: pd.DataFrame) -> Path:
    labels, values, colors = [], [], []
    for station in ["Trivandrum", "Mangalore"]:
        for phase in ["active", "weak"]:
            labels.append(f"{station[:3].upper()}\n{phase}")
            values.append(summary.loc[station, f"mean_{phase}_m"])
            colors.append(STATION_COLORS[station] if phase == "active" else STATION_COLORS[station] + "99")
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, values, color=colors)
    ax.bar_label(bars, fmt="%d m", padding=3)
    ax.set_ylabel("Mean CBL height (m)")
    ax.set_title("Mean CBL height: active vs weak monsoon phase")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path = FIGURES / "cbl_mean.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_llj() -> Path:
    llj = pd.read_csv(DATA / "low_level_jet.csv")
    pivot = llj.pivot(index="station", columns="phase", values="core_speed_kt").loc[["Trivandrum", "Mangalore"]]
    ax = pivot.plot(kind="bar", figsize=(6, 4), color=["#3d5a80", "#98c1d9"], rot=0)
    ax.set_ylabel("LLJ core speed (knots)")
    ax.set_title("Low-Level Jet weakens in the break phase")
    ax.legend(title="Phase", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    path = FIGURES / "llj_core_speed.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    cbl = load_cbl()
    summary = summarise_cbl(cbl)
    print("Mean CBL height by station and phase\n")
    print(summary.to_string(), "\n")
    print("Mangalore / Trivandrum CBL ratio:", terrain_ratio(summary).to_dict(), "\n")

    llj = pd.read_csv(DATA / "low_level_jet.csv").pivot(index="station", columns="phase", values="core_speed_kt")
    drop = ((llj["active"] - llj["weak"]) / llj["active"] * 100).round(0)
    print("LLJ core-speed drop, active -> weak (%):", drop.to_dict(), "\n")

    for path in (plot_daily_cbl(cbl), plot_mean_cbl(summary), plot_llj()):
        print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
