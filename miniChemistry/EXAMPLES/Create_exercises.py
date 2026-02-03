from miniChemistry.Core.Reactions import MolecularReaction
from miniChemistry.Computations.Problems.ProblemSolver import ProblemSolver
from miniChemistry.Computations.SSDatum import SSDatum as D
from miniChemistry.Computations.ReactionCalculator import ReactionCalculator
from random import choice, randint
from typing import Tuple, List, Literal


reactions = [
    'Mg + O2 = MgO',
    'C + O2 = CO2',
    'H2SO3 = SO2 + H2O',
    'Zn + CuSO4 = Cu + ZnSO4',
    'AgNO3 + KCl = KNO3 + AgCl',
    'Na2SO4 + Ba(NO3)2 = NaNO3 + BaSO4',
    'NaOH + HCl = NaCl + H2O',
    'Zn + HNO3 = Zn(NO3)2 + N2O + H2O',
    'KMnO4 + KI + H2SO4 = MnSO4 + K2SO4 + I2 + H2O',
    'K2Cr2O7 + K2SO3 + H2SO4 = Cr2(SO4)3 + K2SO4 + H2O'
]

def select_data(
        reactions: List[str],
        nof_givens: int = 1,
        nof_targets: int = 1,
        allow_targeting_reagents: bool = True,
        allow_give_products: bool = True,
        silent_index_error: bool = True
) -> Tuple[str, List[str], List[str]]:

    def select_substance(l: List, n: int = 1) -> List[str]:
        selected = list()
        for _ in range(n):
            selection = choice(l)
            l.remove(selection)
            selected.append(selection.formula())
        return selected

    reaction = choice(reactions)
    mr = MolecularReaction.from_string(reaction)
    reagents = mr.reagents.copy()
    products = mr.products.copy()

    try:
        if allow_give_products:
            i = randint(0, 1)
            givens = select_substance(reagents if i else products, nof_givens)
        else:
            givens = select_substance(reagents, nof_givens)

        if allow_targeting_reagents:
            i = randint(0, 1)
            targets = select_substance(reagents if i else products, nof_targets)
        else:
            targets = select_substance(products, nof_targets)
    except IndexError as e:
        if silent_index_error:
            return select_data(reactions, nof_givens, nof_targets, allow_targeting_reagents, allow_give_products)
        else:
            raise e

    return reaction, givens, targets

def randfloat(a: int, b: int) -> float:
    return randint(a, b) + randint(0, 9)/10


def reference_comparison(PD_range: Tuple[int, int]) -> None:
    """
    Creates an exercise without excess where a student needs to compare the result with some sort of reference (e.g.
    desired mass of target substance). Optionally, also the percentage difference may be required.

    The deviation can be indicated for the exercise in terms of percentage difference. For this use PD_range. It is a tuple
    of integers where you can indicate PD in percents (!). For example, PD_range=(-10, 10) indicates that the result
    can deviate from desired output by 10% in either direction.

    :param PD_range: Tuple[int, int], negative PD means lack of obtained substance, positive means excess. Lower number
    goes first.
    :return: None
    """

    reaction, givens, targets = select_data(reactions)

    # problems for comparison with a reference
    data_string = f'''
    r: {reaction}
    mps[{targets[0]}] = {randfloat(0, 50)} g
    t: mps[{targets[0]}] = 0.01 g
    '''

    ps = ProblemSolver(data_string, round_result=False)
    mps = ps.solve()[0]

    COUNTER = 0
    reference_value = mps.value / (1 - randint(*PD_range)/100)
    while reference_value < 0.1 and COUNTER < 100:
        reference_value = mps.value / (1 - randint(*PD_range)/100)
        COUNTER += 1

    reference = D(targets[0], 'mps', reference_value, 'g')
    PD = (reference_value - mps.value) / reference_value

    print('Reaction:', reaction)
    print('Reference target:', reference)
    print('Obtained target:', mps)
    print('Difference:', reference - mps)
    print(f'(PD = {PD*100}%)')

