# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2018
# --------------------------------------------------------------------------

# The goal of the diet problem is to select a set of foods that satisfies
# a set of daily nutritional requirements at minimal cost.
# Source of data: http://www.neos-guide.org/content/diet-problem-solver

from collections import namedtuple

from docplex.mp.model import Model
from docplex.util.environment import get_environment

# ----------------------------------------------------------------------------
# Initialize the problem data
# ----------------------------------------------------------------------------

FOODS = [
    ("Roasted Chicken", 0.84, 0, 10),
    ("Spaghetti W/ Sauce", 0.78, 0, 10),
    ("Tomato,Red,Ripe,Raw", 0.27, 0, 10),
    ("Apple,Raw,W/Skin", .24, 0, 10),
    ("Grapes", 0.32, 0, 10),
    ("Chocolate Chip Cookies", 0.03, 0, 10),
    ("Lowfat Milk", 0.23, 0, 10),
    ("Raisin Brn", 0.34, 0, 10),
    ("Hotdog", 0.31, 0, 10)
]

NUTRIENTS = [
    ("Calories", 2000, 2500),
    ("Calcium", 800, 1600),
    ("Iron", 10, 30),
    ("Vit_A", 5000, 50000),
    ("Dietary_Fiber", 25, 100),
    ("Carbohydrates", 0, 300),
    ("Protein", 50, 100)
]

FOOD_NUTRIENTS = [
    ("Roasted Chicken", 277.4, 21.9, 1.8, 77.4, 0, 0, 42.2),
    ("Spaghetti W/ Sauce", 358.2, 80.2, 2.3, 3055.2, 11.6, 58.3, 8.2),
    ("Tomato,Red,Ripe,Raw", 25.8, 6.2, 0.6, 766.3, 1.4, 5.7, 1),
    ("Apple,Raw,W/Skin", 81.4, 9.7, 0.2, 73.1, 3.7, 21, 0.3),
    ("Grapes", 15.1, 3.4, 0.1, 24, 0.2, 4.1, 0.2),
    ("Chocolate Chip Cookies", 78.1, 6.2, 0.4, 101.8, 0, 9.3, 0.9),
    ("Lowfat Milk", 121.2, 296.7, 0.1, 500.2, 0, 11.7, 8.1),
    ("Raisin Brn", 115.1, 12.9, 16.8, 1250.2, 4, 27.9, 4),
    ("Hotdog", 242.1, 23.5, 2.3, 0, 0, 18, 10.4)
]

Food = namedtuple("Food", ["name", "unit_cost", "qmin", "qmax"])
Nutrient = namedtuple("Nutrient", ["name", "qmin", "qmax"])


# ----------------------------------------------------------------------------
# Build the model
# ----------------------------------------------------------------------------

def build_diet_model(name='diet', **kwargs):
    ints = kwargs.pop('ints', False)

    # Create tuples with named fields for foods and nutrients
    foods = [Food(*f) for f in FOODS]
    nutrients = [Nutrient(*row) for row in NUTRIENTS]

    food_nutrients = {(fn[0], nutrients[n].name):
                          fn[1 + n] for fn in FOOD_NUTRIENTS for n in range(len(NUTRIENTS))}

    # Model
    mdl = Model(name=name, **kwargs)

    # Decision variables, limited to be >= Food.qmin and <= Food.qmax
    ftype = mdl.integer_vartype if ints else mdl.continuous_vartype
    qty = mdl.var_dict(foods, ftype, lb=lambda f: f.qmin, ub=lambda f: f.qmax, name=lambda f: "q_%s" % f.name)

    # Limit range of nutrients, and mark them as KPIs
    for n in nutrients:
        amount = mdl.sum(qty[f] * food_nutrients[f.name, n.name] for f in foods)
        mdl.add_range(n.qmin, amount, n.qmax)
        mdl.add_kpi(amount, publish_name="Total %s" % n.name)

    # Minimize cost
    total_cost = mdl.sum(qty[f] * f.unit_cost for f in foods)
    mdl.add_kpi(total_cost, 'Total cost')

    # add a functional KPI , taking a model and a solution as argument
    # this KPI counts the number of foods used.
    def nb_products(mdl_, s_):
        qvs = mdl_.find_matching_vars(pattern="q_")
        return sum(1 for qv in qvs if s_[qv] >= 1e-5)

    mdl.add_kpi(nb_products, 'Nb foods')
    mdl.minimize(total_cost)

    return mdl


# ----------------------------------------------------------------------------
# Solve the model and display the result
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    mdl = build_diet_model(ints=True, log_output=True, float_precision=6)
    mdl.print_information()

    s = mdl.solve()
    if s:
        qty_vars = mdl.find_matching_vars(pattern="q_")
        for fv in qty_vars:
            food_name = fv.name[2:]
            print("Buy {0:<25} = {1:9.6g}".format(food_name, fv.solution_value))

        mdl.report_kpis()
        # Save the CPLEX solution as "solution.json" program output
        with get_environment().get_output_stream("solution.json") as fp:
            mdl.solution.export(fp, "json")
    else:
        print("* model has no solution")
