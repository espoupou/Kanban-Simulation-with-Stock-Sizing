import csv
import random
import time
import os
import matplotlib.pyplot as plt

# Constants
csv_filename = "simulation_results.csv"
SHIFT_DURATION = 8 * 60 * 60  # 8 hours in seconds
stock_stop_time = 1
safety_factor = 0.3

PROCESSING_TIMES = {
    "cutting": lambda: random.uniform(100, 115),  # 1m45s mean time
    "folding": lambda: random.uniform(38, 45),  # 40s
    "bonding": lambda: random.uniform(20, 25),  # 20s - 25s
    "labeling": lambda: random.uniform(5, 10)  # 5s - 10s
}

STOCK_THRESHOLDS = {
    "full": 100,
    "green": 60,  # >60% stock
    "yellow": 30,  # 30%-60% stock triggers Kanban
    "red": 0  # <30% stock
}

# Initial Stock Levels (in units, can be adjusted)
produced_stock = {
    "cutting": 0,
    "folding": 0,
    "bonding": 0,
    "labeling": 0
}

# basic set
resource_stock = {
    "cutting": float('inf'),  # Infinite resource for cutting
    "folding": 0,
    "bonding": 0,
    "labeling": 0
}

lead_times = {
    "cutting": PROCESSING_TIMES["cutting"]() + 1,
    "folding": PROCESSING_TIMES["folding"]() + 1,
    "bonding": PROCESSING_TIMES["bonding"]() + 1,
    "labeling": PROCESSING_TIMES["labeling"]() + 1
}

# Simulation parameters
kanban_cards = {"cutting": 0, "folding": 0, "bonding": 0, "labeling": 0}
processing_timers = {post: 0 for post in PROCESSING_TIMES}
last_processed_time = {post: time.time() for post in PROCESSING_TIMES}
optimal_stock = {}


# Functions
def process_item(post):
    """
    Simulate processing an item at a specific post.
    """
    global produced_stock, resource_stock, kanban_cards, last_processed_time, stock_stop_time

    current_time = time.time()
    elapsed_time = current_time - last_processed_time[post]

    # Check if enough resource stock is available
    if resource_stock[post] <= 0:
        print(f":{post}::Resource Out Of Stock::")
        # brutal stop
        stock_stop_time = 0
    elif elapsed_time >= PROCESSING_TIMES[post]():
        last_processed_time[post] = current_time  # Reset timer
        resource_stock[post] -= 1  # Used one unit of resource stock
        produced_stock[post] += 1  # Add one unit to produced stock

    # Handle stock movement to the next post
    if post != "labeling":
        next_post = list(PROCESSING_TIMES.keys())[list(PROCESSING_TIMES.keys()).index(post) + 1]
        needed_stock = STOCK_THRESHOLDS["full"] - resource_stock[next_post]
        if kanban_cards[next_post] != 0 and produced_stock[post] >= 0:
            to_send = needed_stock if needed_stock <= produced_stock[post] else produced_stock[post]
            if needed_stock <= produced_stock[post]:
                kanban_cards[next_post] = 0
            produced_stock[post] -= to_send
            resource_stock[next_post] += to_send

    # Check stock levels for Kanban
    if resource_stock[post] <= STOCK_THRESHOLDS["green"] * optimal_stock[post]:
        kanban_cards[post] = 1


def write_to_csv(filename, elapsed_time):
    """
    Write the current simulation state to a CSV file.
    """
    with open(filename, mode="a", newline="") as file:
        writer = csv.writer(file)
        row = [elapsed_time]
        for post in PROCESSING_TIMES.keys():
            row.extend([produced_stock[post], resource_stock[post]])
        row.extend([kanban_cards["cutting"], kanban_cards["folding"],
                    kanban_cards["bonding"], kanban_cards["labeling"]])
        writer.writerow(row)


def simulate_shift(optimal_stock_copy):
    """
    Simulate an 8-hour shift in pull mode.
    """
    global optimal_stock
    optimal_stock = optimal_stock_copy
    start_time = time.time()
    elapsed_time = 0

    # Initialize CSV file with a header
    if os.path.exists(csv_filename):
        os.remove(csv_filename)

    with open(csv_filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "Cutting_Produced", "Cutting_Resource",
                         "Folding_Produced", "Folding_Resource",
                         "Bonding_Produced", "Bonding_Resource",
                         "Labeling_Produced", "Labeling_Resource",
                         "Kanban_Cutting", "Kanban_Folding",
                         "Kanban_Bonding", "Kanban_Labeling"])

    # Initialize dynamic plot
    plt.ion()
    fig, ax = plt.subplots()
    time_data = []
    stock_data = {post: [] for post in resource_stock.keys()}

    while elapsed_time < SHIFT_DURATION and stock_stop_time:
        for post in PROCESSING_TIMES.keys():
            process_item(post)
            stock_data[post].append(resource_stock[post])
            print(f"{post} {produced_stock[post]}:{resource_stock[post]}", end=" | ")

        elapsed_time = time.time() - start_time
        print(f"{elapsed_time}\nKanban Cards: {kanban_cards}")
        time_data.append(elapsed_time)

        # Update plot
        ax.clear()
        for post, stock in stock_data.items():
            ax.plot(time_data, stock, label=f"{post.capitalize()} Stock")
        ax.set_title("Stock Levels Over Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Stock Level")
        ax.legend()
        plt.pause(0.1)  # Pause to update the plot

        write_to_csv(csv_filename, elapsed_time)
        time.sleep(1)

        if all(resource_stock[post] <= 0 for post in PROCESSING_TIMES.keys()):
            print("Simulation stopped: All stocks exhausted.")
            break

    # Finalize plot
    plt.ioff()
    plt.show()

    # Output results
    print("Simulation complete!")
    print(f"Final Produced Stock: {produced_stock}")
    print(f"Final Resource Stock: {resource_stock}")
    print(f"Kanban Cards Triggered: {kanban_cards}")
