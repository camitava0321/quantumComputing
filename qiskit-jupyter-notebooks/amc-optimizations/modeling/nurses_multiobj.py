# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2018
# --------------------------------------------------------------------------

from collections import namedtuple

from docplex.mp.model import Model
from docplex.mp.constants import ObjectiveSense
from docplex.util.environment import get_environment

# ----------------------------------------------------------------------------
# Initialize the problem data
# ----------------------------------------------------------------------------

# utility to convert a weekday string to an index in 0..6
_all_days = ["monday",
             "tuesday",
             "wednesday",
             "thursday",
             "friday",
             "saturday",
             "sunday"]


def day_to_day_week(day):
    day_map = {day: d for d, day in enumerate(_all_days)}
    return day_map[day.lower()]


TWorkRules = namedtuple("TWorkRules", ["work_time_max"])
TVacation = namedtuple("TVacation", ["nurse", "day"])
TNursePair = namedtuple("TNursePair", ["firstNurse", "secondNurse"])
TSkillRequirement = namedtuple("TSkillRequirement", ["department", "skill", "required"])


NURSES = [("Anne", 11, 1, 25),
          ("Bethanie", 4, 5, 28),
          ("Betsy", 2, 2, 17),
          ("Cathy", 2, 2, 17),
          ("Cecilia", 9, 5, 38),
          ("Chris", 11, 4, 38),
          ("Cindy", 5, 2, 21),
          ("David", 1, 2, 15),
          ("Debbie", 7, 2, 24),
          ("Dee", 3, 3, 21),
          ("Gloria", 8, 2, 25),
          ("Isabelle", 3, 1, 16),
          ("Jane", 3, 4, 23),
          ("Janelle", 4, 3, 22),
          ("Janice", 2, 2, 17),
          ("Jemma", 2, 4, 22),
          ("Joan", 5, 3, 24),
          ("Joyce", 8, 3, 29),
          ("Jude", 4, 3, 22),
          ("Julie", 6, 2, 22),
          ("Juliet", 7, 4, 31),
          ("Kate", 5, 3, 24),
          ("Nancy", 8, 4, 32),
          ("Nathalie", 9, 5, 38),
          ("Nicole", 0, 2, 14),
          ("Patricia", 1, 1, 13),
          ("Patrick", 6, 1, 19),
          ("Roberta", 3, 5, 26),
          ("Suzanne", 5, 1, 18),
          ("Vickie", 7, 1, 20),
          ("Wendie", 5, 2, 21),
          ("Zoe", 8, 3, 29)
          ]

