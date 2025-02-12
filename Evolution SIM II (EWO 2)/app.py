import random
import matplotlib.pyplot as plt

# Global counter for unique agent IDs.
next_agent_id = 1

# Possible trait values.
EYE_COLORS = ["blue", "green", "brown"]
SKIN_COLORS = ["light", "medium", "dark"]
HAIR_COLORS = ["blonde", "brown", "black"]
NATIONALITIES = ["slavic", "germanic", "uralic-altaic", "latino-romance-greek"]

# Nationality strength factors.
NATIONALITY_STRENGTH = {
    "slavic": 5,
    "germanic": 1.3,
    "uralic-altaic": 1.0,
    "latino-romance-greek": 1.1
}

def effective_fitness(agent):
    """
    Compute an agent’s effective fitness (or "power") by multiplying its raw fitness
    by a weighted average of nationality strength factors (weighted by its genetic background).
    """
    strength = sum(NATIONALITY_STRENGTH[nat] * frac for nat, frac in agent.genetic_background.items())
    return agent.fitness * strength

def is_pure(agent):
    """Return True if the agent is pure (100% one nationality)."""
    for nat, frac in agent.genetic_background.items():
        if abs(frac - 1.0) < 1e-6:
            return True
    return False

def get_pure_nationality(agent):
    """Return the nationality if agent is pure, else None."""
    for nat, frac in agent.genetic_background.items():
        if abs(frac - 1.0) < 1e-6:
            return nat
    return None

class Agent:
    def __init__(self, id, gender, eye_color, hair_color, height, fitness, skin_color, nationality,
                 genetic_background=None, parent_ids=None, age=0, cooldown=0):
        self.id = id
        self.gender = gender  # "M" or "F"
        self.eye_color = eye_color
        self.hair_color = hair_color
        self.nationality = nationality
        self.height = height      # centimeters
        self.fitness = fitness    # points (higher is better)
        self.skin_color = skin_color
        self.parent_ids = parent_ids if parent_ids is not None else []
        self.age = age            # turns lived
        self.cooldown = cooldown  # for females: turns remaining before mating allowed
        
        # Genetic background: if not provided, assume pure.
        if genetic_background is None:
            self.genetic_background = {nationality: 1.0}
        else:
            # Normalize to sum to 1.
            total = sum(genetic_background.values())
            self.genetic_background = {nat: frac/total for nat, frac in genetic_background.items()}
        
        # For males: they start with 1 mating opportunity.
        if self.gender == "M":
            self.mating_opportunities = 1
        # For females: add extra traits.
        else:
            self.beauty = random.randint(1, 5)
            # "blue" now means she likes males with blue eyes or blond hair.
            self.preference = random.choice(["green", "height", "light","germanic"])

    def __repr__(self):
        # Format genetic background as percentages.
        bg_str = ", ".join(f"{nat}:{int(frac*100)}%" for nat, frac in self.genetic_background.items())
        base = (f"Agent(id={self.id}, gender={self.gender}, eye_color={self.eye_color}, "
                f"hair_color={self.hair_color}, nationality={self.nationality} [{bg_str}], "
                f"height={self.height:.1f}, fitness={self.fitness:.1f}, skin_color={self.skin_color}, "
                f"age={self.age}, cooldown={self.cooldown}, parents={self.parent_ids})")
        if self.gender == "F":
            return base + f", beauty={self.beauty}, preference={self.preference})"
        else:
            return base + f", mating_opps={self.mating_opportunities})"

def create_random_agent():
    """Create an agent with random traits (including hair color, nationality, and a pure genetic background)."""
    global next_agent_id
    gender = random.choice(["M", "F"])
    eye_color = random.choice(EYE_COLORS)
    hair_color = random.choice(HAIR_COLORS)
    height = random.uniform(150, 200)      # 150-200 cm
    fitness = random.uniform(50, 100)        # 50-100 points
    skin_color = random.choice(SKIN_COLORS)
    nationality = random.choice(NATIONALITIES)
    genetic_background = {nationality: 1.0}  # Starter agents are pure.
    agent = Agent(
        id=next_agent_id,
        gender=gender,
        eye_color=eye_color,
        hair_color=hair_color,
        nationality=nationality,
        height=height,
        fitness=fitness,
        skin_color=skin_color,
        genetic_background=genetic_background,
        parent_ids=[],
        age=0,
        cooldown=0
    )
    next_agent_id += 1
    return agent

