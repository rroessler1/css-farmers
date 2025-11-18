"""
Example script to run the farmer-biogas ABM.
"""

from model import FarmerBiogasModel


def run_model(steps=100):
    """
    Run the farmer-biogas model for a specified number of steps.

    Args:
        steps: Number of simulation steps to run
    """
    # Create model with default parameters
    model = FarmerBiogasModel(
        n_farmers=50,
        width=10,
        height=10,
        farm_capacity_shift=0,
        contribute_threshold=0.4,
        biogas_payment=100.0,
    )

    print("Starting Farmer-Biogas ABM Simulation")
    print("=" * 50)
    print(f"Number of farmers: {model.n_farmers}")
    print(f"Grid size: {model.width}x{model.height}")
    print(f"Biogas payment per step: ${model.biogas_payment}")
    print("=" * 50)

    # Run simulation
    for i in range(steps):
        model.step()

        # Print progress every 10 steps
        if (i + 1) % 10 == 0:
            model_data = model.datacollector.get_model_vars_dataframe()
            last_row = model_data.iloc[-1]
            print(f"\nStep {i + 1}:")
            print(
                f"  Farmers with biogas plants: {int(last_row['Farmers with Plants'])}/{int(last_row['Total Farmers'])}"
            )
            print(f"  Total biogas plants: {int(last_row['Total Biogas Plants'])}")
            print(
                f"  Total money distributed: ${last_row['Total Money Distributed']:.2f}"
            )

    # Final summary
    print("\n" + "=" * 50)
    print("Simulation Complete!")
    print("=" * 50)

    model_data = model.datacollector.get_model_vars_dataframe()
    agent_data = model.datacollector.get_agent_vars_dataframe()

    # Final statistics
    final_row = model_data.iloc[-1]
    print(f"\nFinal Statistics:")
    print(f"  Total farmers: {int(final_row['Total Farmers'])}")
    print(
        f"  Farmers with plants: {int(final_row['Farmers with Plants'])} ({int(final_row['Farmers with Plants'])/int(final_row['Total Farmers'])*100:.1f}%)"
    )
    print(f"  Total biogas plants: {int(final_row['Total Biogas Plants'])}")
    print(f"  Total money distributed: ${final_row['Total Money Distributed']:.2f}")

    # Show some individual farmer data
    if not agent_data.empty:
        final_step = agent_data.index.get_level_values("Step").max()
        final_agents = agent_data.xs(final_step, level="Step")
        farmers_data = final_agents[final_agents["Farm Size"].notna()]

        if not farmers_data.empty:
            print(f"\nSample Farmer Statistics:")
            print(f"  Average farm size: {farmers_data['Farm Size'].mean():.1f}")
            print(f"  Average willingness: {farmers_data['Willingness'].mean():.2f}")
            print(
                f"  Average money received: ${farmers_data['Money Received'].mean():.2f}"
            )

    return model


if __name__ == "__main__":
    run_model(steps=100)
