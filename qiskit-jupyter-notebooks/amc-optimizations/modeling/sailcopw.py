# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2018
# --------------------------------------------------------------------------


from docplex.mp.model import Model
from docplex.util.environment import get_environment


# The company Sailco must determine how many sailboats to produce over several time periods,
# while satisfying demand and minimizing costs.
# The demand for the periods is known and an inventory of boats is available initially.
# In each period, Sailco can produce boats inside at a fixed cost per boat.
# Additional boats can be produced outside at a higher cost per boat.
# There is an inventory cost per boat per period.
# The business objective is to minimize the overall cost, which is the sum of the
# production cost and inventory cost.
# The production cost is modeled using a *piecewise-linear* function.

# ----------------------------------------------------------------------------
# Initialize the problem data
# ----------------------------------------------------------------------------
nb_periods = 4
demand = {1: 40, 2: 60, 3: 75, 4: 25}

regular_cost = 400
capacity = 40
extra_cost = 450

initial_inventory = 10
inventory_cost = 20

# ----------------------------------------------------------------------------
# Build the model
# ----------------------------------------------------------------------------


def build_sailcopw_model(**kwargs):
    mdl = Model(name="sailcopw", **kwargs)
    periods0 = range(nb_periods + 1)
    periods1 = range(1, nb_periods + 1)

    boats = mdl.continuous_var_dict(periods1, name="boat")
    # full range from 0 to nb_periods
    inv = mdl.continuous_var_dict(periods0, name="inv")

    # ---
    # piecewise cost:
    # up to zero boat cost is zero.
    # up to capacity, each boat costs the regular cost
    # above capacity, unit cost is extra cost (higher than regular cost...)
    pwc = mdl.piecewise(preslope=0, breaksxy=[(0,0), (capacity, capacity * regular_cost)], postslope=extra_cost)
    total_pw_cost = mdl.sum(pwc(boats[t]) for t in periods1)
    mdl.add_kpi(total_pw_cost, "Total piecewise cost")
    total_inventory_cost = inventory_cost * mdl.sum(inv[t1] for t1 in periods1)
    mdl.add_kpi(total_inventory_cost, 'Total inventory cost')

    mdl.minimize(total_pw_cost + total_inventory_cost)

    # initial inventory
    mdl.add_constraint(inv[0] == initial_inventory)
    # balance
    mdl.add_constraints([boats[t] + inv[t - 1] == inv[t] + demand.get(t,0) for t in periods1])

    return mdl

# ----------------------------------------------------------------------------
# Solve the model and display the result
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    sailm = build_sailcopw_model()
    s = sailm.solve(log_output=True)
    if s:
        sailm.report()
        sailm.print_solution()

        # Save the CPLEX solution as "solution.json" program output
        with get_environment().get_output_stream("solution.json") as fp:
            sailm.solution.export(fp, "json")
    else:
        print("Problem has no solution")
