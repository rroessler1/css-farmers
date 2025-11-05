"""
Agent classes for the farmer-biogas ABM.
"""

from enum import Enum
from mesa import Agent


class Farmer(Agent):
    """
    A farmer agent that decides whether to build a biogas plant.

    Decision is based on:
    - Farm size
    - Neighboring farms
    - Personal willingness
    """

    def __init__(
        self, model, farm_size, willingness_to_build, willingness_to_contribute
    ):
        """
        Initialize a Farmer agent.

        Args:
            model: The model instance
            farm_size: Size of the farmer's farm (affects decision)
            willingness: Personal willingness factor (0.0-1.0)
        """
        super().__init__(model)
        self.farm_size = farm_size
        self.willingness_to_build = willingness_to_build
        self.willingness_to_contribute = willingness_to_contribute
        self.has_biogas_plant = False
        self.contributes_to_biogas_plant = False
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
        self._check_and_update_willingness()

    def _check_and_update_willingness(self):
        if self.model.grid:
            neighbors = self.model.grid.get_neighbors(
                self.pos,
                moore=True,
                include_center=False,
                radius=1,  # can increase if needed
            )
            neighbors = [n for n in neighbors if isinstance(n, Farmer)]
            self.willingness_to_contribute += (
                len([n for n in neighbors if n.contributes_to_biogas_plant]) * 0.01
            )

            neighbors = self.model.grid.get_neighbors(
                self.pos,
                moore=True,
                include_center=False,
                radius=3,  # can increase if needed
            )
            neighbors = [n for n in neighbors if isinstance(n, Farmer)]
            self.willingness_to_build += (
                len([n for n in neighbors if n.has_biogas_plant]) * 0.01
            )

    def _decide_whether_to_build_biogas_plant(self):
        if self.willingness_to_build < 0.5:
            return
        if self.contributes_to_biogas_plant:
            return

        if self.model.grid:
            neighbors = self.model.grid.get_neighbors(
                self.pos,
                moore=True,
                include_center=False,
                radius=1,  # can increase if needed
            )
            contributing_neighbors = get_neighbors_willing_to_contribute(neighbors)
            available_lsus = get_available_LSUs(contributing_neighbors) + self.farm_size

            # As per the paper, we only use the largest farms if we have excess capacity
            if available_lsus > BiogasPlant.MAX_SIZE:
                contributing_neighbors = sorted(
                    contributing_neighbors, key=lambda x: x.farm_size, reverse=True
                )
                while available_lsus > BiogasPlant.MAX_SIZE:
                    removed_farmer = contributing_neighbors.pop()
                    available_lsus -= removed_farmer.farm_size

            # TODO: have an actual utility function to decide whether to build a plant
            # right now this builds just as long as there's enough capacity
            if BiogasPlant.MIN_SIZE <= available_lsus <= BiogasPlant.MAX_SIZE:
                self.build_biogas_plant(available_lsus, contributing_neighbors)

    def build_biogas_plant(self, capacity, contributing_neighbors):
        plant = BiogasPlant(self.model, self, capacity)
        self.model.grid.place_agent(plant, self.pos)

        self.has_biogas_plant = True
        self.contributes_to_biogas_plant = True
        for neighbor in contributing_neighbors:
            neighbor.contributes_to_biogas_plant = True

        # TODO: we might want to extend the influence to further neighbors and update their influence score
        return plant


def calculate_utility(plant_type, capacity):
    # TODO: should include age and some other factors I guess
    return calculate_biogas_plant_return(plant_type, capacity)


def get_neighbors_willing_to_contribute(neighbors: list):
    neighbors = [n for n in neighbors if isinstance(n, Farmer)]
    return [
        n
        for n in neighbors
        if not n.contributes_to_biogas_plant and n.willingness_to_contribute > 0.5
    ]


def get_available_LSUs(neighbors: list):
    return sum(n.farm_size for n in neighbors)


def calculate_biogas_plant_return(type, capacity, num_years=20):
    # could also add in maintenance, etc.
    if type == BiogasPlant.SMALL:
        return capacity * 0.27 * num_years
    elif type == BiogasPlant.MEDIUM:
        return capacity * 0.25 * num_years
    elif type == BiogasPlant.LARGE:
        return capacity * 0.22 * num_years


class BiogasPlant(Agent):
    """
    A biogas plant agent that provides payments to its owner.
    """

    SMALL = 1
    MEDIUM = 2
    LARGE = 3

    MIN_SIZE = 75
    MAX_SIZE = 850

    def __init__(self, model, owner, capacity):
        """
        Initialize a BiogasPlant agent.

        Args:
            model: The model instance
            capacity: Capacity of the biogas plant
        """
        super().__init__(model)
        assert BiogasPlant.MIN_SIZE <= capacity <= BiogasPlant.MAX_SIZE, (
            "Biogas plant capacity must be between "
            f"{BiogasPlant.MIN_SIZE} and {BiogasPlant.MAX_SIZE} LSUs."
        )
        self.capacity = capacity
        self.owner = owner
        self.plant_type = self.get_size()

    def get_size(self):
        if self.capacity <= 100:
            return BiogasPlant.SMALL
        elif self.capacity <= 600:
            return BiogasPlant.MEDIUM
        else:
            return BiogasPlant.LARGE

    def get_stipend(self):
        if self.plant_type == BiogasPlant.SMALL:
            return 0.27 * self.capacity
        elif self.plant_type == BiogasPlant.MEDIUM:
            return 0.25 * self.capacity
        else:
            return 0.22 * self.capacity

    def step(self):
        """
        Execute one step of the agent's behavior.
        """
        self.owner.money_received += self.get_stipend()
