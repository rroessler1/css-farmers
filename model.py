"""
Main model for the farmer-biogas ABM.
"""

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import numpy as np

from agents import Farmer, BiogasPlant


class FarmerBiogasModel(Model):
    """
    A model of farmers deciding whether to build biogas plants.
    """

    def __init__(
        self,
        width=20,
        height=20,
        min_farm_capacity=10,
        max_farm_capacity=100,
        min_willingness=0.3,  # werden aktuell nicht direkt genutzt
        max_willingness=0.9,  # werden aktuell nicht direkt genutzt
        plant_cost=700.0,
        biogas_payment=0.10,
        # S-Kurven Parameter
        learning_rate=0.05,      # k
        learning_midpoint=25,   # t0
        # Gewichte
        weight_global_build=0.5,
        weight_social_build=0.05,
        weight_global_contribute=0.5,
        weight_social_contribute=0.1,
        contribute_threshold=0.7,
    ):
        super().__init__()

        self.width = width
        self.height = height
        self.plant_cost = plant_cost
        self.biogas_payment = biogas_payment

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

        # Anteil Innovatoren
        p_innovators = 0.05

        # Einen Farmer pro Zelle
        for x in range(width):
            for y in range(height):
                # Farmgröße (exponentielle Verteilung)
                farm_size = min(
                    g.exponential(scale=1 / 3)
                    * (max_farm_capacity - min_farm_capacity)
                    + min_farm_capacity,
                    max_farm_capacity,
                )

                # Anfängliche Bereitschaft
                if g.random() < p_innovators:
                    base_willingness_build = g.uniform(0.6, 0.9)  # Innovator
                else:
                    base_willingness_build = g.uniform(0.0, 0.3)  # Mehrheit

                base_willingness_contrib = min(
                    1.0, base_willingness_build + g.uniform(0.0, 0.2)
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
                    1 for a in m.agents
                    if isinstance(a, Farmer) and a.has_biogas_plant
                ),
                "Total Biogas Plants": lambda m: sum(
                    1 for a in m.agents if isinstance(a, BiogasPlant)
                ),
                "Total Money Distributed": lambda m: sum(
                    a.money_received for a in m.agents if isinstance(a, Farmer)
                ),
                "Cumulative Adopters": lambda m: sum(
                    1 for a in m.agents
                    if isinstance(a, Farmer) and a.contributes_to_biogas_plant
                ),
                "New Adopters per Step": lambda m: sum(
                    1 for a in m.agents
                    if isinstance(a, Farmer)
                    and a.time_of_adoption is not None
                    and a.time_of_adoption == m.time
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
