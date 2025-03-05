import random
import time
import heapq
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# --- Data Classes ---

class Order:
    def __init__(self, customer_id, price, timestamp, distance):
        self.customer_id = customer_id
        self.price = price
        self.timestamp = timestamp  
        self.distance = distance    
        self.wait_iterations = 0    
        self.penalized = False      

    def __lt__(self, other):
        if self.price == other.price:
            return self.timestamp < other.timestamp
        return self.price > other.price  

    def __repr__(self):
        return (f"(Cust:{self.customer_id}, ${self.price}, "
                f"d:{self.distance}, wait:{self.wait_iterations})")

class Truck:
    def __init__(self, truck_id):
        self.truck_id = truck_id
        self.total_earnings = 0  
        self.mat = 0            
        self.is_broken = False  
        self.repair_time = 0    

    def update_earnings(self, price):
        self.total_earnings += price
        new_mat = (self.total_earnings // 500) * 5
        if new_mat > self.mat:
            self.mat = new_mat

    def deduct_gas(self, cost=20):
        self.total_earnings -= cost

    def break_down(self):
        """Chance for truck to break down randomly."""
        if random.random() < 0.05:  # 5% chance per iteration
            self.is_broken = True
            self.repair_time = random.randint(3, 10)  # Repair takes 3 to 10 iterations

    def repair(self):
        """Repair the truck after a few iterations."""
        if self.is_broken and self.repair_time > 0:
            self.repair_time -= 1
            if self.repair_time == 0:
                self.is_broken = False  # Truck is repaired
                self.repair_time = 0

    def __repr__(self):
        return f"Truck {self.truck_id}: Earnings=${self.total_earnings}, MAT={self.mat}, Broken={self.is_broken}"


# --- Simulation Variables ---

orders_heap = []  
active_deliveries = []  
trucks = [Truck(truck_id=i) for i in range(1, 11)]  
assignment_index = 0  

# --- Order Generation ---

def generate_orders(num_orders):
    """Generate a number of orders with random price and distance."""
    orders = []
    current_time = time.time()
    for _ in range(num_orders):
        price = random.randint(50, 1000)
        distance = random.randint(1, 4)
        customer_id = random.randint(1, 100)
        order_time = current_time + random.random()  
        orders.append(Order(customer_id, price, order_time, distance))
    return orders

# --- Visualization Setup ---

fig, axes = plt.subplots(3, 1, figsize=(10, 12))
ax_orders, ax_active, ax_trucks = axes

ax_orders.set_title("Waiting Orders Queue")
ax_active.set_title("Active Deliveries")
ax_trucks.set_title("Trucks Status")

orders_text = ax_orders.text(0.02, 0.5, "", fontsize=8, va="center", transform=ax_orders.transAxes)
active_text = ax_active.text(0.02, 0.5, "", fontsize=8, va="center", transform=ax_active.transAxes)
trucks_text = ax_trucks.text(0.02, 0.5, "", fontsize=8, va="center", transform=ax_trucks.transAxes)

for ax in axes:
    ax.axis('off')

# --- Global Simulation Variables ---

iteration = 0  

# --- Simulation Update Function ---

# --- Simulation Update Function --- (Modifying this section)
# --- Simulation Update Function --- (Modifying this section)
# --- Simulation Update Function --- (Modifying this section)
def update(frame):
    global iteration, orders_heap, active_deliveries, trucks, assignment_index

    iteration += 1

    # === Process active deliveries ===
    completed = []
    for delivery in active_deliveries:
        delivery['remaining_iters'] -= 1
        if delivery['remaining_iters'] <= 0:
            truck = delivery['truck']
            order = delivery['order']
            truck.update_earnings(order.price)
            completed.append(delivery)
    for delivery in completed:
        active_deliveries.remove(delivery)

    # === Deduct gas cost for all trucks ===
    for truck in trucks:
        truck.deduct_gas(20)

    # === Handle truck breakdowns ===
    for truck in trucks:
        if truck.is_broken:
            truck.repair()  # Start or continue the repair process
        else:
            truck.break_down()  # Check if the truck breaks down

    # === Update waiting orders ===
    temp_orders = []
    priority_orders = []
    late_orders = []  # To track late orders for penalty application
    penalty_total = 0  # Track the total penalty amount to deduct from revenue

    for order in orders_heap:
        order.wait_iterations += 1
        if order.wait_iterations >= 5:  # If order has waited more than 5 iterations
            penalty_fee = 0.2 * order.price  # Example: 20% penalty of the order price
            penalty_total += penalty_fee  # Add penalty fee to the total penalty amount
            order.penalized = True  # Mark as penalized
            late_orders.append(order)  # Add to the late orders list
        elif order.wait_iterations >= 4:
            priority_orders.append(order)
        else:
            temp_orders.append(order)

    # Remove late orders from the heap
    orders_heap = [order for order in orders_heap if order not in late_orders]

    # Re-sort orders, give priority to older orders
    orders_heap = []
    for order in priority_orders + temp_orders + late_orders:
        heapq.heappush(orders_heap, order)

    # === Generate new orders ===
    if len(orders_heap) < 10:
        new_orders_count = min(10 - len(orders_heap), math.ceil(iteration / 2 + 1))
        new_orders = generate_orders(new_orders_count)
        for order in new_orders:
            heapq.heappush(orders_heap, order)

    # === Assign orders to available trucks ===
    for truck in trucks:
        if truck.is_broken:
            continue  # Skip assigning orders to broken trucks

        if any(d['truck'] == truck for d in active_deliveries):
            continue
        if orders_heap:
            order = heapq.heappop(orders_heap)
            active_deliveries.append({
                'truck': truck,
                'order': order,
                'remaining_iters': order.distance
            })

    # === Purchase new truck if needed ===
    total_earnings = sum(truck.total_earnings for truck in trucks)
    required_truck_count = 10 + (total_earnings // 500)
    required_truck_count = min(required_truck_count, 15)

    if len(trucks) < required_truck_count:
        new_truck_id = max(truck.truck_id for truck in trucks) + 1
        trucks.append(Truck(new_truck_id))
        print(f"Purchased new Truck {new_truck_id} at iteration {iteration}.")

    # === Calculate Summary Statistics ===
    total_revenue = sum(truck.total_earnings for truck in trucks) - penalty_total  # Subtract penalties from total revenue
    total_gas_used = iteration * len(trucks) * 20  
    priority_count = sum(1 for order in orders_heap if order.wait_iterations >= 5)

    # === Update Display Text ===
    orders_display = "Waiting Orders:\n" + "\n".join(str(o) for o in sorted(orders_heap, reverse=True))
    active_display = "Active Deliveries:\n" + "\n".join(
        f"Truck {d['truck'].truck_id} delivering {d['order']} (remaining: {d['remaining_iters']})"
        for d in active_deliveries
    )
    trucks_display = "Trucks Status:\n" + "\n".join(str(truck) for truck in trucks)

    summary_display = (f"\nTotal Revenue: ${total_revenue}\n"
                       f"Total Gas Fee: ${total_gas_used}\n"
                       f"Current Priority Orders Delivered: {priority_count}\n"
                       f"Current Iteration Penalty Deducted: ${penalty_total:.2f}")

    orders_text.set_text(orders_display)
    active_text.set_text(active_display)
    trucks_text.set_text(trucks_display + summary_display)

    return orders_text, active_text, trucks_text  # Return should be at the end





# --- Run the Animation ---
ani = animation.FuncAnimation(fig, update, interval=500, blit=False)
plt.show()