def reproduce(female, male):
    """
    Produce offspring from a mating pair.
    - Each reproduction event produces either 1 or 2 children.
    - Child's height is the average of the parents' heights plus half the average fitness plus noise.
    - Child's fitness is the average parent's fitness plus a slight mutation.
    - Traits (eye, skin, hair colors) are inherited (with a chance of mutation).
    - The child's genetic background is the average of the parents' genetic backgrounds.
    - If parents are pure and of the same nationality, the child inherits that nationality;
      if not, the child's nationality field is chosen randomly from the parents (mixed marriage).
    """
    global next_agent_id
    offspring = []
    num_offspring = random.randint(1, 2)

    for _ in range(num_offspring):
        avg_height = (female.height + male.height) / 2
        avg_fitness = (female.fitness + male.fitness) / 2
        child_height = avg_height + (avg_fitness * 0.5) + random.gauss(0, 2)
        child_fitness = (female.fitness + male.fitness) / 2 + random.gauss(0, 5)
        
        # Inherit eye color (with 5% chance of mutation).
        child_eye_color = random.choice([female.eye_color, male.eye_color])
        if random.random() < 0.05:
            child_eye_color = random.choice(EYE_COLORS)
            
        # Inherit skin color (with 5% chance of mutation).
        child_skin_color = random.choice([female.skin_color, male.skin_color])
        if random.random() < 0.05:
            child_skin_color = random.choice(SKIN_COLORS)
            
        # Inherit hair color.
        child_hair_color = random.choice([female.hair_color, male.hair_color])
        if random.random() < 0.05:
            child_hair_color = random.choice(HAIR_COLORS)
            
        # Determine child's nationality.
        if female.nationality == male.nationality:
            child_nationality = female.nationality
        else:
            child_nationality = random.choice([female.nationality, male.nationality])
            
        # Compute child's genetic background as the average of the parents'.
        child_genetic_background = {}
        for nat in NATIONALITIES:
            child_genetic_background[nat] = (female.genetic_background.get(nat, 0) +
                                             male.genetic_background.get(nat, 0)) / 2

        child_gender = random.choice(["M", "F"])

        child = Agent(
            id=next_agent_id,
            gender=child_gender,
            eye_color=child_eye_color,
            hair_color=child_hair_color,
            nationality=child_nationality,
            height=child_height,
            fitness=max(0, child_fitness),
            skin_color=child_skin_color,
            genetic_background=child_genetic_background,
            parent_ids=[female.id, male.id],
            age=0,
            cooldown=0
        )
        next_agent_id += 1
        offspring.append(child)
    return offspring

def forced_trait_death(agent):
    """
    Returns True if the agent dies due to hazardous traits.
    (The probabilities here are examples; adjust as needed.)
    """
    if agent.eye_color == "brown" and random.random() < 0.20:
        print(f"  > Agent {agent.id} died due to hazardous brown eyes.")
        return True
    if agent.eye_color == "green" and random.random() < 0.01:
        print(f"  > Agent {agent.id} died due to hazardous green eyes.")
        return True
    if agent.skin_color == "dark" and random.random() < 0.33:
        print(f"  > Agent {agent.id} died due to hazardous dark skin condition.")
        return True
    if agent.height < 160 and random.random() < 0.25:
        print(f"  > Agent {agent.id} died due to low height ({agent.height:.1f} cm).")
        return True
    if agent.fitness < 60 and random.random() < 0.15:
        print(f"  > Agent {agent.id} died due to low fitness ({agent.fitness:.1f}).")
        return True
    return False

