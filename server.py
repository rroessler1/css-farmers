"""
Visualization server for the farmer-biogas ABM using Mesa's Solara interface.
"""
import mesa
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
            "color": "green" if agent.has_biogas_plant else "brown",
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
    "n_farmers": {
        "type": "SliderInt",
        "value": 50,
        "label": "Number of Farmers",
        "min": 10,
        "max": 200,
        "step": 10,
    },
    "width": {
        "type": "SliderInt",
        "value": 10,
        "label": "Grid Width",
        "min": 5,
        "max": 30,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 10,
        "label": "Grid Height",
        "min": 5,
        "max": 30,
        "step": 1,
    },
    "min_farm_size": {
        "type": "SliderInt",
        "value": 10,
        "label": "Minimum Farm Size",
        "min": 5,
        "max": 50,
        "step": 5,
    },
    "max_farm_size": {
        "type": "SliderInt",
        "value": 100,
        "label": "Maximum Farm Size",
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
    "biogas_payment": {
        "type": "SliderFloat",
        "value": 100.0,
        "label": "Biogas Payment per Step ($)",
        "min": 10.0,
        "max": 500.0,
        "step": 10.0,
    },
}


# Create the visualization page
page = mesa.visualization.SolaraViz(
    FarmerBiogasModel,
    [
        mesa.visualization.components.make_space_component(agent_portrayal),
        mesa.visualization.components.make_plot_component(
            {"Total Farmers": "blue", "Farmers with Plants": "green"}
        ),
        mesa.visualization.components.make_plot_component(
            {"Total Money Distributed": "purple"}
        ),
    ],
    model_params=model_params,
    name="Farmer Biogas Plant ABM",
)
