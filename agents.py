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
        self.max_willingness_to_build = (
            self.base_willingness_to_build + self.random.uniform(0.1, 0.4)
        )
        self.max_willingness_to_build = min(1.0, self.max_willingness_to_build)

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
                self.max_willingness_to_build,
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
                # number of owners = this farmer + the contributors
                n_owners = 1 + len(contributing_neighbors)

                # simple assumption: annual maintenance ~ 3% of capex
                plant_capex = BiogasPlant.get_plant_cost(available_lsus)
                annual_maintenance = 0.03 * plant_capex

                util = calculate_utility(
                    plant_capacity=available_lsus,
                    farmer_farm_size=self.farm_size,
                    maintenance_costs=annual_maintenance,
                    maintenance_interval=1,
                    n_owners=n_owners,
                    plant_lifetime_years=self.model.plant_lifetime_years,
                    discount_rate=self.model.discount_rate,
                    co_owner_penalty=self.model.co_owner_penalty,
                    profit_scale_chf=self.model.profit_scale_chf,
                    biogas_payment_shift=self.model.biogas_payment_shift,
                )

                # 1) hard cutoff: don't build if utility is “too bad”
                if util < self.model.utility_min_threshold:
                    return

                # 2) translate utility into an additional probability
                #    (sigmoid: negative utility -> low probability, positive -> high probability)
                p_utility = 1.0 / (
                    1.0 + math.exp(-self.model.utility_sensitivity * util)
                )

                # combine willingness and utility (multiplicative)
                assert (
                    1.0 >= self.willingness_to_build >= 0.0
                ), "Willingness must be in [0,1]"
                p_final = p_utility * self.willingness_to_build

                if self.random.random() < p_final:
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
                mark_neighbors_as_contributors(contributing_neighbors, self.model)

    def build_biogas_plant(self, capacity, contributing_neighbors):
        plant = BiogasPlant(self.model, self, contributing_neighbors, capacity)
        self.model.grid.place_agent(plant, self.pos)

        self.has_biogas_plant = True
        self.contributes_to_biogas_plant = True
        self.biogas_plant = plant

        current_time = self.model.time
        assert self.time_of_adoption is None, "Farmer is already an adopter!"
        self.time_of_adoption = current_time
        mark_neighbors_as_contributors(contributing_neighbors, self.model)


def calculate_utility(
    plant_capacity: float,  # in lsu
    farmer_farm_size: float,  # in lsu
    maintenance_costs: float,  # every x years in chf
    maintenance_interval: int,  # in years
    n_owners: int,
    plant_lifetime_years: int = 20,
    discount_rate: float = 0.04,
    co_owner_penalty: float = 0.1,  # percentage reduction in utility per co-owner
    profit_scale_chf: float = 100000.0,
    biogas_payment_shift: float = 0.0,
):

    if plant_capacity <= 0 or farmer_farm_size <= 0:
        return -1e9

    # annual energy and revenue
    kw = BiogasPlant.get_kw(plant_capacity)
    annual_kwh = kw * 24 * 365
    annual_revenue_total = annual_kwh * (
        BiogasPlant.get_stipend(plant_capacity) + biogas_payment_shift
    )

    # investment costs
    plant_capex_chf = BiogasPlant.get_plant_cost(plant_capacity)

    # maintenance
    annual_maintenance_total = maintenance_costs / float(max(1, maintenance_interval))

    # farmer's share of capacity
    share_this_farm = farmer_farm_size / plant_capacity
    share_this_farm = max(0.0, min(1.0, share_this_farm))

    # annual net cash-flow for this farmer
    annual_profit_for_farmer = share_this_farm * (
        annual_revenue_total - annual_maintenance_total
    )

    # npv calculation
    # farmer has to pay their share of initial costs at t=0
    # receive discounted annual profits for the plant lifetime
    capex_share_for_farmer = plant_capex_chf / float(max(1, n_owners))
    npv = -capex_share_for_farmer

    for years in range(1, plant_lifetime_years + 1):
        npv += annual_profit_for_farmer / ((1.0 + discount_rate) ** years)

    # converting npv (chf) to utility (dimensionless)
    utility_profit = npv / profit_scale_chf

    # adding a penalty for co-owners (since sharing reduces control, etc.)
    utility_co_owners = -co_owner_penalty * float(max(0, n_owners - 1))

    total_utility = utility_profit + utility_co_owners
    return total_utility


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


