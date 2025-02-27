# Population Evolution Simulation

This project simulates the evolution of a population based on various genetic, environmental, and competitive factors. The simulation includes agents with traits such as eye color, hair color, height, fitness, and nationality. It models reproduction, survival, selection pressure, and competitive interactions among agents.

## Features
- **Agent Traits:** Each agent has gender, eye color, hair color, height, fitness, skin color, and nationality.
- **Genetic Background:** Agents inherit traits and genetic background from their parents.
- **Reproduction:** Agents mate, producing offspring with inherited and sometimes mutated traits.
- **Natural Selection:** Agents can die due to hazardous traits or competitive disadvantages.
- **Competitive Interactions:** Male agents may fight, and females choose mates based on preferences.
- **Simulation Statistics:** The program tracks population size, average fitness, height, and distribution of traits.

## Installation
This project requires Python and `matplotlib` for visualization. Install dependencies with:
```sh
pip install matplotlib
```

## Usage
Run the simulation with:
```sh
python simulation.py
```
Modify the parameters inside `run_simulation()` to change the number of generations and initial population size.

## Code Overview
### `Agent` Class
Represents an individual in the population with inherited and randomly assigned traits.

### `create_random_agent()`
Generates an agent with random attributes.

### `reproduce(female, male)`
Handles reproduction, producing offspring based on parental traits.

### `forced_trait_death(agent)`
Determines if an agent dies due to hazardous traits.

### `male_fights(population)`
Simulates fights between male agents, where weaker males may be eliminated.

### `run_simulation(generations, initial_population_size)`
Runs the simulation for the specified number of generations, applying selection, reproduction, and competitive interactions.

## Example Output
```
=== Generation 1 ===
> Female 3 chose Male 7.
> Male fight: Agent 5 vs Agent 8 – Agent 8 loses!
Population at end of Generation 1: 45
New Offspring: 12
Average Fitness: 75.2
```

## Visualization
The program collects statistical data that can be plotted using `matplotlib` to analyze trends in population fitness, height, and genetic diversity over generations.

## Future Improvements
- Implement more environmental factors affecting survival.
- Add different selection pressures for traits.
- Improve visualization for better insights into population trends.

## License
This project is licensed under the MIT License.
