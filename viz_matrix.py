#!/usr/bin/env python3
"""
Visualize analysis_matrix_final.csv with traffic-light heatmaps.

Generates two figures into figs/:
 - traffic_light_heatmap_best.png: Traffic-light by (price, rate) using best rental_income advantage
 - green_share_heatmap.png: Share of green scenarios by (price, rate)
"""

from pathlib import Path
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.patches as mpatches

CSV = Path("analysis_matrix_final.csv")
FIGDIR = Path("figs")


def traffic_label(x: float) -> str:
    if x >= -300:
        return "Green"
    elif x >= -600:
        return "Yellow"
    return "Red"


def tl_code(label: str) -> int:
    return {"Red": 0, "Yellow": 1, "Green": 2}[label]


def plot_best_case_heatmap(df: pd.DataFrame) -> Path:
    best = (
        df.groupby(["home_price", "interest_rate"], as_index=False)
        .agg(max_adv=("rental_advantage", "max"))
    )
    best["light"] = best["max_adv"].apply(traffic_label)
    best["light_code"] = best["light"].map(tl_code)

    mat = (
        best.pivot(index="interest_rate", columns="home_price", values="light_code")
        .sort_index(ascending=True)
        .sort_index(axis=1)
    )

    cmap = ListedColormap(["#e74c3c", "#f1c40f", "#2ecc71"])  # Red, Yellow, Green
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], cmap.N)

    plt.figure(figsize=(12, 6))
    sns.heatmap(mat, cmap=cmap, norm=norm, cbar=False)
    plt.title("Rental Traffic Light — Best Rental Income per Price/Rate")
    plt.xlabel("Home Price")
    plt.ylabel("Interest Rate")
    plt.xticks(rotation=45, ha="right")
    legend = [
        mpatches.Patch(color="#2ecc71", label="Green (≥ -$300)"),
        mpatches.Patch(color="#f1c40f", label="Yellow (-$600 to -$300)"),
        mpatches.Patch(color="#e74c3c", label="Red (< -$600)"),
    ]
    plt.legend(handles=legend, bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    out = FIGDIR / "traffic_light_heatmap_best.png"
    plt.savefig(out, dpi=200)
    plt.close()
    return out


def plot_green_share_heatmap(df: pd.DataFrame) -> Path:
    grp = (
        df.assign(is_green=lambda d: d["rental_advantage"] >= -300)
        .groupby(["home_price", "interest_rate"])["is_green"]
        .mean()
        .reset_index(name="green_share")
    )
    mat = (
        grp.pivot(index="interest_rate", columns="home_price", values="green_share")
        .sort_index(ascending=True)
        .sort_index(axis=1)
    )

    plt.figure(figsize=(12, 6))
    sns.heatmap(mat, cmap="RdYlGn", vmin=0, vmax=1, cbar_kws={"label": "Green Share"})
    plt.title("Share of Green Scenarios — by Price/Rate")
    plt.xlabel("Home Price")
    plt.ylabel("Interest Rate")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    out = FIGDIR / "green_share_heatmap.png"
    plt.savefig(out, dpi=200)
    plt.close()
    return out


def main():
    if not CSV.exists():
        raise SystemExit(f"CSV not found: {CSV}")
    FIGDIR.mkdir(exist_ok=True)
    df = pd.read_csv(CSV)

    out1 = plot_best_case_heatmap(df)
    out2 = plot_green_share_heatmap(df)

    print(f"Saved {out1}")
    print(f"Saved {out2}")


if __name__ == "__main__":
    main()