SHIFTS = [("Emergency", "monday", 2, 8, 3, 5),
          ("Emergency", "monday", 8, 12, 4, 7),
          ("Emergency", "monday", 12, 18, 2, 5),
          ("Emergency", "monday", 18, 2, 3, 7),
          ("Consultation", "monday", 8, 12, 10, 13),
          ("Consultation", "monday", 12, 18, 8, 12),
          ("Cardiac_Care", "monday", 8, 12, 10, 13),
          ("Cardiac_Care", "monday", 12, 18, 8, 12),
          ("Emergency", "tuesday", 8, 12, 4, 7),
          ("Emergency", "tuesday", 12, 18, 2, 5),
          ("Emergency", "tuesday", 18, 2, 3, 7),
          ("Consultation", "tuesday", 8, 12, 10, 13),
          ("Consultation", "tuesday", 12, 18, 8, 12),
          ("Cardiac_Care", "tuesday", 8, 12, 4, 7),
          ("Cardiac_Care", "tuesday", 12, 18, 2, 5),
          ("Cardiac_Care", "tuesday", 18, 2, 3, 7),
          ("Emergency", "wednesday", 2, 8, 3, 5),
          ("Emergency", "wednesday", 8, 12, 4, 7),
          ("Emergency", "wednesday", 12, 18, 2, 5),
          ("Emergency", "wednesday", 18, 2, 3, 7),
          ("Consultation", "wednesday", 8, 12, 10, 13),
          ("Consultation", "wednesday", 12, 18, 8, 12),
          ("Emergency", "thursday", 2, 8, 3, 5),
          ("Emergency", "thursday", 8, 12, 4, 7),
          ("Emergency", "thursday", 12, 18, 2, 5),
          ("Emergency", "thursday", 18, 2, 3, 7),
          ("Consultation", "thursday", 8, 12, 10, 13),
          ("Consultation", "thursday", 12, 18, 8, 12),
          ("Emergency", "friday", 2, 8, 3, 5),
          ("Emergency", "friday", 8, 12, 4, 7),
          ("Emergency", "friday", 12, 18, 2, 5),
          ("Emergency", "friday", 18, 2, 3, 7),
          ("Consultation", "friday", 8, 12, 10, 13),
          ("Consultation", "friday", 12, 18, 8, 12),
          ("Emergency", "saturday", 2, 12, 5, 7),
          ("Emergency", "saturday", 12, 20, 7, 9),
          ("Emergency", "saturday", 20, 2, 12, 12),
          ("Emergency", "sunday", 2, 12, 5, 7),
          ("Emergency", "sunday", 12, 20, 7, 9),
          ("Emergency", "sunday", 20, 2, 12, 12),
          ("Geriatrics", "sunday", 8, 10, 2, 5)]

NURSE_SKILLS = {"Anne": ["Anaesthesiology", "Oncology", "Pediatrics"],
                "Betsy": ["Cardiac_Care"],
                "Cathy": ["Anaesthesiology"],
                "Cecilia": ["Anaesthesiology", "Oncology", "Pediatrics"],
                "Chris": ["Cardiac_Care", "Oncology", "Geriatrics"],
                "Gloria": ["Pediatrics"], "Jemma": ["Cardiac_Care"],
                "Joyce": ["Anaesthesiology", "Pediatrics"],
                "Julie": ["Geriatrics"], "Juliet": ["Pediatrics"],
                "Kate": ["Pediatrics"], "Nancy": ["Cardiac_Care"],
                "Nathalie": ["Anaesthesiology", "Geriatrics"],
                "Patrick": ["Oncology"], "Suzanne": ["Pediatrics"],
                "Wendie": ["Geriatrics"],
                "Zoe": ["Cardiac_Care"]
                }

VACATIONS = [("Anne", "friday"),
             ("Anne", "sunday"),
             ("Cathy", "thursday"),
             ("Cathy", "tuesday"),
             ("Joan", "thursday"),
             ("Joan", "saturday"),
             ("Juliet", "monday"),
             ("Juliet", "tuesday"),
             ("Juliet", "thursday"),
             ("Nathalie", "sunday"),
             ("Nathalie", "thursday"),
             ("Isabelle", "monday"),
             ("Isabelle", "thursday"),
             ("Patricia", "saturday"),
             ("Patricia", "wednesday"),
             ("Nicole", "friday"),
             ("Nicole", "wednesday"),
             ("Jude", "tuesday"),
             ("Jude", "friday"),
             ("Debbie", "saturday"),
             ("Debbie", "wednesday"),
             ("Joyce", "sunday"),
             ("Joyce", "thursday"),
             ("Chris", "thursday"),
             ("Chris", "tuesday"),
             ("Cecilia", "friday"),
             ("Cecilia", "wednesday"),
             ("Patrick", "saturday"),
             ("Patrick", "sunday"),
             ("Cindy", "sunday"),
             ("Dee", "tuesday"),
             ("Dee", "friday"),
             ("Jemma", "friday"),
             ("Jemma", "wednesday"),
             ("Bethanie", "wednesday"),
             ("Bethanie", "tuesday"),
             ("Betsy", "monday"),
             ("Betsy", "thursday"),
             ("David", "monday"),
             ("Gloria", "monday"),
             ("Jane", "saturday"),
             ("Jane", "sunday"),
             ("Janelle", "wednesday"),
             ("Janelle", "friday"),
             ("Julie", "sunday"),
             ("Kate", "tuesday"),
             ("Kate", "monday"),
             ("Nancy", "sunday"),
             ("Roberta", "friday"),
             ("Roberta", "saturday"),
             ("Janice", "tuesday"),
             ("Janice", "friday"),
             ("Suzanne", "monday"),
             ("Vickie", "wednesday"),
             ("Vickie", "friday"),
             ("Wendie", "thursday"),
             ("Wendie", "saturday"),
             ("Zoe", "saturday"),
             ("Zoe", "sunday")]

