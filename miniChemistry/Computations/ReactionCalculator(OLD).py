from QCalculator.Exceptions.DatumExceptions import IncompatibleUnits

from miniChemistry.Computations.ComputationExceptions.IterativeCalculatorException import (
    SolutionNotFound,
    IncorrectFileFormatting)
from miniChemistry.Computations.ComputationExceptions.QuantityCalculatorException import ValueNotFoundException
from QCalculator import Datum, LinearIterator, Assumption
from QCalculator.Exceptions.LinearIteratorExceptions import SolutionNotFound, CannotRewriteVariable
from miniChemistry.Computations.SSDatum import SSDatum
from miniChemistry.Core.CoreExceptions.ReactionExceptions import WrongReactionConstructorParameters
from miniChemistry.Computations.ComputationExceptions.ReactionCalculatorException import *
from miniChemistry.Core.Reactions.MolecularReaction import MolecularReaction
from typing import List, Tuple, Dict, Any, Generator
from miniChemistry.Core.Substances import Molecule, Simple, Ion
from miniChemistry.Core.Substances.Particle import Particle
from miniChemistry.Core.Tools.parser import parse, split_ion_string
from miniChemistry.Utilities.File import File


class ReactionCalculator:
    """
    The ReactionCalculator class has the following methods:\n
    CONSTRUCTORS\n
    - __init__ from Reaction
    - __init__ from reagents (without products)
    - __init__ from reagents AND products passed as lists
    - __init__ from string

    for each constructor there's a separate classmethod:\n
    - _init_from_reaction(r: Reaction) -> ReactionCalculator
    - _init_from_reagents(rs: List[Particle]) -> ReactionCalculator
    - _init_from_substances(rs: List[Particle], ps: List[Particles]) -> ReactionCalculator
    - _init_from_string(string: str) -> ReactionCalculator

    PRIVATE METHODS\n
    - _create_calculators() -> dict
    - _write_molar_masses() -> None
    - _substance_to_particle(sub: str|Particle) -> Molecule|Simple

    PUBLIC METHODS\n
    1) Variable management\n
    - substance(sub: str|Particle) -> LinearIterator\n
    - assume(*assumptions: str) -> None\n
    - write(*data: SSDatum) -> None\n
    - erase(substance: str|Particle, variable: str) -> None\n
    - assume_excess(*substances: str|Particle) -> None\n

    2) Calculations over the chemical reaction\n
    2.1) Number of moles\n
    - compute_moles_of(*substances: str|Particle, exception_if: str = 'any', except_substances: List[Particle|str] = None) -> List[SSDatum]\n
    - derive_moles_of(use: str|Particle, *find: str|Particle) -> List[SSDatum]\n
    - limiting_reagent(*substances: str|Particle = None) -> List[SSDatum]\n
    - excess(*substances: str|Particle = None) -> List[SSDatum]\n

    2.2) Coefficients\n
    - ratio(*substances: str|Particle, wrt: str|Particle) -> Dict[Particle, float]\n
    - normalized_moles(*substances: str|Particle = None) -> Dict[Particle, float]\n

    2.3) Calculation\n
    - compute(*vars: SSDatum) -> List[SSDatum]\n

    PROPERTIES\n
    - ppt. substances -> Tuple[Particle]\n
    - ppt. reaction -> Reaction\n
    - ppt. coefficients -> Dict[Particle, float]\n

    SETTINGS VARIABLES\n
    cls.WRITE_NEW_VALUES: bool (True if computed values should not be erased afterwards)
    cls.
    """

    EXCESS_COEFFICIENT = 100

    # ===================================================================================================== CONSTRUCTORS
    def __init__(self, *args, **kwargs):
        self._reaction = None

        if len(args) == 1 and isinstance(args[0], MolecularReaction):
            self._init_from_reaction(args[0])
        elif len(args) == 1 and isinstance(args[0], str):
            self._init_from_string(args[0])
        elif len(args) > 1 and all([isinstance(arg, (Molecule, Simple)) for arg in args]):
            self._init_from_reagents(args)
        elif len(kwargs) == 2 and 'reagents' in kwargs and 'products' in kwargs:
            self._init_from_substances(rs=kwargs['reagents'], ps=kwargs['products'])
        else:
            raise InvalidConstructorArguments(variables=locals())

        self._substance_data = self._create_calculators()
        self._write_molar_masses()

    def _init_from_reaction(self, r: MolecularReaction) -> None:
        self._reaction = r

    def _init_from_reagents(self, rs: Tuple[Molecule|Simple, ...]) -> None:
        try:
            self._reaction = MolecularReaction(reagents=list(rs))
        except WrongReactionConstructorParameters:
            raise InitializationError(init_type='reagents', variables=locals())

    def _init_from_substances(self, rs: List[Molecule|Simple], ps: List[Molecule|Simple]) -> None:
        try:
            self._reaction = MolecularReaction(reagents=list(rs), products=list(ps))
        except WrongReactionConstructorParameters:
            raise InitializationError(init_type='reagents and products', variables=locals())

    def _init_from_string(self, string: str) -> None:
        try:
            self._reaction = MolecularReaction.from_string(string)
        except WrongReactionConstructorParameters:
            raise InitializationError(init_type='reaction scheme as a string', variables=locals())

    # ================================================================================================== PRIVATE METHODS
    def _create_calculators(self) -> Dict[Molecule|Simple, LinearIterator]:
        data = dict()

        for sub in self.substances:
            ic = LinearIterator()
            data.update({sub : ic})
            # self.__setattr__(sub.formula(), ic)

        return data

    def _write_molar_masses(self) -> None:
        for sub in self.substances:
            M = sub.molar_mass
            self.substance(sub).write(Datum('M', M, 'g/mole'))

    @staticmethod
    def _substance_to_particle(substance: str|Molecule|Simple) -> Molecule|Simple:
        if isinstance(substance, Particle):
            return substance
        elif isinstance(substance, str):
            sub = parse(substance)

            if isinstance(sub, (Molecule, Simple, Ion)):
                return sub
        else:
            pass

        raise TypeError(f'Wrong substance data type: expected "str", "Molecule", "Ion" or "Simple", got "{type(substance)}"')

    @staticmethod
    def _read_assumptions() -> Generator[Assumption, None, Assumption]:
        file = File(__file__)
        file.bind('CalculatorFiles/Assumptions')

        assumption = None

        for line in file.read_all():
            if line.startswith('#'):
                continue
            elif line == '!':
                if assumption is not None:
                    yield assumption
                else:
                    raise IncorrectFileFormatting(file_name=file.name, variables=locals())
                assumption = None
            elif line.startswith('!'):
                symbol, name = line.split(':')
                symbol = symbol.strip('!').strip(' ')
                name = name.strip(' ')
                assumption = Assumption(symbol, name)
            elif line.startswith('variable'):
                a, b = line.split(' ')
                symbol, value, unit = b.split(':')
                d = Datum(symbol, float(value), unit)
                assumption.to_set(d)
            elif line.startswith('compute'):
                a, b = line.split(' ')
                var, units = b.split('::')
                assumption.to_compute(Datum(var, 0, units))
            elif line.startswith('assume'):
                a, b = line.split(' ')
                var, value, units = b.split(':')
                assumption.to_assume(Datum(var, float(value), units))
            elif line.isalnum():
                raise IncorrectFileFormatting(file_name=file.name, variables=locals())

        if assumption is not None:
            return assumption


    @staticmethod
    def exception_handler(func,
                          iter: List[Molecule|Simple],
                          exception, # Any MiniChemistryException
                          exception_if: str = 'any',
                          except_substances: List[Simple|Molecule] = None,
                          instant_return: bool = False
                          ) -> Any:

        return_list = list()

        exception_count = 0
        exception_types = {
            'any': lambda x: True,
            'some': lambda sub: True if except_substances and sub in except_substances else False,
            'all': lambda x: True if exception_count == len(iter) else False,
            'disabled': lambda x: False
        }

        for substance in iter:

            try:
                result = func(it=substance)

                if not instant_return:
                    return_list.append(result)
                else:
                    return result

            except ComputationException as e:
                exception_count += 1
                if exception_types[exception_if](substance):
                    print(f'The substance is {substance.formula()}')
                    raise e

        return return_list

    # =================================================================================================== PUBLIC METHODS
    #                                                                                                variable management
    def substance(self, substance: str|Molecule|Simple) -> LinearIterator:
        sub = self._substance_to_particle(substance)
        try:
            return self._substance_data[sub]
        except KeyError:
            raise SubstanceNotFound(substance.formula(), variables=locals())

    def assume(self, *assumptions: str) -> None:
        read_assumptions = [a for a in self._read_assumptions()]

        for a in read_assumptions:
            if a.symbol in assumptions:
                for li in self.calculators:
                    a.apply_to(li)

    def write(self, *data: SSDatum, ignore_rewriting: bool = False) -> None:
        for datum in data:
            sub = datum.substance
            d = datum.datum

            try:
                self.substance(sub).write(d)
            except CannotRewriteVariable:
                if ignore_rewriting:
                    return
                else:
                    print(f'Cannot rewrite the variable "{d.symbol}" for substance {sub.formula()}')
                    print('The current value is', self.substance(sub).read(d.symbol, round_to=4))
                    print(f'Tried to rewrite to {d.value} {d.unit}')
                    exit(1)

    def erase(self, substance: str|Molecule|Simple, variable: str) -> None:
        sub = self._substance_to_particle(substance)
        self.substance(sub).erase(variable)

    def assume_excess(self, *substances: str|Molecule|Simple) -> None:
        moles = self.moles(exception_if='all')
        mm = max(moles, key=lambda ssd: ssd.magnitude)
        excess = ReactionCalculator.EXCESS_COEFFICIENT * mm.value

        for substance in substances:
            sub = self._substance_to_particle(substance)
            self.write(SSDatum(sub, 'n', excess, 'moles'))

    def moles(self,
              *substances: str|Molecule|Simple,
              round_to: int = 15,
              exception_if: str = 'any',
              except_substances: List[Molecule|Simple|str] = None
              ) -> List[SSDatum]:

        iterable = [self._substance_to_particle(s) for s in substances] if substances else self.substances

        def func(it: Molecule|Simple):
            sub = self._substance_to_particle(it)
            mole = self.substance(sub).read('n', 'mole', rounding=False)
            return SSDatum(sub, mole.symbol, round(mole.value, round_to), mole.unit)

        return ReactionCalculator.exception_handler(
            func,
            iter=iterable,
            exception=ValueNotFoundException,
            exception_if=exception_if,
            except_substances=except_substances
        )

    #                                                                                                    number of moles
    def compute_moles_of(self,
                         *substances: str|Molecule|Simple,
                         round_to: int = 15,
                         exception_if: str = 'any',
                         except_substances: List[Molecule|Simple|str] = None
                         ) -> List[SSDatum]:

        def func(it: Molecule|Simple):
            # one SSD – one element in the output list
            return self.compute(SSDatum(it, 'n', round(1/9, round_to), 'mole'))[0]

        return ReactionCalculator.exception_handler(
            func,
            iter=[self._substance_to_particle(s) for s in substances],
            exception=ComputationException,
            exception_if=exception_if,
            except_substances=except_substances
        )

    def derive_moles_of(self,
                        *find: Molecule|Simple|str,
                        use: Molecule | Simple | str,
                        round_to: int = 15,
                        ignore_rewriting: bool = False
                        ) -> List[SSDatum]:
        """
        Find normalized moles of "use" and "find"s
        Find coefficients of "find"s
        Multiply normalized moles to the respective coefficient

        :param find:
        :param use:
        :param round_to:
        :return:
        """

        nn_use = self.normalized_moles(use)[0]
        coef_find = self.coefs(*find)

        moles = list()

        for f, c in zip(find, coef_find):
            new_magn = nn_use.value*c
            new_ssd = SSDatum(f, 'n', round(new_magn, round_to), nn_use.unit)
            self.write(new_ssd, ignore_rewriting=ignore_rewriting)
            # new_ssd.rewrite(round(new_ssd.value, round_to), new_ssd.unit)
            moles.append(new_ssd)

        return moles

    def limiting_reagent(self,
                         *substances: Molecule|Simple|str,
                         round_to: int = 15
                         ) -> SSDatum:
        if not substances:
            substances = self.reaction.reagents

        moles = self.normalized_moles(*substances, round_to=round_to)
        lr = min(moles, key=lambda mole: mole.value)
        return lr

    def excess(self,
               *substances: Molecule|Simple|str,
               round_to: int = 15
               ) -> List[SSDatum]:
        exs = list()
        lr = self.limiting_reagent(*substances)
        nn = self.normalized_moles(*substances)
        cs = self.coefs(*substances)

        for i, substance in enumerate(substances):
            sub = self._substance_to_particle(substance)
            nn[i].to_base_units()
            lr.to_base_units()
            magn = round(cs[i]*(nn[i].value - lr.value), round_to)
            ssd = SSDatum(sub, 'n', magn, 'mole')
            exs.append(ssd)

        exs = [ssd for ssd in exs if ssd.value != 0]

        return exs

    #                                                                                                       coefficients
    def ratio(self, *substances: str|Molecule|Simple, wrt: str|Molecule|Simple) -> Dict[Molecule|Simple, float]:
        wrt_sub = self._substance_to_particle(wrt)
        wrt_coef = self.coefficients[wrt_sub]
        coef_ratios = dict()

        if not substances:
            substances = self.reaction.substances

        for substance in substances:
            sub = self._substance_to_particle(substance)
            coef = self.coefficients[sub]
            coef_ratios.update({sub : float(coef/wrt_coef)})

        return coef_ratios

    def normalized_moles(self,
                         *substances: str|Molecule|Simple,
                         round_to: int = 15
                         ) -> List[SSDatum]:

        if not substances:
            substances = self.reaction.substances

        moles = self.moles(*substances, round_to=round_to)
        coefs = [self.coefficients[self._substance_to_particle(s)] for s in substances]
        normalized_list = list()

        for sub, mole, coef in zip(substances, moles, coefs):
            normalized_list.append(SSDatum(sub, mole.symbol, round(mole.value/coef, round_to), mole.unit))

        return normalized_list

    def coefs(self, *substances: Molecule|Simple|str) -> List[float]:
        cs = list()

        for substance in substances:
            sub = self._substance_to_particle(substance)
            c = self.coefficients[sub]
            cs.append(c)

        return cs

    #                                                                                                       calculations
    def compute(self,
                    *variables: SSDatum,
                    rounding: bool = False
                ) -> List[SSDatum]:
        ret_list = list()

        for var in variables:
            sub = var.substance
            self.substance(sub).target = var.datum
            try:
                self.substance(sub).solve(stop_at_target=True, alter_target=True)
                result = self.substance(sub).target.to(var.unit)

                if rounding:
                    magnitude = round(result.value, var.num_decimals)
                else:
                    magnitude = result.value

                ret_list.append(SSDatum(sub, result.symbol, magnitude, result.unit))

            except SolutionNotFound:
                raise ComputationException(self.substance(sub).target.symbol, substance=sub.formula(), variables=locals())
            except IncompatibleUnits as e:
                print(f'Failed at: "{var}".')
                raise e

        return ret_list

    # ======================================================================================================= PROPERTIES
    @property
    def reaction(self) -> MolecularReaction:
        return self._reaction

    @property
    def substances(self) -> List[Molecule|Simple]:
        return self.reaction.substances

    @property
    def calculators(self) -> List[LinearIterator]:
        return list(self._substance_data.values())

    @property
    def coefficients(self) -> Dict[Molecule|Simple, float|int]:
        return self.reaction.coefficients

"""
NaOH = Molecule.from_string('Na', 1, 'OH', -1)
H2SO4 = Molecule.from_string('H', 1, 'SO4', -2)
H2O = Molecule.water
Na2SO4 = Molecule.from_string('Na', 1, 'SO4', -2)

rc = ReactionCalculator('NaOH + H2SO4')
print(rc.reaction.equation)

rc.write(SSDatum(H2SO4, 'mps', 9.8, 'g'))
rc.write(SSDatum(H2O, 'mps', 185, 'g'))

print(*rc.compute_moles_of(H2SO4, H2O, round_to=2))
rc.assume_excess(NaOH)
lr = rc.limiting_reagent(H2SO4, H2O)
print(lr)
print(*rc.moles(H2SO4, H2O))
print(*rc.derive_moles_of(Na2SO4, use=lr.substance, round_to=2))
print(*rc.excess(*rc.reaction.reagents, round_to=2))
"""