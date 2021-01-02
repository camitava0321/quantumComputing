# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2018
# --------------------------------------------------------------------------

"""The model aims at minimizing the production cost for a number of products
while satisfying customer demand. Each product can be produced either inside
the company or outside, at a higher cost.

The inside production is constrained by the company's resources, while outside
production is considered unlimited.

The model first declares the products and the resources.
The data consists of the description of the products (the demand, the inside
and outside costs, and the resource consumption) and the capacity of the
various resources.

The variables for this problem are the inside and outside production for each
product.
"""

from docplex.mp.model import Model
from docplex.util.environment import get_environment


# ----------------------------------------------------------------------------
# Initialize the problem data
# ----------------------------------------------------------------------------
PRODUCTS = [("kluski", 100, 0.6, 0.8),
            ("capellini", 200, 0.8, 0.9),
            ("fettucine", 300, 0.3, 0.4)]

# resources are a list of simple tuples (name, capacity)
RESOURCES = [("flour", 20),
             ("eggs", 40)]

CONSUMPTIONS = {("kluski", "flour"): 0.5,
                ("kluski", "eggs"): 0.2,
                ("capellini", "flour"): 0.4,
                ("capellini", "eggs"): 0.4,
                ("fettucine", "flour"): 0.3,
                ("fettucine", "eggs"): 0.6}


# ----------------------------------------------------------------------------
# Build the model
# ----------------------------------------------------------------------------
def build_production_problem(products, resources, consumptions, **kwargs):
    """ Takes as input:
        - a list of product tuples (name, demand, inside, outside)
        - a list of resource tuples (name, capacity)
        - a list of consumption tuples (product_name, resource_named, consumed)
    """
    mdl = Model(name='production', **kwargs)
    # --- decision variables ---
    mdl.inside_vars  = mdl.continuous_var_dict(products, name=lambda p: 'inside_%s' % p[0])
    mdl.outside_vars = mdl.continuous_var_dict(products, name=lambda p: 'outside_%s' % p[0])

    # --- constraints ---
    # demand satisfaction
    mdl.add_constraints((mdl.inside_vars[prod] + mdl.outside_vars[prod] >= prod[1], 'ct_demand_%s' % prod[0]) for prod in products)

    # --- resource capacity ---
    mdl.add_constraints((mdl.sum(mdl.inside_vars[p] * consumptions[p[0], res[0]] for p in products) <= res[1],
                         'ct_res_%s' % res[0]) for res in resources)

    # --- objective ---
    mdl.total_inside_cost = mdl.sum(mdl.inside_vars[p] * p[2] for p in products)
    mdl.add_kpi(mdl.total_inside_cost, "inside cost")
    mdl.total_outside_cost = mdl.sum(mdl.outside_vars[p] * p[3] for p in products)
    mdl.add_kpi(mdl.total_outside_cost, "outside cost")
    mdl.minimize(mdl.total_inside_cost + mdl.total_outside_cost)
    return mdl


def print_production_solution(mdl, products):
    obj = mdl.objective_value
    print("* Production model solved with objective: {:g}".format(obj))
    print("* Total inside cost=%g" % mdl.total_inside_cost.solution_value)
    for p in products:
        print("Inside production of {product}: {ins_var}".format
              (product=p[0], ins_var=mdl.inside_vars[p].solution_value))
    print("* Total outside cost=%g" % mdl.total_outside_cost.solution_value)
    for p in products:
        print("Outside production of {product}: {out_var}".format
              (product=p[0], out_var=mdl.outside_vars[p].solution_value))


def build_default_production_problem(**kwargs):
    return build_production_problem(PRODUCTS, RESOURCES, CONSUMPTIONS, **kwargs)

# ----------------------------------------------------------------------------
# Solve the model and display the result
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    # Build the model
    model = build_production_problem(PRODUCTS, RESOURCES, CONSUMPTIONS)
    model.print_information()
    # Solve the model.
    if model.solve():
        print_production_solution(model, PRODUCTS)
        # Save the CPLEX solution as "solution.json" program output
        with get_environment().get_output_stream("solution.json") as fp:
            model.solution.export(fp, "json")
    else:
        print("Problem has no solution")