NURSE_ASSOCIATIONS = [("Isabelle", "Dee"),
                      ("Anne", "Patrick")]

NURSE_INCOMPATIBILITIES = [("Patricia", "Patrick"),
                           ("Janice", "Wendie"),
                           ("Suzanne", "Betsy"),
                           ("Janelle", "Jane"),
                           ("Gloria", "David"),
                           ("Dee", "Jemma"),
                           ("Bethanie", "Dee"),
                           ("Roberta", "Zoe"),
                           ("Nicole", "Patricia"),
                           ("Vickie", "Dee"),
                           ("Joan", "Anne")
                           ]

SKILL_REQUIREMENTS = [("Emergency", "Cardiac_Care", 1)]

DEFAULT_WORK_RULES = TWorkRules(40)


# ----------------------------------------------------------------------------
# Prepare the data for modeling
# ----------------------------------------------------------------------------
# subclass the namedtuple to refine the str() method as the nurse's name
class TNurse(namedtuple("TNurse1", ["name", "seniority", "qualification", "pay_rate"])):
    def __str__(self):
        return self.name


# specialized namedtuple to redefine its str() method
class TShift(namedtuple("TShift",
                        ["department", "day", "start_time", "end_time", "min_requirement", "max_requirement"])):

    def __str__(self):
        # keep first two characters in department, uppercase
        dept2 = self.department[0:4].upper()
        # keep 3 days of weekday
        dayname = self.day[0:3]
        return '{}_{}_{:02d}'.format(dept2, dayname, self.start_time).replace(" ", "_")


class ShiftActivity(object):
    @staticmethod
    def to_abstime(day_index, time_of_day):
        """ Convert a pair (day_index, time) into a number of hours since Monday 00:00

        :param day_index: The index of the day from 1 to 7 (Monday is 1).
        :param time_of_day: An integer number of hours.

        :return:
        """
        time = 24 * (day_index - 1)
        time += time_of_day
        return time

    def __init__(self, weekday, start_time_of_day, end_time_of_day):
        assert (start_time_of_day >= 0)
        assert (start_time_of_day <= 24)
        assert (end_time_of_day >= 0)
        assert (end_time_of_day <= 24)

        self._weekday = weekday
        self._start_time_of_day = start_time_of_day
        self._end_time_of_day = end_time_of_day
        # conversion to absolute time.
        start_day_index = day_to_day_week(self._weekday)
        self.start_time = self.to_abstime(start_day_index, start_time_of_day)
        end_day_index = start_day_index if end_time_of_day > start_time_of_day else start_day_index + 1
        self.end_time = self.to_abstime(end_day_index, end_time_of_day)
        assert self.end_time > self.start_time

    @property
    def duration(self):
        return self.end_time - self.start_time

    def overlaps(self, other_shift):
        if not isinstance(other_shift, ShiftActivity):
            return False
        else:
            return other_shift.end_time > self.start_time and other_shift.start_time < self.end_time


