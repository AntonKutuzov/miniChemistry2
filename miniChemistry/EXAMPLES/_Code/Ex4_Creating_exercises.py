"""This code creates a specified number of exercises. Two types of exercises are available: simple ones, without any
excess, and more complicated, where one substance is in excess."""

from miniChemistry.Computations.Problems.ProblemSolver import ProblemSolver
from miniChemistry.Core.Reactions import MolecularReaction
import random as rand

from miniChemistry.EXAMPLES import SETTINGS, comment

reactions = [
    'NaOH + H2SO4 = Na2SO4 + H2O',
    'CaCO3 = CaO + CO2',
    'Ba(NO3)2 + Al2(SO4)3 = Al(NO3)3 + BaSO4',
    'Zn + HNO3 = Zn(NO3)2 + N2O + H2O',
    'H2O + NO2 = HNO2 + HNO3'
]

# simple exercise
comment(10 * '=' + ' EXERCISES WITH NO EXCESS ' + 10 * '=', no_delay=True)
for _ in range(SETTINGS.NUMBER_OF_SIMPLE_EXERCISES):
    reaction = rand.choice(reactions)
    mr = MolecularReaction.from_string(reaction)
    given_s = rand.choice(mr.substances)

    target_s = rand.choice(mr.substances)
    while given_s == target_s:
        target_s = rand.choice(mr.substances)

    given_mass = rand.randint(0, 75) + rand.randint(1, 9)/10

    se_data_string = f'''
mps[{given_s.formula()}] = {given_mass} g
t: mps[{target_s.formula()}] = 0.01 g
r: {reaction}
'''

    ps = ProblemSolver(se_data_string)
    comment(se_data_string, end='', no_delay=True)
    comment('Solution: ' + ''.join([str(a) for a in ps.solve()]), no_delay=True)


# exercises with excess of one substance
comment('\n\n' + 10*'=' + ' EXERCISES WITH ONE SUBSTANCE IN EXCESS ' + 10*'=', no_delay=True)
for _ in range(SETTINGS.NUMBER_OF_EXCESS_EXERCISES):
    while True:
        reaction = rand.choice(reactions)
        mr = MolecularReaction.from_string(reaction)
        if len(mr.reagents) >= 2:
            break

    reagents = mr.reagents.copy()
    given_1 = rand.choice(reagents)
    reagents.remove(given_1)
    given_2 = rand.choice(reagents)
    reagents.remove(given_2)
    target_s = rand.choice(mr.products)

    given_mass_1 = rand.randint(0, 75) + rand.randint(1, 9) / 10
    given_mass_2 = rand.randint(0, 75) + rand.randint(1, 9) / 10

    ee_data_string = f'''
mps[{given_1.formula()}] = {given_mass_1} g
mps[{given_2.formula()}] = {given_mass_2} g
t: mps[{target_s.formula()}] = 0.01 g
r: {reaction}
'''

    ps = ProblemSolver(ee_data_string)
    comment(ee_data_string, end='', no_delay=True)
    comment('Solution: ' + ''.join([str(a) for a in ps.solve()]), no_delay=True)
