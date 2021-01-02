# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2018
# --------------------------------------------------------------------------

# Source: http://blog.yhathq.com/posts/how-yhat-does-cloud-balancing.html

from collections import namedtuple

from docplex.mp.model import Model


# ----------------------------------------------------------------------------
# Initialize the problem data
# ----------------------------------------------------------------------------
class TUser(namedtuple("TUser", ["id", "running", "sleeping", "current_server"])):
    def __str__(self):
        return self.id


SERVERS = ["server002", "server003", "server001", "server006", "server007", "server004", "server005"]

USERS = [("user013", 2, 1, "server002"),
         ("user014", 0, 2, "server002"),
         ("user015", 0, 4, "server002"),
         ("user016", 1, 4, "server002"),
         ("user017", 0, 3, "server002"),
         ("user018", 0, 2, "server002"),
         ("user019", 0, 2, "server002"),
         ("user020", 0, 1, "server002"),
         ("user021", 4, 4, "server002"),
         ("user022", 0, 1, "server002"),
         ("user023", 0, 3, "server002"),
         ("user024", 1, 2, "server002"),
         ("user025", 0, 1, "server003"),
         ("user026", 0, 1, "server003"),
         ("user027", 1, 1, "server003"),
         ("user028", 0, 1, "server003"),
         ("user029", 2, 1, "server003"),
         ("user030", 0, 5, "server003"),
         ("user031", 0, 2, "server003"),
         ("user032", 0, 3, "server003"),
         ("user033", 1, 1, "server003"),
         ("user034", 0, 1, "server003"),
         ("user035", 0, 1, "server003"),
         ("user036", 4, 1, "server003"),
         ("user037", 7, 1, "server003"),
         ("user038", 2, 1, "server003"),
         ("user039", 0, 3, "server003"),
         ("user040", 1, 2, "server003"),
         ("user001", 0, 2, "server001"),
         ("user002", 0, 3, "server001"),
         ("user003", 5, 4, "server001"),
         ("user004", 0, 1, "server001"),
         ("user005", 0, 1, "server001"),
         ("user006", 0, 2, "server001"),
         ("user007", 0, 4, "server001"),
         ("user008", 0, 1, "server001"),
         ("user009", 5, 1, "server001"),
         ("user010", 7, 1, "server001"),
         ("user011", 4, 5, "server001"),
         ("user012", 0, 4, "server001"),
         ("user062", 0, 1, "server006"),
         ("user063", 3, 5, "server006"),
         ("user064", 0, 1, "server006"),
         ("user065", 0, 3, "server006"),
         ("user066", 3, 1, "server006"),
         ("user067", 0, 1, "server006"),
         ("user068", 0, 1, "server006"),
         ("user069", 0, 2, "server006"),
         ("user070", 3, 2, "server006"),
         ("user071", 0, 1, "server006"),
         ("user072", 5, 3, "server006"),
         ("user073", 0, 1, "server006"),
         ("user074", 0, 1, "server006"),
         ("user075", 0, 2, "server007"),
         ("user076", 1, 1, "server007"),
         ("user077", 1, 1, "server007"),
         ("user078", 0, 1, "server007"),
         ("user079", 0, 3, "server007"),
         ("user080", 0, 1, "server007"),
         ("user081", 4, 1, "server007"),
         ("user082", 1, 1, "server007"),
         ("user041", 0, 1, "server004"),
         ("user042", 2, 1, "server004"),
         ("user043", 5, 2, "server004"),
         ("user044", 5, 2, "server004"),
         ("user045", 0, 2, "server004"),
         ("user046", 1, 5, "server004"),
         ("user047", 0, 1, "server004"),
         ("user048", 0, 3, "server004"),
         ("user049", 5, 1, "server004"),
         ("user050", 0, 2, "server004"),
         ("user051", 0, 3, "server004"),
         ("user052", 0, 3, "server004"),
         ("user053", 0, 1, "server004"),
         ("user054", 0, 2, "server004"),
         ("user055", 0, 3, "server005"),
         ("user056", 3, 1, "server005"),
         ("user057", 0, 3, "server005"),
         ("user058", 0, 2, "server005"),
         ("user059", 0, 1, "server005"),
         ("user060", 0, 5, "server005"),
         ("user061", 0, 2, "server005")
         ]

# ----------------------------------------------------------------------------
# Prepare the data for modeling
# ----------------------------------------------------------------------------
DEFAULT_MAX_PROCESSES_PER_SERVER = 50


def _is_migration(user, server):
    """ Returns True if server is not the user's current
        Used in setup of constraints.
    """
    return server != user.current_server


# ----------------------------------------------------------------------------
# Build the model
# ----------------------------------------------------------------------------