def male_fights(population):
    """
    Simulate male fights among the population.
    Randomly pair male agents and, with a 15% chance, the one with lower effective fitness dies.
    Returns the updated population and the number of fights that occurred.
    """
    male_agents = [agent for agent in population if agent.gender == "M"]
    random.shuffle(male_agents)
    to_remove_ids = set()
    fight_count = 0
    for i in range(0, len(male_agents) - 1, 2):
        if random.random() < 0.15:
            fight_count += 1
            m1 = male_agents[i]
            m2 = male_agents[i+1]
            if effective_fitness(m1) > effective_fitness(m2):
                loser = m2
            elif effective_fitness(m2) > effective_fitness(m1):
                loser = m1
            else:
                loser = random.choice([m1, m2])
            print(f"  > Male fight: Agent {m1.id} (eff. fitness {effective_fitness(m1):.1f}) vs "
                  f"Agent {m2.id} (eff. fitness {effective_fitness(m2):.1f}) – Agent {loser.id} loses!")
            to_remove_ids.add(loser.id)
    population = [agent for agent in population if agent.id not in to_remove_ids]
    return population, fight_count

def get_preferred_male(female, available_males):
    """
    For a given female, select the best candidate male based on her preference.
    For "blue" preference, she favors males with blue eyes or blonde hair.
    Additionally, if the female is pure she normally (90% chance) only considers pure males of her own nationality.
    """
    if not available_males:
        return None

    candidates = available_males
    if is_pure(female):
        if random.random() < 0.9:
            female_nat = get_pure_nationality(female)
            filtered = [m for m in available_males if is_pure(m) and get_pure_nationality(m) == female_nat]
            if filtered:
                candidates = filtered

    if female.preference == "blue":
        preferred = [m for m in candidates if m.eye_color == "blue" or m.hair_color == "blonde"]
        if preferred:
            return max(preferred, key=lambda m: (effective_fitness(m) + m.height))
        else:
            return max(candidates, key=lambda m: (effective_fitness(m) + m.height))
    elif female.preference == "fitness":
        return max(candidates, key=lambda m: effective_fitness(m))
    elif female.preference == "height":
        return max(candidates, key=lambda m: m.height)
    else:
        return max(candidates, key=lambda m: (effective_fitness(m) + m.height))

def get_top_two_males(female, available_males):
    """
    For a high-beauty female, return the top two candidate males based on her preference.
    Applies the same same-nationality filtering (90% chance) if the female is pure.
    """
    if not available_males:
        return []
    
    candidates = available_males
    if is_pure(female):
        if random.random() < 0.9:
            female_nat = get_pure_nationality(female)
            filtered = [m for m in available_males if is_pure(m) and get_pure_nationality(m) == female_nat]
            if filtered:
                candidates = filtered

    if female.preference == "blue":
        sorted_males = sorted(
            candidates,
            key=lambda m: ((1 if (m.eye_color == "blue" or m.hair_color == "blonde") else 0),
                           effective_fitness(m) + m.height),
            reverse=True
        )
    elif female.preference == "fitness":
        sorted_males = sorted(candidates, key=lambda m: effective_fitness(m), reverse=True)
    elif female.preference == "height":
        sorted_males = sorted(candidates, key=lambda m: m.height, reverse=True)
    else:
        sorted_males = sorted(candidates, key=lambda m: (effective_fitness(m) + m.height), reverse=True)
    return sorted_males[:2]

def print_population(population, generation):
    """Print details of the entire population sorted by descending raw fitness."""
    sorted_pop = sorted(population, key=lambda a: a.fitness, reverse=True)
    print(f"\nPopulation at end of Generation {generation} (Total: {len(sorted_pop)}):")
    for agent in sorted_pop:
        print("  ", agent)

