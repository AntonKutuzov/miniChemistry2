from miniChemistry.Computations.Problems.ProblemParser import parse_data
from miniChemistry.Core.Reactions import MolecularReaction, IonGroupReaction
from miniChemistry.Core.Substances import Molecule, Simple, Ion
from miniChemistry.Computations.SSDatum import SSDatum
from miniChemistry.Computations.ReactionCalculator import ReactionCalculator

from typing import List, Optional


def solve_S(
            r: MolecularReaction|IonGroupReaction | str | List[Molecule|Simple|Ion],
            ssdata: str,
            target: str,
            round_result: bool = True,
            print_equation: bool = False
        ) -> List[SSDatum]:

    rc = ReactionCalculator(r)
    ssdata = parse_data(ssdata)
    target = parse_data(target)

    rc.write(*ssdata)

    reagent_moles = rc.compute_moles_of(*rc.reaction.reagents, exception_if='all')

    if len(reagent_moles) > 1:
        raise Exception('More than one quantity of moles detected for reagents. Please use solve_LR.')

    moles = reagent_moles[0]

    rc.derive_moles_of(*rc.reaction.products, use=moles.substance)
    rc.derive_moles_of(*rc.reaction.reagents, use=moles.substance, ignore_rewriting=True)

    result = rc.compute(*target, rounding=round_result)

    if print_equation:
        print('Equation:', rc.reaction.equation)

    return result



# PATTERN: <variable from LinearIterator> [ <formula> ] = <value> <units>
reaction = 'Ba(NO3)2 + Na2SO4'
data = '''
    C[ Ba(NO3)2 ] = 0.25 M
    Vsm[ Ba(NO3)2 ] = 150 mL
    Vsm[ Na2SO4 ] = 150 mL
'''
target = 'C[ Na2SO4 ] = 0.001 M'

print(*solve_S(reaction, ssdata=data, target=target, print_equation=True))
