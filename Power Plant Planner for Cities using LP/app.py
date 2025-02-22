import sys
import pulp
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem


class EnergyOptimizationApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.setWindowTitle('Energy Optimization for City')
        self.setGeometry(100, 100, 800, 600)

        # Create widgets (input fields, labels, and buttons)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # City information inputs
        self.energy_demand_input = QLineEdit(self)
        self.energy_demand_input.setPlaceholderText("Enter Energy Demand (in MW)")
        layout.addWidget(self.energy_demand_input)

        self.budget_input = QLineEdit(self)
        self.budget_input.setPlaceholderText("Enter Budget (in currency units)")
        layout.addWidget(self.budget_input)

        self.booster_budget_input = QLineEdit(self)
        self.booster_budget_input.setPlaceholderText("Enter Booster Budget (in currency units)")
        layout.addWidget(self.booster_budget_input)

        # Button to trigger optimization
        self.optimize_button = QPushButton("Optimize Energy Production", self)
        self.optimize_button.clicked.connect(self.optimize_energy)
        layout.addWidget(self.optimize_button)

        # Table to display results (selected assets and energy production)
        self.results_table = QTableWidget(self)
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(['Asset Name', 'Units', 'Predicted Energy Production'])
        layout.addWidget(self.results_table)

        # Set the layout
        self.setLayout(layout)

    def predict_energy(self, asset, weather_factor=1.0):
        """
        Predict the energy production per unit of an asset, adjusted by the weather factor.
        Energy production is scaled by an efficiency factor determined by asset type.
        """
        name = asset["name"].lower()
        efficiency_map = {
            "solar": 1,
            "wind": 100,
            "hydro": 1000,
            "biomass": 1000,
            "coal": 1000,
            "gas": 1000,
            "nuclear": 1000
        }
        efficiency = next((eff for key, eff in efficiency_map.items() if key in name), 1.0)
        return weather_factor * efficiency

    def optimize_energy(self):
        # Get city data from input fields
        energy_demand = float(self.energy_demand_input.text())
        budget = float(self.budget_input.text())
        booster_budget = float(self.booster_budget_input.text())

        # Define assets with cost, environmental penalties, etc.
        assets = [
            {'name': 'Solar Panel', 'cost': 0.758, 'env_penalty': 0, 'repair_cost': 0.010, 'supply_limit': 50, 'development_time': 1.0},
            {'name': 'Wind Turbine', 'cost': 130.0, 'env_penalty': 0, 'repair_cost': 0.030, 'supply_limit': 30, 'development_time': 2.0},
            {'name': 'Hydro Plant', 'cost': 320.0, 'env_penalty': 100, 'repair_cost': 0.080, 'supply_limit': 5, 'development_time': 4.0},
            {'name': 'Biomass Plant', 'cost': 1000.0, 'env_penalty': 500, 'repair_cost': 0.050, 'supply_limit': 10, 'development_time': 3.0},
            {'name': 'Coal Plant', 'cost': 1800.0, 'env_penalty': 2000, 'repair_cost': 0.100, 'supply_limit': 8, 'development_time': 3.0},
            {'name': 'Gas Plant', 'cost': 6000.0, 'env_penalty': 1250, 'repair_cost': 0.150, 'supply_limit': 4, 'development_time': 2.0},
            {'name': 'Nuclear Plant', 'cost': 6900.0, 'env_penalty': 1000, 'repair_cost': 0.200, 'supply_limit': 2, 'development_time': 5.0},
        ]

        # Booster factors
        booster_factor = 0.2
        min_development_time = 0.5

        # Compute effective development time based on booster budget
        for asset in assets:
            effective_time = asset["development_time"] - booster_factor * booster_budget
            effective_time = max(effective_time, min_development_time)
            asset["effective_time"] = effective_time

            # If the asset cannot be developed within the allowed time, mark it as unavailable
            if effective_time > 50:
                asset["supply_limit"] = 0

        # Set the weather factor and compute predicted energy production
        weather_factor = 1.0
        for asset in assets:
            asset['predicted_energy'] = self.predict_energy(asset, weather_factor)

        # Create the optimization problem instance (minimization)
        prob = pulp.LpProblem("Energy_Optimization", pulp.LpMinimize)

        # Decision variables for asset units
        asset_vars = {asset['name']: pulp.LpVariable(asset['name'].replace(" ", "_"), lowBound=0, upBound=asset['supply_limit'], cat='Integer') for asset in assets}

        # Tunable factor for environmental penalty cost
        lambda_env = 0.001

        # Objective: Minimize total lifecycle cost (capital cost + repair + environmental penalty)
        prob += pulp.lpSum(
            (asset['cost'] + asset['repair_cost'] + lambda_env * asset['env_penalty']) * asset_vars[asset['name']]
            for asset in assets
        ), "Total_Cost"

        # Constraint: Total energy production meets or exceeds city demand
        prob += pulp.lpSum(
            asset['predicted_energy'] * asset_vars[asset['name']]
            for asset in assets
        ) >= energy_demand, "Energy_Demand"

        # Constraint: Capital cost must not exceed the budget
        prob += pulp.lpSum(
            asset['cost'] * asset_vars[asset['name']]
            for asset in assets
        ) <= budget, "Budget_Constraint"

        # Solve the optimization problem
        prob.solve()
        status = pulp.LpStatus[prob.status]

        # Display the results in the table
        if status == 'Optimal':
            # Update the table with selected assets and predicted energy production
            self.results_table.setRowCount(0)  # Clear existing rows
            for asset in assets:
                units = asset_vars[asset['name']].varValue
                if units > 0:
                    row_position = self.results_table.rowCount()
                    self.results_table.insertRow(row_position)
                    self.results_table.setItem(row_position, 0, QTableWidgetItem(asset['name']))
                    self.results_table.setItem(row_position, 1, QTableWidgetItem(str(units)))
                    self.results_table.setItem(row_position, 2, QTableWidgetItem(f"{asset['predicted_energy'] * units:.2f}"))

            # Optionally, print the total energy production and cost breakdown here
            print(f"Total Predicted Energy Production: {sum(asset['predicted_energy'] * asset_vars[asset['name']].varValue for asset in assets)}")
        else:
            print("No optimal solution found")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EnergyOptimizationApp()
    window.show()
    sys.exit(app.exec_())