def several_targets(nof_targets: int = 2) -> None:
    """
    Creates an exercise without excess with several target substances.

    :param nof_targets: int, number of target substances
    :return: None
    """

    reaction, givens, targets = select_data(reactions[2:], nof_targets=nof_targets, allow_give_products=False)

    dss = list()
    given_value = randfloat(0, 50)
    for target in targets:
        data_string = f"""
        r: {reaction}
        mps[{givens[0]}] = {given_value} g
        t: mps[{target}] = 0.01 g
        """
        dss.append(data_string)

    print(f'Reaction: {reaction}')
    print(f'Given: mps[{givens[0]}] = {given_value} g')
    print('Answers:')

    for ds in dss:
        ps = ProblemSolver(ds)
        print(*ps.solve())

def excess_for_3() -> None:
    """
    Creates an exercise with excess calculations, with 3 given substances.

    :return: None
    """

    reaction, givens, targets = select_data(reactions[8:], nof_targets=1, nof_givens=3, allow_targeting_reagents=False,
                                            allow_give_products=False)

    data_string = f"""
r: {reaction}
mps[{givens[0]}] = {randfloat(0, 50)} g
mps[{givens[1]}] = {randfloat(0, 50)} g
mps[{givens[2]}] = {randfloat(0, 50)} g
t: mps[{targets[0]}] = 0.01 g"""

    ps = ProblemSolver(data_string)
    print(data_string)
    print(*ps.solve())

def excess_mass() -> None:
    """
    Creates an exercise with excess calculations, where the aim is to find the mass of the substance in excess that is
    left after the reaction.

    :return: None
    """

    reaction, givens, targets = select_data(reactions[0:3]+reactions[4:], nof_givens=2,
                                            allow_targeting_reagents=False, allow_give_products=False)

    rc = ReactionCalculator(reaction)
    print('Reaction:', rc.reaction.equation)

    for given in givens:
        v = randfloat(0, 50)
        rc.write(D(given, 'mps', v, 'g'))
        print(f'mps[{given}] = {v} g')
    print(f'aim: mass of excess substance')

    rc.all_moles()
    excess = rc.excess(*givens)

    for exD in excess:
        MM = exD.substance.molar_mass
        mps = exD * D(exD.substance, 'M', MM, 'g/mole')
        print(f'Excess of {exD.substance.formula()}: {mps}')

def lack_mass() -> None:
    """
    Creates an exercise with excess calculations. The aim is to find a mass of lacking substance so that after the
    reaction there are no reagents left. I.e. the mass of lacking substance that corresponds for the mass left of
    the excess substance.

    :return: None
    """

    reaction, givens, targets = select_data(reactions[0:3] + reactions[4:], nof_givens=2,
                                            allow_targeting_reagents=False, allow_give_products=False)

    rc = ReactionCalculator(reaction)
    print('Reaction:', rc.reaction.equation)

    for given in givens:
        v = randfloat(0, 50)
        rc.write(D(given, 'mps', v, 'g'))
        print(f'mps[{given}] = {v} g')
    print(f'aim: mass of lack substance needed to run the reaction completely')

    rc.compute_moles_of(*givens)
    excess = rc.excess(*givens)

    if len(excess) > 1:
        raise Exception()
    else:
        rc2 = ReactionCalculator(reaction)
        exD = excess[0]
        rc2.write(exD)
        givens.remove(exD.substance.formula())
        lack = givens[0]  # we have only two given substances
        rc2.derive_moles_of(lack, use=exD.substance)
        lack_mps = rc2.compute(D(lack, 'mps', 0.001, 'g'))
        print(*lack_mps)


if __name__ == '__main__':
    ALLOWED_EXERCISE_TYPES = Literal['reference', 'several targets', 'excess of 3', 'excess mass', 'lack mass']


    # SETTINGS
    EXERCISE_TYPE: ALLOWED_EXERCISE_TYPES = 'reference'
    NOF_EXERCISES = 10
    PD_RANGE = (-10, 10)
    PERCENT_OF_3_TARGET_EXERCISES = 10

    # CODE
    for _ in range(10):
        print(40 * '=')

        match EXERCISE_TYPE:
            case 'reference':
                reference_comparison(PD_range=PD_RANGE)
            case 'several targets':
                i = randint(0, 100)
                if i > 100 - PERCENT_OF_3_TARGET_EXERCISES:
                    several_targets(nof_targets=3)
                else:
                    several_targets(nof_targets=2)
            case 'excess of 3':
                excess_for_3()
            case 'excess mass':
                excess_mass()
            case 'lack mass':
                lack_mass()
            case _:
                print(f'Exercise with name "{EXERCISE_TYPE}" does not exist.')
                break
