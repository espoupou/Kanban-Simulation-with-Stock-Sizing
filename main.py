from simulation import simulate_shift, SHIFT_DURATION, PROCESSING_TIMES, lead_times, resource_stock, csv_filename
import pandas as pd
import matplotlib.pyplot as plt


def calculate_stock_levels(processing_times, lead_times, safety_factor=0.1):
    """
    Calculate optimal stock levels for each post.

    Args:
        processing_times (dict): Processing times for each post (in seconds).
        lead_times (dict): Lead times for each post (in seconds).
        safety_factor (float): Percentage of daily production to add as safety stock.

    Returns:
        dict: Optimal stock levels for each post.
    """
    stock_levels = {}
    for post, post_time in processing_times.items():
        downstream_time = processing_times.get(next(iter(processing_times.keys())), post_time)()
        demand_rate = 1 / downstream_time                       # Units per second
        lead_time = lead_times.get(post, post_time)             # I set it to 1 sec since next post is just aside
        safety_stock = safety_factor * (demand_rate * SHIFT_DURATION)
        stock_levels[post] = int((demand_rate * lead_time) + safety_stock)
    return stock_levels


if __name__ == "__main__":
    optimal_stock = calculate_stock_levels(PROCESSING_TIMES, lead_times, 0.3)
    print("Optimal Stock Levels:", optimal_stock)
    for post in optimal_stock.keys():
        resource_stock[post] = optimal_stock[post]
    resource_stock["cutting"] = 25

    # Run Simulation
    simulate_shift(optimal_stock)

    data = pd.read_csv(csv_filename)
    data.plot(x="Time", y=["Cutting_Resource", "Folding_Resource", "Bonding_Resource", "Labeling_Resource"])
    plt.title("Stock Levels Over Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Stock Level")
    plt.show()