def run_simulation(generations, initial_population_size):
    """
    Run the simulation for a specified number of generations.
    Also, collect statistics at each generation for plotting later.
    """
    population = [create_random_agent() for _ in range(initial_population_size)]
    
    # Initialize stats storage.
    stats = {
        "generations": [],
        "population": [],
        "male_count": [],
        "female_count": [],
        "avg_eff_fitness": [],
        "fights": [],
        "male_selection_stress": [],
        "avg_height": [],
        "eye_color": {color: [] for color in EYE_COLORS},
        "hair_color": {color: [] for color in HAIR_COLORS},
        "skin_color": {color: [] for color in SKIN_COLORS},
        "nationality": {nat: [] for nat in NATIONALITIES}
    }
    
    for gen in range(1, generations + 1):
        print(f"\n=== Generation {gen} ===")
        
        # 1. Age update.
        for agent in population:
            agent.age += 1
        population = [agent for agent in population if agent.age < 4]
        
        # 2. Decrease female cooldown.
        for agent in population:
            if agent.gender == "F" and agent.cooldown > 0:
                agent.cooldown -= 1

        # 3. Forced trait death.
        survivors = []
        for agent in population:
            if not forced_trait_death(agent):
                survivors.append(agent)
        population = survivors

        # 4. Male fights.
        population, fight_count = male_fights(population)
        
        # 5. Remove the bottom 10% by effective fitness.
        if population:
            num_to_remove = max(1, int(len(population) * 0.1))
            population.sort(key=lambda a: effective_fitness(a))
            removed_agents = population[:num_to_remove]
            population = population[num_to_remove:]
            print(f"  > Removed {len(removed_agents)} low-fitness agent(s).")
        
        # 6. Mating phase.
        new_agents = []
        for agent in population:
            if agent.gender == "M":
                agent.mating_opportunities = 1

        eligible_females = [agent for agent in population if agent.gender == "F" and agent.cooldown == 0]
        eligible_females.sort(key=lambda f: f.beauty, reverse=True)

        def available_males():
            return [m for m in population if m.gender == "M" and m.mating_opportunities > 0]

        for female in eligible_females:
            current_available = available_males()
            if not current_available:
                break
            
            # High-beauty females may trigger a contest.
            if female.beauty >= 4:
                candidates = get_top_two_males(female, current_available)
                if len(candidates) >= 2:
                    m1, m2 = candidates[0], candidates[1]
                    if effective_fitness(m1) > effective_fitness(m2):
                        winner = m1
                    elif effective_fitness(m2) > effective_fitness(m1):
                        winner = m2
                    else:
                        winner = random.choice([m1, m2])
                    winner.mating_opportunities += 1
                    chosen_male = winner
                    print(f"  > High-beauty Female {female.id} (beauty {female.beauty}, pref {female.preference}) "
                          f"triggered a fight between Male {m1.id} and Male {m2.id}; winner is Male {winner.id}.")
                else:
                    chosen_male = candidates[0]
                    print(f"  > High-beauty Female {female.id} (beauty {female.beauty}, pref {female.preference}) "
                          f"found only one candidate: Male {chosen_male.id}.")
            else:
                chosen_male = get_preferred_male(female, current_available)
                if chosen_male:
                    print(f"  > Female {female.id} (beauty {female.beauty}, pref {female.preference}) chose Male {chosen_male.id}.")

            if chosen_male:
                chosen_male.mating_opportunities -= 1
                female.cooldown = 1
                children = reproduce(female, chosen_male)
                new_agents.extend(children)
        
        # 7. Add offspring.
        population.extend(new_agents)
        
        # 8. Print population.
        print_population(population, gen)
        if population:
            avg_eff = sum(effective_fitness(agent) for agent in population) / len(population)
            avg_ht = sum(agent.height for agent in population) / len(population)
        else:
            avg_eff = 0
            avg_ht = 0
        print(f"  > Generation {gen} Summary: Population Size = {len(population)}, "
              f"New Offspring = {len(new_agents)}, Average Effective Fitness = {avg_eff:.2f}, "
              f"Average Height = {avg_ht:.2f} cm")

        # === Collect Statistics ===
        stats["generations"].append(gen)
        stats["population"].append(len(population))
        male_count = sum(1 for agent in population if agent.gender == "M")
        female_count = sum(1 for agent in population if agent.gender == "F")
        stats["male_count"].append(male_count)
        stats["female_count"].append(female_count)
        stats["avg_eff_fitness"].append(avg_eff)
        stats["fights"].append(fight_count)
        stats["avg_height"].append(avg_ht)
        # Male selection stress: ratio of number of males to fights (if no fights, just use number of males)
        stress = male_count / fight_count if fight_count > 0 else male_count
        stats["male_selection_stress"].append(stress)
        
        # Eye color distribution.
        for color in EYE_COLORS:
            count = sum(1 for agent in population if agent.eye_color == color)
            stats["eye_color"][color].append(count)
        
        # Hair color distribution.
        for color in HAIR_COLORS:
            count = sum(1 for agent in population if agent.hair_color == color)
            stats["hair_color"][color].append(count)
        
        # Skin color distribution.
        for color in SKIN_COLORS:
            count = sum(1 for agent in population if agent.skin_color == color)
            stats["skin_color"][color].append(count)
        
        # Nationality distribution.
        for nat in NATIONALITIES:
            count = sum(1 for agent in population if agent.nationality == nat)
            stats["nationality"][nat].append(count)
    
    return population, stats

