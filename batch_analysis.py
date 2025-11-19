"""
Manual sensitivity analysis for the farmer–biogas ABM.

"""

import itertools
import pandas as pd

from model import FarmerBiogasModel, average_cost_per_kw
from agents import Farmer, BiogasPlant


# --------- Helper functions for model-level metrics --------- #

def final_cumulative_adopters(model):
    """Number of farmers that ever adopted (built or contributed)."""
    agents = list(model.agents)
    return sum(
        1
        for a in agents
        if isinstance(a, Farmer) and a.contributes_to_biogas_plant
    )


def num_plants(model):
    """Number of biogas plants in the system."""
    agents = list(model.agents)
    return sum(1 for a in agents if isinstance(a, BiogasPlant))


def total_kw(model):
    """Total installed kW capacity."""
    agents = list(model.agents)
    return sum(
        a.get_kw(a.capacity)
        for a in agents
        if isinstance(a, BiogasPlant)
    )


def run_one_sim(param_dict, max_steps=80):
    """
    Run one simulation with the given parameter dict and return a result row.
    param_dict must contain all keyword args needed for FarmerBiogasModel.
    """
    model = FarmerBiogasModel(**param_dict)

    for _ in range(max_steps):
        model.step()

    row = {
        **param_dict,  # include parameter values in the result row
        "Final_Cumulative_Adopters": final_cumulative_adopters(model),
        "Num_Plants": num_plants(model),
        "Total_KW": total_kw(model),
        "Average_Cost_per_KW": average_cost_per_kw(model),
    }
    return row

def plot_all_sensitivities(df, variable_ranges):
    """
    Create a sensitivity plot for each variable in variable_ranges.
    Plots mean of each collected metric vs the parameter values.
    """
    import matplotlib.pyplot as plt

    metrics = [
        "Final_Cumulative_Adopters",
        "Num_Plants",
        "Total_KW",
        "Average_Cost_per_KW"
    ]

    for param in variable_ranges.keys():
        for metric in metrics:
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



if __name__ == "__main__":
    # Parameters that stay constant across runs
    fixed_params = dict(
        width=20,
        height=20,
        farm_capacity_shift=0,
        # you can fix other FarmerBiogasModel defaults here if you want
    )

    # Parameters you want to sweep
    # → just change these lists to try other sensitivities
    variable_ranges = dict(
        learning_rate=[0.02, 0.05, 0.08, 0.1, 0.2],
        weight_global_build=[0.2, 0.5, 0.8],
        contribute_threshold=[0.3, 0.4, 0.5],
        innovator_share=[0.0, 0.01, 0.05, 0.1, 0.2],
        # you can add more, e.g.:
        # co_owner_penalty=[0.0, 0.1, 0.2, 0.3],
        # utility_min_threshold=[-0.5, 0.0, 0.5],
    )

    iterations = 5
    max_steps = 80

    # ---- build all parameter combinations ----
    param_names = list(variable_ranges.keys())
    param_grid = list(itertools.product(*[variable_ranges[p] for p in param_names]))

    results = []

    for combo in param_grid:
        param_values = dict(zip(param_names, combo))
        param_values.update(fixed_params)

        for run in range(iterations):
            print(f"Running combo {param_values}, run {run+1}/{iterations} ...")
            row = run_one_sim(param_values, max_steps=max_steps)
            row["run"] = run  # keep track of replicate
            results.append(row)

    df = pd.DataFrame(results)
    df.to_csv("batch_results_manual.csv", index=False)
    print("Saved batch_results_manual.csv")
    print(df.head())
    plot_all_sensitivities(df, variable_ranges)


