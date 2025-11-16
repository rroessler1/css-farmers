"""
Agent classes for the farmer-biogas ABM.
"""

from enum import Enum
from mesa import Agent
import math


class Farmer(Agent):
    """
    A farmer agent that decides whether to build a biogas plant.
    ...
    """

    def __init__(
        self, model, farm_size, willingness_to_build, willingness_to_contribute
    ):
        """
        Initialize a Farmer agent.
        ...
        """
        super().__init__(model)
        self.farm_size = farm_size

        # store initial values (reluctance at t=0)
        self.base_willingness_to_build = willingness_to_build
        self.base_willingness_to_contribute = willingness_to_contribute

        # these will be updated over time
        self.willingness_to_build = willingness_to_build
        self.willingness_to_contribute = willingness_to_contribute

        # *** VERBESSERUNG: Lese Gewichte aus dem Modell ***
        # Ermöglicht Sensitivitätsanalysen
        self.weight_global_build = self.model.weight_global_build
        self.weight_social_build = self.model.weight_social_build
        self.weight_global_contribute = self.model.weight_global_contribute
        self.weight_social_contribute = self.model.weight_social_contribute

        self.time_of_adoption = None  # record when this farmer first adopts

        self.has_biogas_plant = False
        self.contributes_to_biogas_plant = False
        self.biogas_plant = None
        self.money_received = 0.0

    def step(self):
        """
        Execute one step of the agent's behavior.
        """
        if self.has_biogas_plant:
            self._decide_whether_to_upgrade_biogas_plant()
            return

        # Wenn der Bauer schon Teil einer Anlage ist, muss er nichts mehr tun.
        # (Er wird aber noch von anderen als Nachbar "gesehen")
        if self.contributes_to_biogas_plant:
            return

        # 1) update trust / willingness based on time and neighbors
        self._update_adoption_and_learning()

        # 2) then make the decision with the updated willingness
        # (self.contributes_to_biogas_plant ist hier immer False)
        self._decide_whether_to_build_biogas_plant()

    def _update_adoption_and_learning(self):
        """Update willingness_to_build / contribute via time-based and social learning."""

        # --- 1. Global learning over time (same for all farmers) ---

        # *** VERBESSERUNG: Nutze Standard Mesa Scheduler Zeit ***
        t = self.model.time
        k = self.model.learning_rate
        t0 = self.model.learning_midpoint

        global_learning = 1.0 / (1.0 + math.exp(-k * (t - t0)))  # in [0,1]

        # --- 2. Social learning from neighbors ---
        if self.model.grid:
            neighbors = self.model.grid.get_neighbors(
                self.pos,
                moore=True,
                include_center=False,
                radius=2,  # Annahme: Lerne von Radius 2
            )
            neighbors = [n for n in neighbors if isinstance(n, Farmer)]
        else:
            neighbors = []

        if neighbors:
            adopted_neighbors = [
                n
                for n in neighbors
                if n.has_biogas_plant or n.contributes_to_biogas_plant
            ]
            share_adopted = len(adopted_neighbors) / len(neighbors)
        else:
            share_adopted = 0.0

        # --- 3. Combine baseline reluctance + global + social learning ---
        # clamp everything to [0,1] for safety
        self.willingness_to_build = max(
            0.0,
            min(
                1.0,
                self.base_willingness_to_build
                + self.weight_global_build * global_learning
                + self.weight_social_build * share_adopted,
            ),
        )

        self.willingness_to_contribute = max(
            0.0,
            min(
                1.0,
                self.base_willingness_to_contribute
                + self.weight_global_contribute * global_learning
                + self.weight_social_contribute * share_adopted,
            ),
        )

    def _decide_whether_to_build_biogas_plant(self):
        # (Check auf self.contributes_to_biogas_plant ist jetzt im step(),
        #  also hier nicht mehr nötig)

        # probabilistic adoption: higher willingness -> higher chance this step
        p_adopt = max(0.0, min(1.0, self.willingness_to_build**3))

        if self.random.random() > p_adopt:
            return

        # rest of your capacity / neighbor logic as before
        if self.model.grid:
            neighbors = self.model.grid.get_neighbors(
                self.pos,
                moore=True,
                include_center=False,
                radius=1,  # Annahme: Kooperiere nur mit Radius 1
            )

            # *** VERBESSERUNG: Übergebe Modell-Parameter statt 0.5 ***
            threshold = self.model.contribute_threshold
            contributing_neighbors = get_neighbors_willing_to_contribute(
                neighbors, threshold
            )

            available_lsus = get_available_LSUs(contributing_neighbors) + self.farm_size

            if available_lsus > BiogasPlant.MAX_SIZE:
                contributing_neighbors = sorted(
                    contributing_neighbors, key=lambda x: x.farm_size, reverse=True
                )
                while available_lsus > BiogasPlant.MAX_SIZE and contributing_neighbors:
                    removed_farmer = contributing_neighbors.pop()
                    available_lsus -= removed_farmer.farm_size

            if BiogasPlant.MIN_SIZE <= available_lsus <= BiogasPlant.MAX_SIZE:
                self.build_biogas_plant(available_lsus, contributing_neighbors)

    def _decide_whether_to_upgrade_biogas_plant(self):
        p_adopt = max(0.0, min(1.0, self.willingness_to_build**3))
        if self.random.random() > p_adopt:
            return

        if self.model.grid:
            neighbors = self.model.grid.get_neighbors(
                self.pos,
                moore=True,
                include_center=False,
                radius=1,
            )

            threshold = self.model.contribute_threshold
            contributing_neighbors = get_neighbors_willing_to_contribute(
                neighbors, threshold
            )
            additional_lsus = get_available_LSUs(contributing_neighbors)
            if additional_lsus + self.biogas_plant.capacity > BiogasPlant.MAX_SIZE:
                contributing_neighbors = sorted(
                    contributing_neighbors, key=lambda x: x.farm_size, reverse=True
                )
                while additional_lsus > BiogasPlant.MAX_SIZE and contributing_neighbors:
                    removed_farmer = contributing_neighbors.pop()
                    additional_lsus -= removed_farmer.farm_size

            if self.biogas_plant.can_upgrade(additional_lsus):
                self.biogas_plant.upgrade(additional_lsus, contributing_neighbors)
                mark_neighbors_as_contributors(contributing_neighbors, self.model.time)

    def build_biogas_plant(self, capacity, contributing_neighbors):
        plant = BiogasPlant(self.model, self, contributing_neighbors, capacity)
        self.model.grid.place_agent(plant, self.pos)

        self.has_biogas_plant = True
        self.contributes_to_biogas_plant = True
        self.biogas_plant = plant

        current_time = self.model.time
        assert self.time_of_adoption is None, "Farmer is already an adopter!"
        self.time_of_adoption = current_time
        mark_neighbors_as_contributors(contributing_neighbors, current_time)


