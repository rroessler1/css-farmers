"""
Manual sensitivity analysis for the farmer–biogas ABM.

"""

import itertools
import pandas as pd
import tqdm

from model import (
    FarmerBiogasModel,
    average_cost_per_kw,
    average_num_contributors,
    percent_plants_with_contributors,
)
from agents import Farmer, BiogasPlant


# --------- Helper functions for model-level metrics --------- #


def final_cumulative_adopters(model):
    """Number of farmers that ever adopted (built or contributed)."""
    agents = list(model.agents)
    return sum(
        1 for a in agents if isinstance(a, Farmer) and a.contributes_to_biogas_plant
    )


def num_plants(model):
    """Number of biogas plants in the system."""
    agents = list(model.agents)
    return sum(1 for a in agents if isinstance(a, BiogasPlant))


def total_kw(model):
    """Total installed kW capacity."""
    agents = list(model.agents)
    return sum(a.get_kw(a.capacity) for a in agents if isinstance(a, BiogasPlant))

def plant_size_counts(model):
    """Number of plants by size class (small / medium / large)."""
    agents = list(model.agents)
    small = sum(
        1
        for a in agents
        if isinstance(a, BiogasPlant) and a.plant_type == BiogasPlant.SMALL
    )
    medium = sum(
        1
        for a in agents
        if isinstance(a, BiogasPlant) and a.plant_type == BiogasPlant.MEDIUM
    )
    large = sum(
        1
        for a in agents
        if isinstance(a, BiogasPlant) and a.plant_type == BiogasPlant.LARGE
    )
    return small, medium, large


def run_one_sim(param_dict, max_steps=80):
    """
    Run one simulation with the given parameter dict and return a result row.
    param_dict must contain all keyword args needed for FarmerBiogasModel.
    """
    model = FarmerBiogasModel(**param_dict)

    for _ in range(max_steps):
        model.step()

    # neue Auswertungen
    small, medium, large = plant_size_counts(model)


    row = {
        **param_dict,  # include parameter values in the result row
        "Final_Cumulative_Adopters": final_cumulative_adopters(model),
        "Num_Plants": num_plants(model),
        "Total_KW": total_kw(model),
        "Average_Cost_per_KW": average_cost_per_kw(model),
        "Average_Num_Contributors": average_num_contributors(model),
        "Percent_Plants_with_Contributors": percent_plants_with_contributors(model),

        # neu: Anzahl Anlagen nach Grösse
        "Num_Plants_Small": small,
        "Num_Plants_Medium": medium,
        "Num_Plants_Large": large,


    }
    return row



def plot_all_sensitivities(df, variable_ranges):
    """
    Create sensitivity plots:
    - single-metric plots (wie bisher)
    - plus einen Multi-Plot für die Anlagengrössen (Small/Medium/Large).
    """
    import matplotlib.pyplot as plt

    # "normale" Metriken
    single_metrics = [
        "Final_Cumulative_Adopters",
        "Num_Plants",
        "Total_KW",
        "Average_Cost_per_KW",
    ]

    # Grössen-Metriken (alle zusammen in einem Plot)
    size_metrics = [
        "Num_Plants_Small",
        "Num_Plants_Medium",
        "Num_Plants_Large",
        # optional:
        # "KW_Small", "KW_Medium", "KW_Large",
    ]

    # ---------- 1) Single-metric Plots (wie vorher) ----------
    for param in variable_ranges.keys():
        for metric in single_metrics:
            plt.figure()
            grouped = df.groupby(param)[metric].mean().reset_index()
            plt.plot(grouped[param], grouped[metric], marker="o")
            plt.xlabel(param)
            plt.ylabel(f"Mean {metric}")
            plt.title(f"Sensitivity of {metric} to {param}")
            plt.tight_layout()
            plt.savefig(f"sensitivity_{metric}_vs_{param}.png", dpi=300)
            plt.show()
            plt.close()
            print(f"Saved: sensitivity_{metric}_vs_{param}.png")

    # ---------- 2) Gemeinsamer Plot für Anlagengrössen ----------
    for param in variable_ranges.keys():
        plt.figure()
        grouped = df.groupby(param).mean().reset_index()


        label_map = {
            "Num_Plants_Small": "Small plants",
            "Num_Plants_Medium": "Medium plants",
            "Num_Plants_Large": "Large plants",
        }

        for metric in size_metrics:
            if metric in grouped.columns:
                plt.plot(
                    grouped[param],
                    grouped[metric],
                    marker="o",
                    label=label_map.get(metric, metric),
                )

        plt.xlabel(param)
        plt.ylabel("Mean number of plants")
        plt.title(f"Sensitivity of plant size distribution to {param}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"sensitivity_plant_sizes_vs_{param}.png", dpi=300)
        plt.show()
        plt.close()
        print(f"Saved: sensitivity_plant_sizes_vs_{param}.png")


if __name__ == "__main__":
    # Parameters that stay constant across runs
    fixed_params = dict(
        width=20,
        height=20,

    )

    # Parameters  to sweep

    variable_ranges = dict(
        #learning_rate=[0.02, 0.05, 0.08, 0.1, 0.2,0.3,0.4,0.5,1],
        #weight_global_build=[0,0.2, 0.4, 0.6, 0.8,1],
        #weight_social_build=[0,0.2, 0.4, 0.6, 0.8,1],
        #weight_global_contribute=[0,0.2, 0.4, 0.6, 0.8,1],
        #weight_social_contribute=[0,0.2, 0.4, 0.6, 0.8,1],
        #contribute_threshold=[0,0.2, 0.4, 0.6, 0.8,1],
        #p_innovators=[0,0.02, 0.05, 0.08, 0.1, 0.2,0.3,0.4,0.5,0.8,1],
        # biogas_payment_shift=[-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3],
        # farm_capacity_shift=[-30, -20, -10, 0, 10, 20, 30],
        # contribute_threshold=[0.1, 0.3, 0.5, 0.7,1],
        learning_midpoint=[5,10, 20, 30, 40, 50, 60, 70, 80]
        # utility_sensitivity=[0.5, 1.0, 2.0],
        # utility_min_threshold=[-0.2, -0.1, 0.0, 0.1, 0.2],
        # plant_lifetime_years=[15, 20, 25],
        # discount_rate=[0.02, 0.04, 0.06],
        # profit_scale_chf=[50_000.0, 100_000.0, 200_000.0],
    )

    iterations = 20
    max_steps = 80

    # ---- build all parameter combinations ----
    param_names = list(variable_ranges.keys())
    param_grid = list(itertools.product(*[variable_ranges[p] for p in param_names]))

    results = []

    for combo in tqdm.tqdm(param_grid, desc="Parameter sweep"):
        param_values = dict(zip(param_names, combo))
        param_values.update(fixed_params)

        for run in range(iterations):
            row = run_one_sim(param_values, max_steps=max_steps)
            row["run"] = run  # keep track of replicate
            results.append(row)

    df = pd.DataFrame(results)
    df.to_csv("batch_results_manual.csv", index=False)
    print("Saved batch_results_manual.csv")
    print(df)
    plot_all_sensitivities(df, variable_ranges)
