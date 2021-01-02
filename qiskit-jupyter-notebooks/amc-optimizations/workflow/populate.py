#!/usr/bin/python
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Licensed Materials - Property of IBM
# 5725-A06 5725-A29 5724-Y48 5724-Y49 5724-Y54 5724-Y55 5655-Y21
# Copyright IBM Corporation 2009, 2019. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with
# IBM Corp.
# ---------------------------------------------------------------------------
"""
Reading a MIP problem and generating multiple solutions.

This sample can be used to run populate either on a model file (LP or SAV)
or a DOcplex model instance.

"""
from docplex.mp.model_reader import ModelReader


def populate_from_file(filename, gap=0.1,
                       pool_intensity=4,
                       pool_capacity=None,
                       eps_diff=1e-7,
                       verbose=False):
    """ Runs populate on a model file.

    :param filename: the model file.
    :param gap: MIP gap to use for the populate phase (default is 10%)
    :param pool_intensity: the value for the paramater mip.pool.intensity (defaut is 4)
    :param pool_capacity: the pool capacity (if any)
    :param eps_diff: precision to use for testing variable difference
    :param verbose: optional flag to print results.

    :return: the solution pool as returned by `docplex.mp.Model.populate()`
    """
    m = ModelReader.read(filename)
    assert m
    return populate_from_model(m, gap,
                               pool_intensity, pool_capacity, eps_diff, verbose)


def populate_from_model(mdl,
                        gap=0.1,
                        pool_intensity=4,
                        pool_capacity=None,
                        eps_diff=1e-7,
                        verbose=False):
    """ Runs populate on a model instance.

    :param mdl: a model instance.
    :param gap: MIP gap to use for the populate phase (default is 10%)
    :param pool_intensity: the value for the paramater mip.pool.intensity (defaut is 4)
    :param pool_capacity: the pool capacity (if any)
    :param eps_diff: precision to use for testing variable difference
    :param verbose: optional flag to print results.

    :return: the solution pool as returned by `docplex.mp.Model.populate()`
    """
    print(f"* running populate on model: '{mdl.name}', gap={gap}, intensity={pool_intensity}, capacity={pool_capacity}")
    # set the solution pool relative gap parameter to obtain solutions
    # of objective value within 10% of the optimal
    mdl.parameters.mip.pool.relgap = gap
    if pool_intensity is not None:
        assert 0 <= pool_intensity <= 4, f"Pool intensity must be in [0..4], {pool_intensity} was passed"
        mdl.parameters.mip.pool.intensity = pool_intensity
    if pool_capacity is not None:
        assert pool_capacity >= 1
        mdl.parameters.mip.pool.capacity = pool_capacity

    try:
        solnpool = mdl.populate_solution_pool(log_output=verbose)
    except Exception as ex:
        print("Exception raised during populate: {0}".format(str(ex)))
        return

    if not solnpool:
        print("! Model {0} fails to solve, no pool generated".format(mdl.name))

    print()
    print("* Solve status = '{0}'".format(mdl.solve_details.status))
    # Print information about the incumbent
    print()
    print("-- Objective value of the incumbent  = {0}".format(mdl.objective_value))
    sol = mdl.solution
    assert sol is not None

    # Print information about other solutions
    print()
    nb_pool_sols = solnpool.size
    print("-- The solution pool contains {0} solutions.".format(nb_pool_sols))

    numsolreplaced = solnpool.num_replaced
    print("-- %d solutions were removed due to the solution pool "
          "relative gap parameter." % numsolreplaced)

    print("* Pool objective statistics")
    solnpool.describe_objectives()

    print()
    print("#solution       objective       #var diff.")
    numcols = mdl.number_of_variables
    for s, sol_i in enumerate(solnpool, start=1):
        objval_i = sol_i.objective_value

        # compute the number of variables that differ in solution i and in the incumbent
        numdiff = 0
        for dv in mdl.iter_variables():
            dvv_i = sol_i[dv]
            dvv = sol[dv]
            if abs(dvv_i - dvv) >= eps_diff:
                numdiff += 1
        print("%-15s %-10g      %02d / %d" %
              (s, objval_i, numdiff, numcols))
    return solnpool


if __name__ == "__main__":
    from os.path import abspath, dirname, join
    import sys

    if len(sys.argv) == 1:
        filename = join(dirname(abspath(__file__)), "sports.lp")
    else:
        filename = sys.argv[1]
    populate_from_file(filename)


