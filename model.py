"""
Main model for the farmer-biogas ABM.
"""

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import numpy as np

from agents import Farmer, BiogasPlant
from lsu_distribution import sample_lsu


class FarmerBiogasModel(Model):
    """
    A model of farmers deciding whether to build biogas plants.
    """

    def __init__(
        self,
        width=20,
        height=20,
        farm_capacity_shift=0,
        biogas_payment_shift=0,
        learning_rate=0.05,
        learning_midpoint=35,
        weight_global_build=0.2,
        weight_social_build=0.2,
        weight_global_contribute=0.5,
        weight_social_contribute=0.5,
        contribute_threshold=0.25,
        # NEW:
        co_owner_penalty=-2,
        utility_sensitivity=1.0,
        utility_min_threshold=0.0,
        p_innovators=0.05,
    ):
        ...
        self.co_owner_penalty = co_owner_penalty
        self.utility_sensitivity = utility_sensitivity
        self.utility_min_threshold = utility_min_threshold
        super().__init__()

        self.width = width
        self.height = height
        self.biogas_payment_shift = biogas_payment_shift
        # Zeitvariable für Adoption usw.
        self.time = 0

        # Parameter, auf die Farmer zugreifen
        self.learning_rate = learning_rate
        self.learning_midpoint = learning_midpoint

        self.weight_global_build = weight_global_build
        self.weight_social_build = weight_social_build
        self.weight_global_contribute = weight_global_contribute
        self.weight_social_contribute = weight_social_contribute
        self.contribute_threshold = contribute_threshold

        # Grid (kein Scheduler)
        self.grid = MultiGrid(width, height, torus=False)

        # Zufalls-Generator
        g = np.random.Generator(np.random.PCG64())

        # Einen Farmer pro Zelle
        for x in range(width):
            for y in range(height):
                # Farmgröße (exponentielle Verteilung)
                farm_size = sample_lsu(farm_capacity_shift)

                # Anfängliche Bereitschaft
                if g.random() < p_innovators:
                    base_willingness_build = g.uniform(0.1, 0.3)  # Innovator
                else:
                    base_willingness_build = g.uniform(0.0, 0.0001)  # Mehrheit

                base_willingness_contrib = max(
                    0.0, min(1.0, base_willingness_build + g.uniform(0.0, 0.2))
                )

                farmer = Farmer(
                    self,
                    farm_size,
                    base_willingness_build,
                    base_willingness_contrib,
                )
                # Agent wird automatisch zu self.agents hinzugefügt
                self.grid.place_agent(farmer, (x, y))

        # DataCollector (jetzt über m.agents statt m.schedule.agents)
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
                "Total Plant Upgrades": lambda m: sum(
                    a.num_upgrades for a in m.agents if isinstance(a, BiogasPlant)
                ),
                "Total Money Distributed": lambda m: sum(
                    a.money_received for a in m.agents if isinstance(a, Farmer)
                ),
                "Total Plant Utilization": lambda m: sum(
                    a.capacity for a in m.agents if isinstance(a, BiogasPlant)
                ),
                "Total KW Produced": lambda m: sum(
                    a.get_kw(a.capacity) for a in m.agents if isinstance(a, BiogasPlant)
                ),
                "Total Plant Cost": lambda m: sum(
                    a.get_plant_cost(a.capacity)
                    for a in m.agents
                    if isinstance(a, BiogasPlant)
                ),
                "Average Cost per KW": average_cost_per_kw,
                "Cumulative Adopters": lambda m: sum(
                    1
                    for a in m.agents
                    if isinstance(a, Farmer) and a.contributes_to_biogas_plant
                ),
                "New Adopters per Step": lambda m: sum(
                    1
                    for a in m.agents
                    if isinstance(a, Farmer)
                    and a.time_of_adoption is not None
                    and a.time_of_adoption == m.time
                ),
                "Avg Num Contributors": lambda m: sum(
                    len(a.contributors)
                    for a in m.agents
                    if isinstance(a, BiogasPlant) and len(a.contributors) > 0
                )
                / max(
                    1,
                    sum(
                        1
                        for a in m.agents
                        if isinstance(a, BiogasPlant) and len(a.contributors) > 0
                    ),
                ),
                "Percent of Plants with Contributors": lambda m: (
                    sum(
                        1
                        for a in m.agents
                        if isinstance(a, BiogasPlant) and len(a.contributors) > 0
                    )
                    / max(1, sum(1 for a in m.agents if isinstance(a, BiogasPlant)))
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
        self.time += 1  # our own time counter
        self.agents.shuffle_do("step")  # calls .step() on all agents
        self.datacollector.collect(self)


def average_cost_per_kw(model):
    plants = [a for a in model.agents if isinstance(a, BiogasPlant)]
    tot_cost = sum(a.get_plant_cost(a.capacity) for a in plants)
    tot_kw = sum(a.get_kw(a.capacity) for a in plants)
    return tot_cost / tot_kw if tot_kw > 0 else 0.0
