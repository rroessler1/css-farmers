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
        if not self.has_biogas_plant:
            decision_score = self._calculate_decision_score()
            
            # Build plant if decision score exceeds willingness threshold
            if decision_score >= self.willingness:
                self.has_biogas_plant = True
                # Create biogas plant at same location
                biogas_plant = BiogasPlant(
                    self.model,
                    self
                )
                # Place on grid at same location
                if self.model.grid:
                    self.model.grid.place_agent(biogas_plant, self.pos)
        
        # Receive payment if biogas plant exists
        if self.has_biogas_plant:
            self.money_received += self.model.biogas_payment
    
    def _calculate_decision_score(self):
        """
        Calculate a decision score based on farm characteristics.
        
        Returns:
            float: Decision score between 0.0 and 1.0
        """
        # Base score from farm size (normalized)
        size_score = min(self.farm_size / 100.0, 1.0)
        
        # Get neighboring farmers
        neighbors_score = 0.0
        if self.model.grid:
            neighbors = self.model.grid.get_neighbors(
                self.pos,
                moore=True,
                include_center=False
            )
            
            # Count neighboring farmers and their average farm size
            farmer_neighbors = [n for n in neighbors if isinstance(n, Farmer)]
            if farmer_neighbors:
                avg_neighbor_size = sum(f.farm_size for f in farmer_neighbors) / len(farmer_neighbors)
                neighbors_score = min(avg_neighbor_size / 100.0, 1.0) * 0.5
        
        # Combine scores (weighted)
        decision_score = (size_score * 0.6) + (neighbors_score * 0.4)
        
        return decision_score


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
