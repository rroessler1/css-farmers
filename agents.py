"""
Agent classes for the farmer-biogas ABM.
"""

from mesa import Agent


class Farmer(Agent):
    """
    A farmer agent that decides whether to build a biogas plant.

    Decision is based on:
    - Farm size
    - Neighboring farms
    - Personal willingness
    """

    def __init__(self, model, farm_size, willingness):
        """
        Initialize a Farmer agent.

        Args:
            model: The model instance
            farm_size: Size of the farmer's farm (affects decision)
            willingness: Personal willingness factor (0.0-1.0)
        """
        super().__init__(model)
        self.farm_size = farm_size
        self.willingness = willingness
        self.has_biogas_plant = False
        self.contributes_to_biogas_plant = False
        self.influence = 0
        self.money_received = 0.0

    def step(self):
        """
        Execute one step of the agent's behavior.

        The farmer decides whether to build a biogas plant based on:
        - Their farm size
        - The number/size of neighboring farms
        - Their personal willingness
        """
        # Only make decision if don't already have a plant
        if not self.contributes_to_biogas_plant:
            self._decide_whether_to_build_biogas_plant()

        # Receive payment if biogas plant exists
        if self.has_biogas_plant:
            self.money_received += self.model.biogas_payment

        if self.contributes_to_biogas_plant:
            self.influence += self.model.neighbor_influence

    def _decide_whether_to_build_biogas_plant(self):
        """
        Calculate a decision score based on farm characteristics.

        Returns:
            float: Decision score between 0.0 and 1.0
        """
        # Get neighboring farmers
        if self.model.grid:
            neighbors = self.model.grid.get_neighbors(
                self.pos, moore=True, include_center=False
            )

            # Count neighboring farmers and their average farm size
            farmer_neighbors = [n for n in neighbors if isinstance(n, Farmer)]
            if farmer_neighbors:
                total_contributions = sum(
                    f.farm_size
                    for f in farmer_neighbors
                    if not f.contributes_to_biogas_plant
                )
                total_influence = sum(
                    f.influence
                    for f in farmer_neighbors
                    if f.contributes_to_biogas_plant
                )
                if (
                    total_contributions
                    + total_influence
                    + self.model.biogas_payment * 1000
                    > self.model.plant_cost
                ):
                    for f in farmer_neighbors:
                        f.contributes_to_biogas_plant = True
                    self.contributes_to_biogas_plant = True
                    self.has_biogas_plant = True


class BiogasPlant(Agent):
    """
    A biogas plant agent that provides payments to its owner.
    """

    def __init__(self, model, owner):
        """
        Initialize a BiogasPlant agent.

        Args:
            model: The model instance
            owner: The Farmer agent that owns this plant
        """
        super().__init__(model)
        self.owner = owner

    def step(self):
        """
        Execute one step of the agent's behavior.

        The biogas plant currently just exists - payments are handled
        by the Farmer agent.
        """
        pass
