import pulp
import json
from itertools import product
import unidecode
from math import exp
import sys

# Potential ameliorations:
    # Take into account 0.5 in availability ("Maybe")
    # Being able to specify the tolerance for the number of person in each group (actually set to 1 person)

def main(target_number, dispo_file_path, previous_groups_file_path):

    # Warning
    print("\nWarning: Names have to be carefuly and properly written in files")


    # Import arguments

    # target_number is the desired number of people in each group
    # Groups will be made plus/minus 1 person of target_number
    target_number = int(target_number)

    ## File of availabilities (imported from a doodle and already pre-processed)
    ### Header = "Name" + dates
    ### Each row is name and 0 or 1 for each date
    dispo_file = dispo_file_path

    ## File of previous groups
    ### Template: list of previous groups in the format [Ordinal of session, [list of people names]]
    previous_groups_file = previous_groups_file_path





    # Generate data for solving the optimization problem

    ## Create lists of data

    ### constraints is the availability list of people list (0 or 1)
    ### all dates and people are in the same order in their list than in the constraint matrix
    constraints = []
    people_names = []
    date_names = []
    previous_groups_raw = []

    ## Read dispo file to generate constraint matrix but also names and dates
    with open(dispo_file, newline='') as csvfile:
        import csv
        csv = csv.reader(csvfile, delimiter=';')
        header = True
        for row in csv:
            if header:
                date_names = row[1:]
                header = False
            else:
                people_names.append(unidecode.unidecode(row[0]))
                constraints.append(row[1:])

    people = [i for i in range(len(people_names))]
    dates = [j for j in range(len(date_names))]

    ## Import the file of previous groups
    with open(previous_groups_file) as json_file:
        previous_groups_raw = json.load(json_file)

    ## Transform the raw file into a dictionnary with keys people that plays the current session and value list of tuples (person, ordinal session play with this person) -- the same person can appear several times here
    ## Update the number of last played session for each to people to normalize the optimization function
    previous_groups = {people:[] for people in people_names}
    last_played_session = {people:0 for people in people_names}

    for session in previous_groups_raw:
        for person in session[1]:
            for other_person in session[1]:
                if person != other_person:
                    try:
                        last_played_session[unidecode.unidecode(person)] = max(session[0], last_played_session[unidecode.unidecode(person)])
                        previous_groups[unidecode.unidecode(person)].append([other_person, session[0]])
                    except:
                        pass





    # Generate liste of possible groups to give as input

    ## Create list of all possibilites
    group_only_combinations = [tuple(c) for c in pulp.allcombinations(people, target_number + 1)]

    ### Remove undesired combinations
    #### Only groups of target_number - 1 to target_number + 1 people are considered
    group_only_combinations = [x for x in group_only_combinations if len(x) >= target_number - 1]

    #### Remove combinations of 3 of 5 people in setting in which they are not suited
    if len(people_names)%target_number == 1:
        group_only_combinations = [x for x in group_only_combinations if len(x) >= target_number]
    if ((target_number != 2) and (len(people_names)%target_number == target_number - 1)):
        group_only_combinations = [x for x in group_only_combinations if len(x) <= target_number]


    combinations = [(date,combi) for (date, combi) in product(dates, group_only_combinations)]

    ### Remove impossible date/person matches (such that this constraint is already addressed)
    def possible(combi):
        possible = True
        for person in combi[1]:
            if int(constraints[person][combi[0]])==0:
                possible = False
        return(possible)

    combinations = [x for x in combinations if possible(x)]





    # Define the optimization function of the problem

    ## Binary variable to state that a setting is used
    x = pulp.LpVariable.dicts('Create groups based on availability constraints and people turnover', combinations, lowBound = 0, upBound = 1, cat = pulp.LpInteger)

    ## Fitness function
    ### Sum of ordinals of people that already play together in this session ; quantity to minimize (if they play recently, ordinal is higher)
    def fitness(combi):
        fitness = 0
        n = len(combi[1])
        for i in range(0, n):
            name = unidecode.unidecode(people_names[combi[1][i]])
            to_normalized_number_session = last_played_session[name]
            for j in range(0, n):
                another_name = unidecode.unidecode(people_names[combi[1][j]])
                for (person, session) in previous_groups[name]:
                    if person == another_name:
                        fitness += session / to_normalized_number_session
        return (fitness)

    ## Optimization problem
    problem = pulp.LpProblem("Casting", pulp.LpMinimize)

    ## Objective function
    ### Sum of exponential of fitness function for all groups, such that an optimum has to be achieved in each combi to get a global optimum
    problem += sum([exp(fitness(combi)) * x[combi] for combi in combinations])





    # Define the constraints of optimization problem

    ## Availability constraint is already assumed at the moment of selection of possibilities

    ## Every person plays once
    for person in people:
        problem += sum([x[combi] for combi in combinations if person in combi[1]]) == 1, "%s must play"%person

    ## Each date is used at most once
    for date in dates:
        problem += sum([x[combi] for combi in combinations if date == combi[0]]) <= 1, "%s can not be used twice"%date

    ## Group sizes are as close as possible to target_number - this translates into a number of dates to match
    if (len(people)/target_number)%1 != 0.5:
        problem += sum([x[combi] for combi in combinations]) == round(len(people)/target_number), "Group sizes close to targer number"
    else:
        problem += sum([x[combi] for combi in combinations]) <= int(len(people)/target_number) + 1, "Group sizes close to targer number / low bound"
        problem += sum([x[combi] for combi in combinations]) >= int(len(people)/target_number), "Group sizes close to targer number / high bound"





    # Solve the model and return the solution

    ## Solve the model
    problem.solve()

    ## Check that constraints are satisfied
    problem = False
    for combi in combinations:
        if x[combi].value() == 1.0:
            for person in combi[1]:
                if constraints[person][combi[0]] == "0":
                    problem = True

    if problem:
        return("Constraints not respected")

    ## Print the solution and return cost (scale 0-1)
    cost = 0
    print("\nGroups are:\n")
    separator = ", "
    for combi in combinations:
        if x[combi].value() == 1.0:
            cost += exp(fitness(combi))
            print(date_names[combi[0]] + ": " + separator.join([people_names[person] for person in combi[1]]) + "\n")

    print("Cost function is " + str(cost))





# Create main function
if __name__ == "__main__":
    target_number = sys.argv[1]
    dispo_file_path = sys.argv[2]
    previous_groups_file_path = sys.argv[3]
    main(target_number, dispo_file_path, previous_groups_file_path)