def solve(model, **kwargs):
    # Here, we set the number of threads for CPLEX to 2 and set the time limit to 2mins.
    model.parameters.threads = 2
    model.parameters.mip.tolerances.mipgap = 0.000001
    model.parameters.timelimit = 120  # nurse should not take more than that !
    sol = model.solve(log_output=True, **kwargs)
    if sol is not None:
        print("solution for a cost of {}".format(model.objective_value))
        print_information(model)
        # print_solution(model)
        return model.objective_value
    else:
        print("* model is infeasible")
        return None


def load_data(model, shifts_, nurses_, nurse_skills, vacations_=None,
              nurse_associations_=None, nurse_imcompatibilities_=None):
    """ Usage: load_data(shifts, nurses, nurse_skills, vacations) """
    model.number_of_overlaps = 0
    model.work_rules = DEFAULT_WORK_RULES
    model.shifts = [TShift(*shift_row) for shift_row in shifts_]
    model.nurses = [TNurse(*nurse_row) for nurse_row in nurses_]
    model.skill_requirements = SKILL_REQUIREMENTS
    model.nurse_skills = nurse_skills
    # transactional data
    model.vacations = [TVacation(*vacation_row) for vacation_row in vacations_] if vacations_ else []
    model.nurse_associations = [TNursePair(*npr) for npr in nurse_associations_]\
    if nurse_associations_ else []
    model.nurse_incompatibilities = [TNursePair(*npr) for npr in nurse_imcompatibilities_]\
    if nurse_imcompatibilities_ else []

    # computed
    model.departments = set(sh.department for sh in model.shifts)


    print('#nurses: {0}'.format(len(model.nurses)))
    print('#shifts: {0}'.format(len(model.shifts)))
    print('#vacations: {0}'.format(len(model.vacations)))
    print("#associations=%d" % len(model.nurse_associations))
    print("#incompatibilities=%d" % len(model.nurse_incompatibilities))


def setup_data(model):
    """ compute internal data """
    # compute shift activities (start, end duration) and stor ethem in a dict indexed by shifts
    model.shift_activities = {s: ShiftActivity(s.day, s.start_time, s.end_time) for s in model.shifts}
    # map from nurse names to nurse tuples.
    model.nurses_by_id = {n.name: n for n in model.nurses}


def setup_variables(model):
    all_nurses, all_shifts = model.nurses, model.shifts
    # one binary variable for each pair (nurse, shift) equal to 1 iff nurse n is assigned to shift s
    model.nurse_assignment_vars = model.binary_var_matrix(all_nurses, all_shifts, 'NurseAssigned')
    # for each nurse, allocate one variable for work time
    model.nurse_work_time_vars = model.continuous_var_dict(all_nurses, lb=0, name='NurseWorkTime')
    # and two variables for over_average and under-average work time
    model.nurse_over_average_time_vars = model.continuous_var_dict(all_nurses, lb=0,
                                                                   name='NurseOverAverageWorkTime')
    model.nurse_under_average_time_vars = model.continuous_var_dict(all_nurses, lb=0,
                                                                    name='NurseUnderAverageWorkTime')
    # finally the global average work time
    model.average_nurse_work_time = model.continuous_var(lb=0, name='AverageWorkTime')