def mark_neighbors_as_contributors(contributing_neighbors: list, model):
    for neighbor in contributing_neighbors:
        assert neighbor.time_of_adoption is None, "Neighbor is already a contributor!"
        neighbor.contributes_to_biogas_plant = True
        neighbor.time_of_adoption = model.time
        model.grid.remove_agent(neighbor)


def get_available_LSUs(neighbors: list):
    return sum(n.farm_size for n in neighbors)


class BiogasPlant(Agent):
    """
    A biogas plant agent that provides payments to its owner.
    """

    SMALL = 1
    MEDIUM = 2
    LARGE = 3

    MIN_SIZE = 75
    MAX_SIZE = 850

    # source: https://www.euki.de/wp-content/uploads/2021/03/Brochure_Biogas-Initiative_WEB.pdf
    KW_PER_LSU = 18 / 100  # 18 kW per 100 LSUs

    # True is how it's defined in plant pricing references
    # False does interpolation for any size
    USE_PIECEWISE_COST_FUNCTION = True

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

    @staticmethod
    def get_size(capacity):
        # This is defined by the paper in Sandrine's group
        # But we could also define based on kW instead
        if capacity <= 100:
            return BiogasPlant.SMALL
        elif capacity <= 600:
            return BiogasPlant.MEDIUM
        else:
            return BiogasPlant.LARGE

    @staticmethod
    def get_kw(capacity):
        # source: https://www.euki.de/wp-content/uploads/2021/03/Brochure_Biogas-Initiative_WEB.pdf
        # large plants are 30% relatively more efficient
        default_kw = capacity * BiogasPlant.KW_PER_LSU
        factor = (default_kw - 75) / (1000 - 75)
        if BiogasPlant.USE_PIECEWISE_COST_FUNCTION:
            factor = max(0.0, min(1.0, factor))
        return default_kw * (1 + 0.3 * factor)

    @staticmethod
    def get_plant_cost(capacity):
        # source: https://www.dvl.org/uploads/tx_ttproducts/datasheet/DVL-Publikation-Schriftenreihe-22_Vom_Landschaftspflegematerial_zum_Biogas-ein_Beratungsordner.pdf
        # # piecewise function, as plants get cheaper once larger than 75 kW
        if BiogasPlant.USE_PIECEWISE_COST_FUNCTION:
            default_price_per_kw = 9000
            factor = (BiogasPlant.get_kw(capacity) - 75) / (150 - 75)
            factor = max(0.0, min(1.0, factor))
            return (9000 - factor * (9000 - 6500)) * BiogasPlant.get_kw(capacity)
        else:
            # experimenting here with linear function
            cost_per_kw = 11500 - BiogasPlant.get_kw(capacity) * 2500 / 75
            return cost_per_kw * BiogasPlant.get_kw(capacity)

    @staticmethod
    def get_stipend(capacity):
        if BiogasPlant.get_kw(capacity) <= 50:
            return 0.27
        elif BiogasPlant.get_kw(capacity) <= 100:
            return 0.25
        else:
            return 0.22

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

    def get_color(self):
        if self.plant_type == BiogasPlant.SMALL:
            return "purple"
        elif self.plant_type == BiogasPlant.MEDIUM:
            return "orange"
        else:
            return "red"

    def step(self):
        self.owner.money_received += (
            (self.get_stipend(self.capacity) + self.model.biogas_payment_shift)
            * self.get_kw(self.capacity)
            * 24
            * 365
        )
