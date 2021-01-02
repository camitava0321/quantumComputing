# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2018
# --------------------------------------------------------------------------

from collections import namedtuple

from docplex.mp.model import Model
from docplex.util.environment import get_environment


# ----------------------------------------------------------------------------
# Initialize the problem data
# ----------------------------------------------------------------------------
nbs = (8, 3, 2)

team_div1 = {"Baltimore Ravens", "Cincinnati Bengals", "Cleveland Browns",
             "Pittsburgh Steelers", "Houston Texans", "Indianapolis Colts",
             "Jacksonville Jaguars", "Tennessee Titans", "Buffalo Bills",
             "Miami Dolphins", "New England Patriots", "New York Jets",
             "Denver Broncos", "Kansas City Chiefs", "Oakland Raiders",
             "San Diego Chargers"}

team_div2 = {"Chicago Bears", "Detroit Lions", "Green Bay Packers",
             "Minnesota Vikings", "Atlanta Falcons", "Carolina Panthers",
             "New Orleans Saints", "Tampa Bay Buccaneers", "Dallas Cowboys",
             "New York Giants", "Philadelphia Eagles", "Washington Redskins",
             "Arizona Cardinals", "San Francisco 49ers", "Seattle Seahawks",
             "St. Louis Rams"}

Match = namedtuple("Matches", ["team1", "team2", "is_divisional"])


# ----------------------------------------------------------------------------
# Build the model
# ----------------------------------------------------------------------------
def build_sports(**kwargs):
    print("* building sport scheduling model instance")
    mdl = Model('sportSchedCPLEX', **kwargs)

    nb_teams_in_division, nb_intra_divisional, nb_inter_divisional = nbs
    assert len(team_div1) == len(team_div2)
    mdl.teams = list(team_div1 | team_div2)
    # team index ranges from 1 to 2N
    team_range = range(1, 2 * nb_teams_in_division + 1)

    # Calculate the number of weeks necessary.
    nb_weeks = (nb_teams_in_division - 1) * nb_intra_divisional + nb_teams_in_division * nb_inter_divisional
    weeks = range(1, nb_weeks + 1)
    mdl.weeks = weeks

    print("{0} games, {1} intradivisional, {2} interdivisional"
          .format(nb_weeks, (nb_teams_in_division - 1) * nb_intra_divisional,
                  nb_teams_in_division * nb_inter_divisional))

    # Season is split into two halves.
    first_half_weeks = range(1, nb_weeks // 2 + 1)
    nb_first_half_games = nb_weeks // 3

    # All possible matches (pairings) and whether of not each is intradivisional.
    matches = [Match(t1, t2, 1 if (t2 <= nb_teams_in_division or t1 > nb_teams_in_division) else 0)
               for t1 in team_range for t2 in team_range if t1 < t2]
    mdl.matches = matches
    # Number of games to play between pairs depends on
    # whether the pairing is intradivisional or not.
    nb_play = {m: nb_intra_divisional if m.is_divisional == 1 else nb_inter_divisional for m in matches}

    plays = mdl.binary_var_matrix(keys1=matches, keys2=weeks,
                                  name=lambda mw: "play_%d_%d_w%d" % (mw[0].team1, mw[0].team2, mw[1]))
    mdl.plays = plays

    for m in matches:
        mdl.add_constraint(mdl.sum(plays[m, w] for w in weeks) == nb_play[m],
                           "correct_nb_games_%d_%d" % (m.team1, m.team2))

    for w in weeks:
        # Each team must play exactly once in a week.
        for t in team_range:
            max_teams_in_division = (plays[m, w] for m in matches if m.team1 == t or m.team2 == t)
            mdl.add_constraint(mdl.sum(max_teams_in_division) == 1,
                               "plays_exactly_once_%d_%s" % (w, t))

    # Games between the same teams cannot be on successive weeks.
    mdl.add_constraints(plays[m, w] + plays[m, w + 1] <= 1
                        for w in weeks for m in matches if w < nb_weeks)

    # Some intradivisional games should be in the first half.
    for t in team_range:
        max_teams_in_division = [plays[m, w] for w in first_half_weeks for m in matches if
                                 m.is_divisional == 1 and (m.team1 == t or m.team2 == t)]

        mdl.add_constraint(mdl.sum(max_teams_in_division) >= nb_first_half_games,
                           "in_division_first_half_%s" % t)

    # postpone divisional matches as much as possible
    # we weight each play variable with the square of w.
    mdl.maximize(mdl.sum(plays[m, w] * w * w for w in weeks for m in matches if m.is_divisional))
    return mdl

# a named tuple to store solution
TSolution = namedtuple("TSolution", ["week", "is_divisional", "team1", "team2"])


def print_sports_solution(mdl):
    # iterate with weeks first
    solution = [TSolution(w, m.is_divisional, mdl.teams[m.team1], mdl.teams[m.team2])
                for w in mdl.weeks for m in mdl.matches
                if mdl.plays[m, w].to_bool()]

    currweek = 0
    print("Intradivisional games are marked with a *")
    for s in solution:
        # assume records are sorted by increasing week indices.
        if s.week != currweek:
            currweek = s.week
            print(" == == == == == == == == == == == == == == == == ")
            print("On week %d" % currweek)

        print("    {0:s}{1} will meet the {2}".format("*" if s.is_divisional else "", s.team1, s.team2))


# ----------------------------------------------------------------------------
# Solve the model and display the result
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    # Build the model
    model = build_sports()
    model.print_information()
    # Solve the model. If a key has been specified above, the solve
    # will use IBM Decision Optimization on cloud.
    if model.solve():
        model.report()
        print_sports_solution(model)
        # Save the CPLEX solution as "solution.json" program output
        with get_environment().get_output_stream("solution.json") as fp:
            model.solution.export(fp, "json")
    else:
        print("Problem could not be solved: " + model.solve_details.get_status())