def setup_constraints(model):
    all_nurses = model.nurses
    all_shifts = model.shifts
    nurse_assigned = model.nurse_assignment_vars
    nurse_work_time = model.nurse_work_time_vars
    shift_activities = model.shift_activities
    nurses_by_id = model.nurses_by_id
    max_work_time = model.work_rules.work_time_max

    # define average
    model.add_constraint(
        len(all_nurses) * model.average_nurse_work_time == model.sum(nurse_work_time[n] for n in all_nurses), "average")

    # compute nurse work time , average and under, over
    for n in all_nurses:
        work_time_var = nurse_work_time[n]
        model.add_constraint(
            work_time_var == model.sum(nurse_assigned[n, s] * shift_activities[s].duration for s in all_shifts),
            "work_time_{0!s}".format(n))

        # relate over/under average worktime variables to the worktime variables
        # the trick here is that variables have zero lower bound
        # however, thse variables are not completely defined by this constraint,
        # only their difference is.
        # if these variables are part of the objective, CPLEX wil naturally minimize their value,
        # as expected
        model.add_constraint(
            work_time_var == model.average_nurse_work_time
            + model.nurse_over_average_time_vars[n]
            - model.nurse_under_average_time_vars[n],
            "average_work_time_{0!s}".format(n))

        # state the maximum work time as a constraint, so that is can be relaxed,
        # should the problem become infeasible.
        model.add_constraint(work_time_var <= max_work_time, "max_time_{0!s}".format(n))

    # vacations
    v = 0
    for vac_nurse_id, vac_day in model.vacations:
        vac_n = nurses_by_id[vac_nurse_id]
        for shift in (s for s in all_shifts if s.day == vac_day):
            v += 1
            model.add_constraint(nurse_assigned[vac_n, shift] == 0,
                                 "medium_vacations_{0!s}_{1!s}_{2!s}".format(vac_n, vac_day, shift))
    #print('#vacation cts: {0}'.format(v))

    # a nurse cannot be assigned overlapping shifts
    # post only one constraint per couple(s1, s2)
    number_of_overlaps = 0
    nb_shifts = len(all_shifts)
    for i1 in range(nb_shifts):
        for i2 in range(i1 + 1, nb_shifts):
            s1 = all_shifts[i1]
            s2 = all_shifts[i2]
            if shift_activities[s1].overlaps(shift_activities[s2]):
                number_of_overlaps += 1
                for n in all_nurses:
                    model.add_constraint(nurse_assigned[n, s1] + nurse_assigned[n, s2] <= 1,
                                         "high_overlapping_{0!s}_{1!s}_{2!s}".format(s1, s2, n))
    #print('# overlapping cts: {0}'.format(number_of_overlaps))

    for s in all_shifts:
        demand_min = s.min_requirement
        demand_max = s.max_requirement
        total_assigned = model.sum(nurse_assigned[n, s] for n in model.nurses)
        model.add_constraint(total_assigned >= demand_min,
                             "high_req_min_{0!s}_{1}".format(s, demand_min))
        model.add_constraint(total_assigned <= demand_max,
                             "medium_req_max_{0!s}_{1}".format(s, demand_max))

    for (dept, skill, required) in model.skill_requirements:
        if required > 0:
            for dsh in (s for s in all_shifts if dept == s.department):
                model.add_constraint(model.sum(nurse_assigned[skilled_nurse, dsh] for skilled_nurse in
                                               (n for n in all_nurses if
                                                n.name in model.nurse_skills.keys() and skill in model.nurse_skills[
                                                    n.name])) >= required,
                                     "high_required_{0!s}_{1!s}_{2!s}_{3!s}".format(dept, skill, required, dsh))

    # nurse-nurse associations
    # for each pair of associated nurses, their assignment variables are equal
    # over all shifts.
    c = 0
    for (nurse_id1, nurse_id2) in model.nurse_associations:
        if nurse_id1 in nurses_by_id and nurse_id2 in nurses_by_id:
            nurse1 = nurses_by_id[nurse_id1]
            nurse2 = nurses_by_id[nurse_id2]
            for s in all_shifts:
                c += 1
                ctname = 'medium_ct_nurse_assoc_{0!s}_{1!s}_{2:d}'.format(nurse_id1, nurse_id2, c)
                model.add_constraint(nurse_assigned[nurse1, s] == nurse_assigned[nurse2, s], ctname)

    # nurse-nurse incompatibilities
    # for each pair of incompatible nurses, the sum of assigned variables is less than one
    # in other terms, both nurses can never be assigned to the same shift
    c = 0
    for (nurse_id1, nurse_id2) in model.nurse_incompatibilities:
        if nurse_id1 in nurses_by_id and nurse_id2 in nurses_by_id:
            nurse1 = nurses_by_id[nurse_id1]
            nurse2 = nurses_by_id[nurse_id2]
            for s in all_shifts:
                c += 1
                ctname = 'medium_ct_nurse_incompat_{0!s}_{1!s}_{2:d}'.format(nurse_id1, nurse_id2, c)
                model.add_constraint(nurse_assigned[nurse1, s] + nurse_assigned[nurse2, s] <= 1, ctname)

    model.total_number_of_assignments = model.sum(nurse_assigned[n, s] for n in all_nurses for s in all_shifts)
    model.nurse_costs = [model.nurse_assignment_vars[n, s] * n.pay_rate * model.shift_activities[s].duration for n in
                         model.nurses
                         for s in model.shifts]
    model.total_salary_cost = model.sum(model.nurse_costs)


