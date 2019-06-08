# Group-Opti
**Optimization script to cast people in several groups on their availabilities and constraint of turn-over from previous groups**

## Requirements

This script needs the following packages to work:

[PuLP](https://pythonhosted.org/PuLP/index.html) : Optimization library used in the script

`pip install pulp`

[Unidecode](https://pypi.org/project/Unidecode/) : Unicode library to avoid errors due to typo

`pip install Unidecode`

## Optimization problem specs

Objective of this optimization script:

- Cast people in groups on different dates

Conditions and constraints for the optimization problem:

- People availability
- Everyone must be casted (once and only once)
- Groups have to be set on different dates
- Groups must match a target number of people per group

Optimization criteria:

- People must be casted in groups as different as possible from previous groups in which they were\*

Limitations:

- People have to provide their availabilities (Yes/No) for each date ("Maybe" is not taken into account)
- There is a tolerance of plus/minus one person per group if the number of people does not perfectly match with the target number of people per group
  - The optimization script tries to create the computed ideal number of groups to reduce tolerance at its minimal possible value. If no solution can be found, the constraints `"Group sizes"` have to be lightened or removed.
- People names in data files have to be carefuly written since errors will prevent from computing optimization function for people whose name has been mistyped thus set to default.

## Use

Three inputs are needed:

- `target_number` (int): Target number of people per group

- `path_to_dates.csv` (str): Path to .csv file containing people binary availabilies with rows being people and columns being dates (separators must be ",")

- `path_to_previous_groups.json` (str) : Path to .json file containing list of previous groups. Format of each previous group in this list must be [n, list] with n being the ordinal number of the session for which this group has been used and list being the list of names.

To run the script, just:

`python opti-script.py target_number path_to_dates path_to_previous_groups`

## Example

An example is provided in the `Example/` folder, with input files. To run the example problem, just: `python opti-script.py 2 Example/dates.csv Example/previous_groups.json`

## Misceallenous
\* Optimization function to minimize is defined as the sum for all groups of the exponential of the sum for each pair perso in a group of the ordinals of the sessions in which they alreay have been in the same group with other members of its group normalized by the ordinal of its last played session. Consequences are the following:
- Normalization makes that people that have not been included in the most recent groups still matters in terms of "different people matches"
- Repartition of people that have already been in the same groups is homogenous among all groups and not concentrated on a few groups (costs are shared)