def plot_stats(stats):
    """Generate plots for the collected simulation statistics."""
    generations = stats["generations"]
    
    # We'll create a figure with 2 rows and 4 columns (8 subplots) and use 7 of them.
    plt.figure(figsize=(16, 8))
    
    # Subplot 1: Population size per generation.
    plt.subplot(2, 4, 1)
    plt.plot(generations, stats["population"], marker='o')
    plt.title("Population Size per Generation")
    plt.xlabel("Generation")
    plt.ylabel("Population Size")
    
    # Subplot 2: Male and Female counts.
    plt.subplot(2, 4, 2)
    plt.plot(generations, stats["male_count"], marker='o', label='Males')
    plt.plot(generations, stats["female_count"], marker='o', label='Females')
    plt.title("Male & Female Count")
    plt.xlabel("Generation")
    plt.ylabel("Count")
    plt.legend()
    
    # Subplot 3: Average effective fitness per generation.
    plt.subplot(2, 4, 3)
    plt.plot(generations, stats["avg_eff_fitness"], marker='o', color='green')
    plt.title("Avg. Effective Fitness")
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    
    # Subplot 4: Male selection stress per generation.
    plt.subplot(2, 4, 4)
    plt.plot(generations, stats["male_selection_stress"], marker='o', color='red')
    plt.title("Male Selection Stress\n(Males / Fights)")
    plt.xlabel("Generation")
    plt.ylabel("Stress Ratio")
    
    # Subplot 5: Distribution of eye colors.
    plt.subplot(2, 4, 5)
    for color in EYE_COLORS:
        plt.plot(generations, stats["eye_color"][color], marker='o', label=color)
    plt.title("Eye Color Distribution")
    plt.xlabel("Generation")
    plt.ylabel("Count")
    plt.legend()
    
    # Subplot 6: Average Height per Generation.
    plt.subplot(2, 4, 6)
    plt.plot(generations, stats["avg_height"], marker='o', color='purple')
    plt.title("Average Height per Generation")
    plt.xlabel("Generation")
    plt.ylabel("Height (cm)")
    
    # Subplot 7: Distribution of skin colors.
    plt.subplot(2, 4, 7)
    for color in SKIN_COLORS:
        plt.plot(generations, stats["skin_color"][color], marker='o', label=color)
    plt.title("Skin Color Distribution")
    plt.xlabel("Generation")
    plt.ylabel("Count")
    plt.legend()
    
    plt.tight_layout()
    
    # Hair color distribution in a separate figure.
    plt.figure(figsize=(12, 6))
    for color in HAIR_COLORS:
        plt.plot(generations, stats["hair_color"][color], marker='o', label=color)
    plt.title("Hair Color Distribution per Generation")
    plt.xlabel("Generation")
    plt.ylabel("Count")
    plt.legend()
    
    # Nationality distribution in another figure.
    plt.figure(figsize=(12, 6))
    for nat in NATIONALITIES:
        plt.plot(generations, stats["nationality"][nat], marker='o', label=nat)
    plt.title("Nationality Distribution per Generation")
    plt.xlabel("Generation")
    plt.ylabel("Count")
    plt.legend()
    
    plt.show()

if __name__ == "__main__":
    # Run the simulation for 15 generations starting with 10 agents.
    final_population, stats = run_simulation(generations=15, initial_population_size=100)
    
    print("\n=== Final Population ===")
    for agent in final_population:
        print("  ", agent)
    
    # Plot the collected statistics.
    plot_stats(stats)
