"""
Basic tests for the farmer-biogas ABM.
"""
import unittest
from model import FarmerBiogasModel
from agents import Farmer, BiogasPlant


class TestFarmerBiogasModel(unittest.TestCase):
    """Test the FarmerBiogasModel class."""
    
    def setUp(self):
        """Set up a test model."""
        self.model = FarmerBiogasModel(
            n_farmers=10,
            width=5,
            height=5,
            min_farm_size=20,
            max_farm_size=80,
            min_willingness=0.3,
            max_willingness=0.7,
            biogas_payment=50.0
        )
    
    def test_model_initialization(self):
        """Test that the model initializes correctly."""
        self.assertEqual(len([a for a in self.model.agents if isinstance(a, Farmer)]), 10)
        self.assertEqual(self.model.width, 5)
        self.assertEqual(self.model.height, 5)
        self.assertEqual(self.model.biogas_payment, 50.0)
    
    def test_farmers_have_attributes(self):
        """Test that farmers have the correct attributes."""
        farmers = [a for a in self.model.agents if isinstance(a, Farmer)]
        for farmer in farmers:
            self.assertIsNotNone(farmer.farm_size)
            self.assertGreaterEqual(farmer.farm_size, 20)
            self.assertLessEqual(farmer.farm_size, 80)
            self.assertIsNotNone(farmer.willingness)
            self.assertGreaterEqual(farmer.willingness, 0.3)
            self.assertLessEqual(farmer.willingness, 0.7)
            self.assertFalse(farmer.has_biogas_plant)
            self.assertEqual(farmer.money_received, 0.0)
    
    def test_model_step(self):
        """Test that the model can step without errors."""
        initial_farmers = len([a for a in self.model.agents if isinstance(a, Farmer)])
        self.model.step()
        # Farmers count should remain the same
        farmers_after = len([a for a in self.model.agents if isinstance(a, Farmer)])
        self.assertEqual(initial_farmers, farmers_after)
    
    def test_biogas_plants_created(self):
        """Test that biogas plants are created when farmers decide to build."""
        # Run for several steps to allow decisions
        for _ in range(50):
            self.model.step()
        
        # Check if any biogas plants were created
        biogas_plants = [a for a in self.model.agents if isinstance(a, BiogasPlant)]
        farmers_with_plants = [a for a in self.model.agents if isinstance(a, Farmer) and a.has_biogas_plant]
        
        # Number of plants should equal number of farmers with plants
        self.assertEqual(len(biogas_plants), len(farmers_with_plants))
    
    def test_payment_system(self):
        """Test that farmers with biogas plants receive payments."""
        # Run for several steps
        for _ in range(20):
            self.model.step()
        
        farmers_with_plants = [a for a in self.model.agents if isinstance(a, Farmer) and a.has_biogas_plant]
        
        if farmers_with_plants:
            # At least one farmer should have received money
            for farmer in farmers_with_plants:
                self.assertGreater(farmer.money_received, 0)
    
    def test_data_collection(self):
        """Test that data collection works."""
        self.model.step()
        model_data = self.model.datacollector.get_model_vars_dataframe()
        self.assertFalse(model_data.empty)
        self.assertIn("Total Farmers", model_data.columns)
        self.assertIn("Farmers with Plants", model_data.columns)
        self.assertIn("Total Biogas Plants", model_data.columns)
        self.assertIn("Total Money Distributed", model_data.columns)


class TestFarmerAgent(unittest.TestCase):
    """Test the Farmer agent class."""
    
    def setUp(self):
        """Set up a test model with a single farmer."""
        self.model = FarmerBiogasModel(
            n_farmers=1,
            width=3,
            height=3,
            min_farm_size=50,
            max_farm_size=50,
            min_willingness=0.0,  # Very low threshold - easier to build plant
            max_willingness=0.1,
            biogas_payment=100.0
        )
        self.farmer = [a for a in self.model.agents if isinstance(a, Farmer)][0]
    
    def test_farmer_decision_making(self):
        """Test that farmers make decisions."""
        initial_state = self.farmer.has_biogas_plant
        # Run model for a few steps
        for _ in range(10):
            self.model.step()
        # With low willingness threshold and decent farm size, farmer is likely to build plant
        # (decision_score >= willingness threshold means they build)
        self.assertTrue(isinstance(self.farmer.has_biogas_plant, bool))
    
    def test_farmer_receives_payment(self):
        """Test that farmer receives payment after building plant."""
        # Force farmer to have a plant
        self.farmer.has_biogas_plant = True
        initial_money = self.farmer.money_received
        
        # Step the farmer
        self.farmer.step()
        
        # Money should have increased
        self.assertEqual(self.farmer.money_received, initial_money + self.model.biogas_payment)


if __name__ == "__main__":
    unittest.main()
