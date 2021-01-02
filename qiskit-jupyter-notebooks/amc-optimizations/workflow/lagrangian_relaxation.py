# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2018
# --------------------------------------------------------------------------

import json

from docplex.util.environment import get_environment
from docplex.mp.model import Model


# ----------------------------------------------------------------------------
# Initialize the problem data
# ----------------------------------------------------------------------------
B = [15, 15, 15]
C = [
    [ 6, 10, 1],
    [12, 12, 5],
    [15,  4, 3],
    [10,  3, 9],
    [8,   9, 5]
]
A = [
    [ 5,  7,  2],
    [14,  8,  7],
    [10,  6, 12],
    [ 8,  4, 15],
    [ 6, 12,  5]
]


# ----------------------------------------------------------------------------
# Build the model
# ----------------------------------------------------------------------------
def run_GAP_model(As, Bs, Cs, **kwargs):
    with Model('GAP per Wolsey -without- Lagrangian Relaxation', **kwargs) as mdl:
        print("#As={}, #Bs={}, #Cs={}".format(len(As), len(Bs), len(Cs)))
        number_of_cs = len(C)
        # variables
        x_vars = [mdl.binary_var_list(c, name=None) for c in Cs]

        # constraints
        mdl.add_constraints(mdl.sum(xv) <= 1 for xv in x_vars)

        mdl.add_constraints(mdl.sum(x_vars[ii][j] * As[ii][j] for ii in range(number_of_cs)) <= bs
                            for j, bs in enumerate(Bs))

        # objective
        total_profit = mdl.sum(mdl.scal_prod(x_i, c_i) for c_i, x_i in zip(Cs, x_vars))
        mdl.maximize(total_profit)
        #  mdl.print_information()
        s = mdl.solve()
        assert s is not None
        obj = s.objective_value
        print("* GAP with no relaxation run OK, best objective is: {:g}".format(obj))
    return obj


def run_GAP_model_with_Lagrangian_relaxation(As, Bs, Cs, max_iters=101, **kwargs):
    with Model('GAP per Wolsey -with- Lagrangian Relaxation', **kwargs) as mdl:
        print("#As={}, #Bs={}, #Cs={}".format(len(As), len(Bs), len(Cs)))
        number_of_cs = len(Cs)
        c_range = range(number_of_cs)
        # variables
        x_vars = [mdl.binary_var_list(c, name=None) for c in Cs]
        p_vars = mdl.continuous_var_list(Cs, name='p')  # new for relaxation

        mdl.add_constraints(mdl.sum(xv) == 1 - pv for xv, pv in zip(x_vars, p_vars))

        mdl.add_constraints(mdl.sum(x_vars[ii][j] * As[ii][j] for ii in c_range) <= bs
                            for j, bs in enumerate(Bs))

        # lagrangian relaxation loop
        eps = 1e-6
        loop_count = 0
        best = 0
        initial_multiplier = 1
        multipliers = [initial_multiplier] * len(Cs)

        total_profit = mdl.sum(mdl.scal_prod(x_i, c_i) for c_i, x_i in zip(Cs, x_vars))
        mdl.add_kpi(total_profit, "Total profit")

        while loop_count <= max_iters:
            loop_count += 1
            # rebuilt at each loop iteration
            total_penalty = mdl.scal_prod(p_vars, multipliers)
            mdl.maximize(total_profit + total_penalty)
            s = mdl.solve()
            if not s:
                print("*** solve fails, stopping at iteration: %d" % loop_count)
                break
            best = s.objective_value
            penalties = [pv.solution_value for pv in p_vars]
            print('%d> new lagrangian iteration:\n\t obj=%g, m=%s, p=%s' % (loop_count, best, str(multipliers), str(penalties)))

            do_stop = True
            justifier = 0
            for k in c_range:
                penalized_violation = penalties[k] * multipliers[k]
                if penalized_violation >= eps:
                    do_stop = False
                    justifier = penalized_violation
                    break

            if do_stop:
                print("* Lagrangian relaxation succeeds, best={:g}, penalty={:g}, #iterations={}"
                      .format(best, total_penalty.solution_value, loop_count))
                break
            else:
                # update multipliers and start loop again.
                scale_factor = 1.0 / float(loop_count)
                multipliers = [max(multipliers[i] - scale_factor * penalties[i], 0.) for i in c_range]
                print('{0}> -- loop continues, m={1!s}, justifier={2:g}'.format(loop_count, multipliers, justifier))

    return best


def run_default_GAP_model_with_lagrangian_relaxation(**kwargs):
    return run_GAP_model_with_Lagrangian_relaxation(As=A, Bs=B, Cs=C, **kwargs)


# ----------------------------------------------------------------------------
# Solve the model and display the result
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    # Run the model. If a key has been specified above, the model will run on
    # IBM Decision Optimization on cloud.
    gap_best_obj = run_GAP_model(A, B, C)
    relaxed_best = run_GAP_model_with_Lagrangian_relaxation(A, B, C)
    # save the relaxed solution
    with get_environment().get_output_stream("solution.json") as fp:
        fp.write(json.dumps({"objectiveValue": relaxed_best}).encode('utf-8'))
