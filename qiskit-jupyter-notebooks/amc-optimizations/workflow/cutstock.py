# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

from collections import namedtuple
import json

from docplex.util.environment import get_environment
from docplex.mp.model import Model


# ----------------------------------------------------------------------------
# Initialize the problem data
# ----------------------------------------------------------------------------
DEFAULT_ROLL_WIDTH = 110
DEFAULT_ITEMS = [(1, 20, 48), (2, 45, 35), (3, 50, 24), (4, 55, 10), (5, 75, 8)]
DEFAULT_PATTERNS = [(i, 1) for i in range(1, 6)]  # (1, 1), (2, 1) etc
DEFAULT_PATTERN_ITEM_FILLED = [(p, p, 1) for p in range(1, 6)]  # pattern1 for item1, pattern2 for item2, etc.

FIRST_GENERATION_DUALS = [1, 1, 1, 1, 0]


# ----------------------------------------------------------------------------
# Build the model
# ----------------------------------------------------------------------------
class TItem(object):
    def __init__(self, item_id, item_size, demand):
        self.id = item_id
        self.size = item_size
        self.demand = demand
        self.dual_value = -1

    @classmethod
    def make(cls, args):
        arg_id = args[0]
        arg_size = args[1]
        arg_demand = args[2]
        return cls(arg_id, arg_size, arg_demand)

    def __str__(self):
        return 'item%d' % self.id


class TPattern(namedtuple("TPattern", ["id", "cost"])):
    def __str__(self):
        return 'pattern%d' % self.id

# ---


def make_cutstock_pattern_generation_model(items, roll_width, **kwargs):
    gen_model = Model(name='cutstock_generate_patterns', **kwargs)
    # store data
    gen_model.items = items
    gen_model.roll_width = roll_width
    # default values
    gen_model.duals = [1] * len(items)
    # 1. create variables: one per item
    gen_model.use_vars = gen_model.integer_var_list(keys=items, ub=999999, name='use')
    # 2 setup constraint:
    # --- sum of item usage times item sizes must be less than roll width
    gen_model.add(gen_model.dot(gen_model.use_vars, (it.size for it in items)) <= roll_width)

    # store dual expression for dynamic edition
    gen_model.use_dual_expr = 1 - gen_model.dot(gen_model.use_vars, gen_model.duals)
    # minimize
    gen_model.minimize(gen_model.use_dual_expr)

    return gen_model


def cutstock_update_duals(gmodel, new_duals):
    # update the duals array and the the duals expression...
    # edition is propagated to the objective of the model.
    gmodel.duals = new_duals
    use_vars = gmodel.use_vars
    assert len(new_duals) == len(use_vars)
    updated_used = [(use, -new_duals[u]) for u, use in enumerate(use_vars)]
    # this modification is notified to the objective.
    gmodel.use_dual_expr.set_coefficients(updated_used)
    return gmodel


def make_custstock_master_model(item_table, pattern_table, fill_table, roll_width, **kwargs):
    m = Model(name='custock_master', **kwargs)

    # store data as properties
    m.items = [TItem.make(it_row) for it_row in item_table]
    m.items_by_id = {it.id: it for it in m.items}
    m.patterns = [TPattern(*pattern_row) for pattern_row in pattern_table]
    m.patterns_by_id = {pat.id: pat for pat in m.patterns}
    m.max_pattern_id = max(pt.id for pt in m.patterns)

    # build a dictionary storing how much each pattern fills each item.
    m.pattern_item_filled = {(m.patterns_by_id[p], m.items_by_id[i]): f for (p, i, f) in fill_table}
    m.roll_width = roll_width

    # --- variables
    # one cut var per pattern...
    m.MAX_CUT = 9999
    m.cut_vars = m.continuous_var_dict(m.patterns, lb=0, ub=m.MAX_CUT, name="cut")

    # --- add fill constraints
    #
    all_patterns = m.patterns
    all_items = m.items
    m.item_fill_cts = []
    for item in all_items:
        item_fill_ct = m.sum(
            m.cut_vars[p] * m.pattern_item_filled.get((p, item), 0) for p in all_patterns) >= item.demand
        item_fill_ct.name = 'ct_fill_{0!s}'.format(item)
        m.item_fill_cts.append(item_fill_ct)
    m.add_constraints(m.item_fill_cts)

    # --- minimize total cut stock
    m.total_cutting_cost = m.sum(m.cut_vars[p] * p.cost for p in all_patterns)
    m.minimize(m.total_cutting_cost)

    return m


