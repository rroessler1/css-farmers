"""
Main model for the farmer-biogas ABM.
"""

import random
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agents import Farmer, BiogasPlant


class FarmerBiogasModel(Model):
    """
    A model of farmers deciding whether to build biogas plants.

    The model simulates farmers making decisions based on their farm size,
    neighboring farms, and personal willingness. Farmers with biogas plants
    receive periodic payments.
    """

    def __init__(
        self,
        width=20,
        height=20,
        min_farm_capacity=10,
        max_farm_capacity=100,
        min_willingness=0.3,
        max_willingness=0.9,
        plant_cost=700.0,
        biogas_payment=0.10,
    ):
        """
        Initialize the FarmerBiogasModel.

        Args:
            n_farmers: Number of farmer agents to create
            width: Width of the grid
            height: Height of the grid
            min_farm_size: Minimum farm size
            max_farm_size: Maximum farm size
            min_willingness: Minimum willingness threshold (0.0-1.0)
            max_willingness: Maximum willingness threshold (0.0-1.0)
            biogas_payment: Amount of money farmers receive per step with a plant
        """
        super().__init__()
        self.width = width
        self.height = height
        self.plant_cost = plant_cost
        self.biogas_payment = biogas_payment

        # Create grid
        self.grid = MultiGrid(width, height, torus=False)

        # Create farmers
        for i in range(width):
            for j in range(height):
                # Random farm size and willingness
                farm_size = random.uniform(min_farm_capacity, max_farm_capacity)
                willingness = random.uniform(min_willingness, max_willingness)

                # Create farmer agent
                farmer = Farmer(self, farm_size, willingness, willingness)

                # Place farmer on grid
                self.grid.place_agent(farmer, (i, j))

        # Data collector for tracking metrics
        self.datacollector = DataCollector(
            model_reporters={
                "Total Farmers": lambda m: sum(
                    1 for a in m.agents if isinstance(a, Farmer)
                ),
                "Farmers with Plants": lambda m: sum(
                    1 for a in m.agents if isinstance(a, Farmer) and a.has_biogas_plant
                ),
                "Total Biogas Plants": lambda m: sum(
                    1 for a in m.agents if isinstance(a, BiogasPlant)
                ),
                "Total Money Distributed": lambda m: sum(
                    a.money_received for a in m.agents if isinstance(a, Farmer)
                ),
            },
            agent_reporters={
                "Farm Size": lambda a: a.farm_size if isinstance(a, Farmer) else None,
                "Willingness to Contribute": lambda a: (
                    a.willingness_to_contribute if isinstance(a, Farmer) else None
                ),
                "Has Plant": lambda a: (
                    a.has_biogas_plant if isinstance(a, Farmer) else None
                ),
                "Money Received": lambda a: (
                    a.money_received if isinstance(a, Farmer) else None
                ),
            },
        )

    def step(self):
        """
        Execute one step of the model.
        """
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")