def build_load_balancing_model(servers, users_, max_process_per_server=DEFAULT_MAX_PROCESSES_PER_SERVER, **kwargs):
    m = Model(name='load_balancing', **kwargs)

    # decision objects

    users = [TUser(*user_row) for user_row in users_]

    active_var_by_server = m.binary_var_dict(servers, name='isActive')

    def user_server_pair_namer(u_s):
        u, s = u_s
        return '%s_to_%s' % (u.id, s)

    assign_user_to_server_vars = m.binary_var_matrix(users, servers, user_server_pair_namer)

    m.add_constraints(
        m.sum(assign_user_to_server_vars[u, s] * u.running for u in users) <= max_process_per_server for s in servers)
    # each assignment var <u, s>  is <= active_server(s)
    for s in servers:
        for u in users:
            ct_name = 'ct_assign_to_active_{0!s}_{1!s}'.format(u, s)
            m.add_constraint(assign_user_to_server_vars[u, s] <= active_var_by_server[s], ct_name)

        # sum of assignment vars for (u, all s in servers) == 1
        for u in users:
            ct_name = 'ct_unique_server_%s' % (u[0])
            m.add_constraint(m.sum((assign_user_to_server_vars[u, s] for s in servers)) == 1, ct_name)

    number_of_active_servers = m.sum((active_var_by_server[svr] for svr in servers))
    m.add_kpi(number_of_active_servers, "Number of active servers")

    number_of_migrations = m.sum(
        assign_user_to_server_vars[u, s] for u in users for s in servers if
        _is_migration(u, s))
    m.add_kpi(number_of_migrations, "Total number of migrations")

    max_sleeping_workload = m.integer_var(name="max_sleeping_processes")
    for s in servers:
        ct_name = 'ct_define_max_sleeping_%s' % s
        m.add_constraint(
            m.sum(
                assign_user_to_server_vars[u, s] * u.sleeping for u in users) <= max_sleeping_workload,
            ct_name)
    m.add_kpi(max_sleeping_workload, "Max sleeping workload")
    # Set objective function
    # m.minimize(number_of_active_servers)
    m.minimize_static_lex([number_of_active_servers, number_of_migrations, max_sleeping_workload])

    # attach artefacts to model for reporting
    m.users = users
    m.servers = servers
    m.active_var_by_server = active_var_by_server
    m.assign_user_to_server_vars = assign_user_to_server_vars
    m.max_sleeping_workload = max_sleeping_workload

    return m


def lb_report(mdl):
    active_servers = sorted([s for s in mdl.servers if mdl.active_var_by_server[s].solution_value == 1])
    print("Active Servers: {0} = {1}".format(len(active_servers), active_servers))
    print("*** User/server assignments , #migrations={0} ***".format(
        mdl.kpi_by_name("number of migrations").solution_value))
    # for (u, s) in sorted(mdl.assign_user_to_server_vars):
    #     if mdl.assign_user_to_server_vars[(u, s)].solution_value == 1:
    #         print("{} uses {}, migration: {}".format(u, s, "yes" if _is_migration(u, s) else "no"))
    print("*** Servers sleeping processes ***")
    for s in active_servers:
        sleeping = sum(mdl.assign_user_to_server_vars[u, s].solution_value * u.sleeping for u in mdl.users)
        print("Server: {} #sleeping={}".format(s, sleeping))


def make_default_load_balancing_model(**kwargs):
    return build_load_balancing_model(SERVERS, USERS, **kwargs)


def lb_save_solution_as_json(mdl, json_file):
    """Saves the solution for this model as JSON.

    Note that this is not a CPLEX Solution file, as this is the result of post-processing a CPLEX solution
    """
    import json
    solution_dict = {}
    # active server
    active_servers = sorted([s for s in mdl.servers if mdl.active_var_by_server[s].solution_value == 1])
    solution_dict["active servers"] = active_servers

    # sleeping processes by server
    sleeping_processes = {}
    for s in active_servers:
        sleeping = sum(mdl.assign_user_to_server_vars[u, s].solution_value * u.sleeping for u in mdl.users)
        sleeping_processes[s] = sleeping
    solution_dict["sleeping processes by server"] = sleeping_processes

# user assignment
    user_assignment = []
    for (u, s) in sorted(mdl.assign_user_to_server_vars):
        if mdl.assign_user_to_server_vars[(u, s)].solution_value == 1:
            n = {
                'user': u.id,
                'server': s,
                'migration': "yes" if _is_migration(u, s) else "no"
            }
            user_assignment.append(n)
    solution_dict['user assignment'] = user_assignment
    json_file.write(json.dumps(solution_dict, indent=3).encode('utf-8'))

# ----------------------------------------------------------------------------
# Solve the model and display the result
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    lbm = make_default_load_balancing_model()

    # Run the model.
    lbs = lbm.solve(log_output=True)
    lb_report(lbm)
    # save json, used in worker tests
    from docplex.util.environment import get_environment
    with get_environment().get_output_stream("solution.json") as fp:
        lb_save_solution_as_json(lbm, fp)