def add_pattern_to_master_model(master_model, item_usages):
    """ Adds a new pattern to the master model.

    This function performs the following:

    1. build a new pattern instance from item usages (taken from sub-model)
    2. add it to the master model
    3. update decision objects with this new pattern.
    """
    new_pattern_id = max(pt.id for pt in master_model.patterns) + 1
    new_pattern = TPattern(new_pattern_id, 1)
    master_model.patterns.append(new_pattern)
    for used, item in zip(item_usages, master_model.items):
        master_model.pattern_item_filled[new_pattern, item] = used

    # --- add one decision variable, linked to the new pattern.
    new_pattern_cut_var = master_model.continuous_var(lb=0, ub=master_model.MAX_CUT,
                                                      name='cut_{0}'.format(new_pattern_id))
    master_model.cut_vars[new_pattern] = new_pattern_cut_var

    # update constraints
    for item, ct in zip(master_model.items, master_model.item_fill_cts):
        # update fill constraint by changing lhs
        ctlhs = ct.lhs
        filled = master_model.pattern_item_filled[new_pattern, item]
        if filled:
            ctlhs += new_pattern_cut_var * filled

    # update objective:
    #   side-effect on  the total cutting cost expr propagates to the objective.
    cost_expr = master_model.total_cutting_cost
    cost_expr += new_pattern_cut_var * new_pattern.cost  # this performw a side effect!

    return master_model


def cutstock_print_solution(cutstock_model):
    patterns = cutstock_model.patterns
    cut_var_values = {p: cutstock_model.cut_vars[p].solution_value for p in patterns}
    pattern_item_filled = cutstock_model.pattern_item_filled
    print("| Nb of cuts | Pattern   | Pattern's detail (# of item1,item2,...) |")
    print("| {} |".format("-" * 70))
    for p in patterns:
        if cut_var_values[p] >= 1e-3:
            pattern_detail = {b.id: pattern_item_filled[a, b] for a, b in pattern_item_filled if
                              a == p}
            print(
                "| {:<10g} | {!s:9} | {!s:45} |".format(cut_var_values[p],
                                                        p,
                                                        pattern_detail))
    print("| {} |".format("-" * 70))


def cutstock_save_as_json(model, json_file):
    patterns = model.patterns
    cut_var_values = {p: model.cut_vars[p].solution_value for p in patterns}
    solution = []
    for p in patterns:
        if cut_var_values[p] >= 1e-3:
            pattern_detail = {b.id: model.pattern_item_filled[(a, b)] for (a, b) in model.pattern_item_filled if
                              a == p}
            n = {'pattern': str(p),
                 'cuts': "%g" % cut_var_values[p],
                 'details': pattern_detail}
            solution.append(n)
    json_file.write(json.dumps(solution, indent=3).encode('utf-8'))


def cutstock_solve(item_table, pattern_table, fill_table, roll_width, **kwargs):
    verbose = kwargs.pop('verbose', True)
    master_model = make_custstock_master_model(item_table, pattern_table, fill_table, roll_width, **kwargs)

    # these two fields contain named tuples
    items = master_model.items
    patterns = master_model.patterns
    gen_model = make_cutstock_pattern_generation_model(items, roll_width, **kwargs)

    rc_eps = 1e-6
    obj_eps = 1e-4
    loop_count = 0
    best = 0
    curr = 1e+20
    ms = None

    while loop_count < 100 and abs(best - curr) >= obj_eps:
        ms = master_model.solve(**kwargs)
        loop_count += 1
        best = curr
        if not ms:
            print('{}> master model fails, stop'.format(loop_count))
            break
        else:
            assert ms
            curr = master_model.objective_value
            if verbose:
                print('{}> new column generation iteration, #patterns={}, best={:g}, curr={:g}'
                      .format(loop_count, len(patterns), best, curr))
            duals = master_model.dual_values(master_model.item_fill_cts)
            if verbose:
                print('{0}> moving duals from master to sub model: {1}'
                      .format(loop_count, list(map(lambda x: float('%0.2f' % x), duals))))
            cutstock_update_duals(gen_model, duals)
            gs = gen_model.solve(**kwargs)
            if not gs:
                print('{}> slave model fails, stop'.format(loop_count))
                break

            rc_cost = gen_model.objective_value
            if rc_cost <= -rc_eps:
                if verbose:
                    print('{}> slave model runs with obj={:g}'.format(loop_count, rc_cost))
            else:
                if verbose:
                    print('{}> pattern-generator model stops, obj={:g}'.format(loop_count, rc_cost))
                break

            use_values = gen_model.solution.get_values(gen_model.use_vars)
            if verbose:
                print('{}> add new pattern to master data: {}'.format(loop_count, str(use_values)))
            # make a new pattern with use values
            if not (loop_count < 100 and abs(best - curr) >= obj_eps):
                print('* terminating: best-curr={:g}'.format(abs(best - curr)))
                break
            add_pattern_to_master_model(master_model, use_values)

    if ms:
        if verbose:
            print('\n* Cutting-stock column generation terminates, best={:g}, #loops={}'.format(curr, loop_count))
            cutstock_print_solution(master_model)
        return ms
    else:
        print("!!!!  Cutting-stock column generation fails  !!!!")
        return None


def cutstock_solve_default(**kwargs):
    return cutstock_solve(DEFAULT_ITEMS, DEFAULT_PATTERNS, DEFAULT_PATTERN_ITEM_FILLED, DEFAULT_ROLL_WIDTH,
                          **kwargs)


# -----------------------------------------------------------------------------
# Solve the model and display the result
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    s = cutstock_solve_default()
    assert abs(s.objective_value - 46.25) <= 0.1
    # Save the solution as "solution.json" program output.
    with get_environment().get_output_stream("solution.json") as fp:
        cutstock_save_as_json(s.model, fp)
