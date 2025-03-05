# Delivery Simulation with Truck Management System

This is a simulation of a delivery system with multiple trucks managing customer orders. The system handles order processing, truck assignments, and includes features such as truck breakdowns, late delivery penalties, and dynamic truck purchase based on revenue.

## Features
- **Order Management**: Orders are randomly generated with prices and distances. The system prioritizes orders based on their age and price.
- **Truck Management**: Trucks deliver orders and earn revenue. They can break down randomly, and repairs are handled with a time cost.
- **Penalty System**: If a customer waits more than 5 iterations (turns), a penalty fee is applied and deducted from the overall revenue.
- **Dynamic Fleet Growth**: New trucks are purchased automatically based on total revenue.
- **Real-Time Visualization**: The simulation displays the current status of orders, deliveries, and trucks using `matplotlib` for real-time updates.

## Requirements
- Python 3.x
- Required Python libraries:
  - `random`
  - `time`
  - `heapq`
  - `math`
  - `matplotlib`
  