def calculate_utility(plant_type, capacity):
    # TODO: should include age and some other factors I guess
    return calculate_biogas_plant_return(plant_type, capacity)


# *** VERBESSERUNG: Nimm Schwellenwert als Argument ***
def get_neighbors_willing_to_contribute(
    neighbors: list, contribute_threshold: float, include_current_contributors=False
):
    neighbors = [n for n in neighbors if isinstance(n, Farmer)]
    return [
        n
        for n in neighbors
        if not n.contributes_to_biogas_plant
        and n.willingness_to_contribute > contribute_threshold
    ]


def mark_neighbors_as_contributors(contributing_neighbors: list, current_time):
    for neighbor in contributing_neighbors:
        assert neighbor.time_of_adoption is None, "Neighbor is already a contributor!"
        neighbor.contributes_to_biogas_plant = True
        neighbor.time_of_adoption = current_time


def get_available_LSUs(neighbors: list):
    return sum(n.farm_size for n in neighbors)


# ... (Rest des Codes bleibt gleich) ...


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

    # ... (Keine Änderungen hier) ...
    SMALL = 1
    MEDIUM = 2
    LARGE = 3

    MIN_SIZE = 75
    MAX_SIZE = 850

    def __init__(self, model, owner, contributors, capacity):
        super().__init__(model)
        assert BiogasPlant.MIN_SIZE <= capacity <= BiogasPlant.MAX_SIZE, (
            "Biogas plant capacity must be between "
            f"{BiogasPlant.MIN_SIZE} and {BiogasPlant.MAX_SIZE} LSUs."
        )
        self.capacity = capacity
        self.owner = owner
        self.contributors = contributors
        self.plant_type = self.get_size(capacity)
        self.num_upgrades = 0

    def can_upgrade(self, additional_capacity):
        return self.get_size(self.capacity + additional_capacity) > self.plant_type

    def upgrade(self, additional_capacity, new_contributors):
        assert self.can_upgrade(
            additional_capacity
        ), "New capacity must be larger to upgrade."
        self.capacity += additional_capacity
        self.contributors = self.contributors + new_contributors
        self.plant_type = self.get_size(self.capacity)
        self.num_upgrades += 1

    def get_size(self, capacity):
        if capacity <= 100:
            return BiogasPlant.SMALL
        elif capacity <= 600:
            return BiogasPlant.MEDIUM
        else:
            return BiogasPlant.LARGE

    def get_color(self):
        if self.plant_type == BiogasPlant.SMALL:
            return "purple"
        elif self.plant_type == BiogasPlant.MEDIUM:
            return "orange"
        else:
            return "red"

    def get_stipend(self):
        if self.plant_type == BiogasPlant.SMALL:
            return 0.27 * self.capacity
        elif self.plant_type == BiogasPlant.MEDIUM:
            return 0.25 * self.capacity
        else:
            return 0.22 * self.capacity

    def step(self):
        self.owner.money_received += self.get_stipend()