def setup_objective(model):
    model.add_kpi(model.total_salary_cost, "Total salary cost")
    model.add_kpi(model.total_number_of_assignments, "Total number of assignments")
    model.add_kpi(model.average_nurse_work_time, "average work time")

    total_over_average_worktime = model.sum(model.nurse_over_average_time_vars[n] for n in model.nurses)
    total_under_average_worktime = model.sum(model.nurse_under_average_time_vars[n] for n in model.nurses)
    model.add_kpi(total_over_average_worktime, "Total over-average worktime")
    model.add_kpi(total_under_average_worktime, "Total under-average worktime")
    total_fairness = total_over_average_worktime + total_under_average_worktime
    model.add_kpi(total_fairness, "Total fairness")

    model.minimize_static_lex([model.total_salary_cost, total_fairness, model.total_number_of_assignments])


def print_information(model):
    print("#shifts=%d" % len(model.shifts))
    print("#nurses=%d" % len(model.nurses))
    print("#vacations=%d" % len(model.vacations))
    print("#nurse skills=%d" % len(model.nurse_skills))
    print("#nurse associations=%d" % len(model.nurse_associations))
    print("#incompatibilities=%d" % len(model.nurse_incompatibilities))
    model.print_information()
    model.report_kpis()


def print_solution(model):
    print("*************************** Solution ***************************")
    print("Allocation By Department:")
    for d in model.departments:
        print("\t{}: {}".format(d, sum(
            model.nurse_assignment_vars[n, s].solution_value for n in model.nurses for s in model.shifts if
            s.department == d)))
    print("Cost By Department:")
    for d in model.departments:
        cost = sum(
            model.nurse_assignment_vars[n, s].solution_value * n.pay_rate * model.shift_activities[s].duration for n in
            model.nurses for s in model.shifts if s.department == d)
        print("\t{}: {}".format(d, cost))
    print("Nurses Assignments")
    for n in sorted(model.nurses):
        total_hours = sum(
            model.nurse_assignment_vars[n, s].solution_value * model.shift_activities[s].duration for s in model.shifts)
        print("\t{}: total hours:{}".format(n.name, total_hours))
        for s in model.shifts:
            if model.nurse_assignment_vars[n, s].solution_value == 1:
                print("\t\t{}: {} {}-{}".format(s.day, s.department, s.start_time, s.end_time))


# ----------------------------------------------------------------------------
# Build the model
# ----------------------------------------------------------------------------

def build(context=None, **kwargs):
    mdl = Model("Nurses", context=context, **kwargs)
    load_data(mdl, SHIFTS, NURSES, NURSE_SKILLS, VACATIONS, NURSE_ASSOCIATIONS,
              NURSE_INCOMPATIBILITIES)
    setup_data(mdl)
    setup_variables(mdl)
    setup_constraints(mdl)
    setup_objective(mdl)
    return mdl


# ----------------------------------------------------------------------------
# Solve the model and display the result
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    # Build model
    model = build()

    # Solve the model and print solution
    solve(model)

    print(model.solve_details)

    # Save the CPLEX solution as "solution.json" program output
    with get_environment().get_output_stream("solution.json") as fp:
        model.solution.export(fp, "json")
