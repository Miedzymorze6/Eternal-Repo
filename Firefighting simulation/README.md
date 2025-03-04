
# Forest Fire Simulation with Firefighting Agents

This is a Python-based simulation of a forest fire spreading in a grid, featuring an agent-based firefighting system. The simulation models fire spread with wind, water obstacles, and heat dynamics. Firefighters are deployed to fight the fire, and users can interact with the simulation by placing water patterns (such as square, circle, triangle, or octagon) to help control the fire spread.

## Features

- **Fire Spread Simulation**: The fire spreads based on a probability model, influenced by wind direction and obstacles like water.
- **Heat Simulation**: Heat spreads to nearby cells, potentially causing a tree to ignite.
- **Firefighting Agents**: Agents are deployed around the fire to fight it. They move towards the fire and spray water in their direction.
- **Interactive Pattern Placement**: Users can click on the grid to place patterns (square, circle, triangle, or octagon) of water to influence fire spread.
- **Graphical Display**: The simulation includes a real-time graphical representation of the fire and a line graph showing the number of burned trees over time.

## Requirements

- Python 3.x
- Pygame library
- Numpy library
