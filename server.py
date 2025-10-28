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
        portrayal = {
            "size": 50,
            "color": (
                "green"
                if agent.has_biogas_plant
                else "yellow" if agent.contributes_to_biogas_plant else "brown"
            ),
            "shape": "circle",
            "layer": 0,
        }
        # Size based on farm size
        portrayal["size"] = 30 + (agent.farm_size / 5)
        return portrayal
    elif isinstance(agent, BiogasPlant):
        return {
            "size": 60,
            "color": "blue",
            "shape": "rect",
            "layer": 1,
        }
    return {}


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
    "min_farm_capacity": {
        "type": "SliderInt",
        "value": 10,
        "label": "Minimum Farm Capacity",
        "min": 5,
        "max": 50,
        "step": 5,
    },
    "max_farm_capacity": {
        "type": "SliderInt",
        "value": 100,
        "label": "Maximum Farm Capacity",
        "min": 50,
        "max": 200,
        "step": 10,
    },
    "min_willingness": {
        "type": "SliderFloat",
        "value": 0.3,
        "label": "Minimum Willingness",
        "min": 0.0,
        "max": 0.5,
        "step": 0.1,
    },
    "max_willingness": {
        "type": "SliderFloat",
        "value": 0.9,
        "label": "Maximum Willingness",
        "min": 0.5,
        "max": 1.0,
        "step": 0.1,
    },
    "plant_cost": {
        "type": "SliderFloat",
        "value": 700,
        "label": "Biogas Plant Cost ($)",
        "min": 0,
        "max": 2000,
        "step": 50,
    },
}


@solara.component
def BiogasPaymentControl(model):
    """Solara component to adjust biogas payment on the running model.

    This component injects a small card into the left sidebar so it cannot be
    dragged around the main dashboard.
    """

    def set_payment(v):
        model.biogas_payment = v
        force_update()

    # Render into the global Sidebar so this control is fixed in the left column
    with solara.Sidebar():
        with solara.Card("Biogas Payment"):
            solara.SliderFloat(
                label="Biogas payment per step ($)",
                value=model.biogas_payment,
                on_value=set_payment,
                min=0.0,
                max=1.0,
                step=0.05,
            )

    return None


# Create the visualization page
page = SolaraViz(
    model=FarmerBiogasModel(),
    renderer=None,
    components=[
        make_space_component(agent_portrayal),
        make_plot_component({"Total Farmers": "blue", "Farmers with Plants": "green"}),
        make_plot_component({"Total Money Distributed": "purple"}),
        # Live control to adjust biogas payment while the model runs
        BiogasPaymentControl,
    ],
    model_params=model_params,
    name="Farmer Biogas Plant ABM",
)