# * building sport scheduling model instance
# 37 games, 21 intradivisional, 16 interdivisional
# * running populate on model: 'sportSchedCPLEX', gap=0.2, intensity=3, capacity=13
# Version identifier: 20.1.0.0 | 2020-09-28 | 1fa7d7e06
# CPXPARAM_Read_DataCheck                          1
# CPXPARAM_MIP_Pool_Capacity                       13
# CPXPARAM_MIP_Pool_Intensity                      3
# CPXPARAM_MIP_Pool_RelGap                         0.20000000000000001
#
# Populate: phase I
# Tried aggregator 1 time.
# Reduced MIP has 5048 rows, 4440 columns, and 23976 nonzeros.
# Reduced MIP has 4440 binaries, 0 generals, 0 SOSs, and 0 indicators.
# Presolve time = 0.02 sec. (13.62 ticks)
# Probing time = 0.00 sec. (3.09 ticks)
# Tried aggregator 1 time.
# Reduced MIP has 5048 rows, 4440 columns, and 23976 nonzeros.
# Reduced MIP has 4440 binaries, 0 generals, 0 SOSs, and 0 indicators.
# Presolve time = 0.02 sec. (13.19 ticks)
# Probing time = 0.02 sec. (3.09 ticks)
# Clique table members: 4912.
# MIP emphasis: balance optimality and feasibility.
# MIP search method: dynamic search.
# Parallel mode: deterministic, using up to 12 threads.
# Root relaxation solution time = 0.22 sec. (160.99 ticks)
#
#         Nodes                                         Cuts/
#    Node  Left     Objective  IInf  Best Integer    Best Bound    ItCnt     Gap
#
# *     0+    0                        65154.0000   984200.0000              ---
# *     0+    0                        66386.0000   984200.0000              ---
#       0     0    95032.0000   690    66386.0000    95032.0000       10   43.15%
# *     0+    0                        95032.0000    95032.0000             0.00%
#
# Root node processing (before b&c):
#   Real time             =    1.27 sec. (1267.92 ticks)
# Parallel b&c, 12 threads:
#   Real time             =    0.00 sec. (0.00 ticks)
#   Sync time (average)   =    0.00 sec.
#   Wait time (average)   =    0.00 sec.
#                           ------------
# Total (root+branch&cut) =    1.27 sec. (1267.92 ticks)
#
# Populate: phase II
# MIP emphasis: balance optimality and feasibility.
# MIP search method: dynamic search.
# Parallel mode: deterministic, using up to 12 threads.
#
#         Nodes                                         Cuts/
#    Node  Left     Objective  IInf  Best Integer    Best Bound    ItCnt     Gap
#
#       0     2    95032.0000     1    95032.0000    95032.0000       10    0.00%
# Elapsed time = 1.38 sec. (1330.87 ticks, tree = 0.02 MB, solutions = 1)
#      13    11    95032.0000     1    95032.0000    95032.0000     1356    0.00%
#      14    13    95032.0000   177    95032.0000    95032.0000      682    0.00%
#      19     4    94942.0000   128    95032.0000    95032.0000     1596    0.00%
#      24    20    95032.0000    53    95032.0000    95032.0000     6009    0.00%
#      34    30    94942.0000   140    95032.0000    95032.0000    16312    0.00%
#      43    27    95032.0000    24    95032.0000    95032.0000    15340    0.00%
# *    55    48      integral     0    95032.0000    95032.0000    25086    0.00%
#      66    44    95032.0000    99    95032.0000    95032.0000    24510    0.00%
#      93    45    95032.0000   233    95032.0000    95032.0000    24470    0.00%
#     305   223    95032.0000   183    95032.0000    95032.0000    36558    0.00%
# Elapsed time = 10.47 sec. (4704.46 ticks, tree = 4.12 MB, solutions = 13)
#     469   362    94966.0000   360    95032.0000    95032.0000    47180    0.00%
#
# Root node processing (before b&c):
#   Real time             =    0.06 sec. (60.42 ticks)
# Parallel b&c, 12 threads:
#   Real time             =   11.98 sec. (4799.58 ticks)
#   Sync time (average)   =    1.07 sec.
#   Wait time (average)   =    0.00 sec.
#                           ------------
# Total (root+branch&cut) =   12.05 sec. (4860.00 ticks)
#
# * Solve status = 'populate solution limit exceeded'
#
# -- Objective value of the incumbent  = 95032.00000000003
#
# -- The solution pool contains 13 solutions.
# -- 11 solutions were removed due to the solution pool relative gap parameter.
# * Pool objective statistics
# count  = 13
# mean   = 95003.38461538461
# std    = 42.955322897675096
# min    = 94936.0
# med    = 95032.0
# max    = 95032.00000000003
#
# #solution       objective       #var diff.
# 1               95032           00 / 4440
# 2               94936           122 / 4440
# 3               95032           262 / 4440
# 4               94942           258 / 4440
# 5               95032           250 / 4440
# 6               95032           182 / 4440
# 7               95032           182 / 4440
# 8               95032           268 / 4440
# 9               94936           282 / 4440
# 10              95032           262 / 4440
# 11              94942           214 / 4440
# 12              95032           80 / 4440
# 13              95032           234 / 4440
#
# Process finished with exit code 0