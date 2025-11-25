"""
Visualization server for the farmer-biogas ABM using Mesa's Solara interface.
"""

from mesa.visualization import SolaraViz, make_space_component, make_plot_component
import solara
from mesa.visualization.utils import force_update

from agents import Farmer, BiogasPlant
from model import FarmerBiogasModel


def agent_portrayal(agent):
    """
    Define how agents are portrayed in the visualization.

    Args:
        agent: The agent to portray

    Returns:
        dict: Portrayal properties for the agent
    """
    if isinstance(agent, Farmer):
        if agent.has_biogas_plant:
            return {
                "size": 60,  # size doesn't work unfortunately :(
                "color": agent.biogas_plant.get_color(),
                "marker": "s",
            }
        else:
            portrayal = {
                "size": 50,
                "color": (
                    agent.biogas_plant.get_color()
                    if agent.has_biogas_plant
                    else "green" if agent.contributes_to_biogas_plant else "blue"
                ),
                "marker": "o",
            }
            return portrayal
    else:
        # This is the biogas plant. Haven't figured out how to hide agents
        return {
            "size": 60,  # size doesn't work unfortunately :(
            "color": agent.get_color(),
            "marker": "s",
        }


# Model parameters for the interface
model_params = {
    "width": {
        "type": "SliderInt",
        "value": 20,
        "label": "Grid Width",
        "min": 5,
        "max": 30,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 20,
        "label": "Grid Height",
        "min": 5,
        "max": 30,
        "step": 1,
    },
    "farm_capacity_shift": {
        "type": "SliderInt",
        "value": 10,
        "label": "Farm Capacity Shift",
        "min": -50,
        "max": 50,
        "step": 5,
    },
    "contribute_threshold": {
        "type": "SliderFloat",
        "value": 0.4,
        "label": "Contribution Threshold",
        "min": 0.0,
        "max": 1.0,
        "step": 0.05,
    },
}


@solara.component
def BiogasPaymentControl(model):
    """Solara component to adjust biogas payment on the running model.

    This component injects a small card into the left sidebar so it cannot be
    dragged around the main dashboard.
    """

    def set_payment(v):
        model.biogas_payment_shift = v
        force_update()

    # Render into the global Sidebar so this control is fixed in the left column
    with solara.Sidebar():
        with solara.Card("Biogas Payment"):
            solara.SliderFloat(
                label="Biogas payment per step ($)",
                value=model.biogas_payment_shift,
                on_value=set_payment,
                min=-3.0,
                max=3.0,
                step=0.05,
            )

    return None


# Create the visualization page
page = SolaraViz(
    model=FarmerBiogasModel(),
    renderer=None,
    components=[
        make_space_component(agent_portrayal),
        make_plot_component({"Avg Num Contributors": "blue"}),
        make_plot_component({"Percent of Plants with Contributors": "blue"}),
        # Plot 1: diffusion curve + its derivative
        make_plot_component(
            {
                "Total Farmers": "blue",
                "Cumulative Adopters": "green",  # S-curve
                "New Adopters per Step": "orange",  # bell-shaped curve
            }
        ),
        # Plot 2: Biogas Plants
        make_plot_component(
            {
                "Total Biogas Plants": "blue",
                "Total Plant Upgrades": "green",  # S-curve
            }
        ),
        make_plot_component({"Total KW Produced": "blue"}),
        make_plot_component({"Total Plant Cost": "blue"}),
        make_plot_component({"Average Cost per KW": "blue"}),
        # live control
        BiogasPaymentControl,
    ],
    model_params=model_params,
    name="Farmer Biogas Plant ABM",
)
