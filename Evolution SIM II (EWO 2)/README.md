This piece of software does not imply or promote any malicious intentions whatsoever that could be falsely justified/claimed by any individual/organization/company/government and such in any field of crime.

This code simulates an evolutionary population model where agents (humans) are created, reproduce, and are subjected to natural selection based on certain traits like fitness, height, and genetic background. Here's a breakdown of its key components:

1. Traits and Global Constants
The simulation defines traits such as eye color, hair color, skin color, height, and nationality.
Nationalities have different strength factors, affecting an agent's fitness.
Agents can be male or female, with different attributes and reproductive roles.

3. The Agent Class
Defines individuals in the simulation with attributes like:
ID, gender, eye color, hair color, height, fitness, nationality, age, cooldown (for females), and genetic background.
Females have beauty ratings and mate preferences (e.g., favoring height or eye color).
Males have a limited number of mating opportunities per generation (monogamy for low-rank males, polygamy ~ trio for top ranking males). 

5. Fitness & Selection Functions
effective_fitness(agent): Computes fitness based on nationality strength.
is_pure(agent): Checks if an agent is 100% of one nationality.
get_pure_nationality(agent): Returns the nationality if pure.

7. Creating & Reproducing Agents
create_random_agent(): Generates agents with random traits.
reproduce(female, male): Simulates offspring creation with:
Trait inheritance with mutation probability (5%).
Height influenced by parents' height + fitness.
Fitness slightly mutated.
Nationality inherited or mixed.
Genetic background averaged from parents.
1-2 children per mating event.

9. Natural Selection
forced_trait_death(agent): Some traits have survival disadvantages:
Brown eyes: 20% chance of dying.
Dark skin: 33% chance of dying.
Height below 160 cm: 25% chance of dying.
Low fitness: 15% chance of dying.
male_fights(population): Simulates male-male combat, where weaker males may die (15% chance per fight).
Bottom 10% of the population (lowest effective fitness) are removed each generation.

11. Mate Selection
get_preferred_male(female, available_males): Determines the best male for a female based on her preferences.
get_top_two_males(female, available_males): High-beauty females trigger male contests, where the winner mates.
Pure females (90% probability) prefer pure males of the same nationality.

13. Running the Simulation
run_simulation(generations, initial_population_size):
Ages agents.
Reduces female cooldown.
Removes agents that die from trait-based hazards.
Simulates fights between males.
Mates eligible males & females to produce offspring.
Tracks statistics (population size, fitness, height, colors, nationalities).
Prints details about the population.
