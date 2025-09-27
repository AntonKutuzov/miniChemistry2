from miniChemistry.Computations.Problems.ProblemParser import parse_data
from miniChemistry.Core.Reactions import MolecularReaction, IonGroupReaction
from miniChemistry.Core.Substances import Molecule, Simple, Ion
from miniChemistry.Computations.SSDatum import SSDatum
from miniChemistry.Computations.ReactionCalculator import ReactionCalculator

from typing import List, Optional


def solve_LR(
            r: MolecularReaction|IonGroupReaction | str | List[Molecule|Simple|Ion],
            ssdata: str,
            target: str,
            round_result: bool = True,
            find_moles: Optional[List[Molecule|Simple|Ion]] = None
        ) -> List[SSDatum]:

    rc = ReactionCalculator(r)
    ssdata = parse_data(ssdata)
    target = parse_data(target)

    for ssd in ssdata:
        rc.substance(ssd.substance).write(ssd.datum)

    rc.compute_moles_of(*rc.reaction.reagents, exception_if='all')
    lr = rc.limiting_reagent(*rc.reaction.reagents)

    if find_moles is not None:
        product_moles = rc.derive_moles_of(*find_moles, use=lr.substance)
        return product_moles
    else:
        rc.derive_moles_of(*rc.reaction.products, use=lr.substance)
        rc.derive_moles_of(*rc.reaction.reagents, use=lr.substance, ignore_rewriting=True)
        result = rc.compute(*target, rounding=round_result)
        return result


# PATTERN: <variable from LinearIterator> [ <formula> ] = <value> <units>
reaction = 'Ba(NO3)2 + Na2SO4'
data = '''
C[ Ba(NO3)2 ] = 0.5M
Vsm[ Ba(NO3)2 ] = 200 mL
Vsm[ NaNO3 ] = 200 mL
Vsm[ BaSO4 ] = 200 mL
mps[ Na2SO4 ] = 40 g
'''
target = """
mps[ NaNO3 ] = 0.001 g
mps[ BaSO4 ] = 0.001 g
C[ NaNO3 ] = 0.001 mol/L
C[ BaSO4 ] = 0.001 M
"""

print(*solve_LR(reaction, ssdata=data, target=target), sep='\n')
