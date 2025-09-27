import copy
from typing import Tuple, Dict
from miniChemistry.Core.Reactions import MolecularReaction
from miniChemistry.Core.Substances import Molecule, Simple


"""
NEW DATA PRESENTATION RULES
<variable> [ <substancES with ; as a separator> ] = <value> <units>
r: <reaction>
reaction: <reaction> # also works
t: <target> # can be given multiple times
target: <target> # also works
# comment are written in the same way as in Python (no triple strings)


** For example **
Vsm[] = 100 mL # meaning that ALL substances have volume of their solution of 100 mL. The substances taken from a reaction
Vsm[ NaNO3; BaSO4 ] = 100 mL # meaning that sodium nitrate and barium sulfate have mixture volume of 100 mL

------

So, a code that looks like this

Vsm[] = 100 mL
C[ Ba(NO3)2; Na2SO4 ] = 1M
r: Ba(NO3)2 + Na2SO4
t: C[] = 0.0001 M
target: mps[ BaSO4 ] = 0.01 g

Will be translated into an exercise that looks like this
Ba(NO3)2 + Na2SO4 -> 2NaNO3 + BaSO4
Given molar concentrations of Ba(NO3)2 and Na2SO4 of 1M, find all the other concentrations. (I.e. concentrations 
of the products, but in other cases that also can be concentrations of other reagents). Also find the mass of 
pure barium sulfate.
"""

from typing import List
from miniChemistry.Computations.SSDatum import SSDatum


class ProblemParser:
    def __init__(self, data_string: str):
        self._reaction = None
        self._targets = list()
        self._givens = list()

        self._parse_data(data_string)
        self._data_string = data_string


    def remove_spaces(self, string: str) -> str:
        while ' ' in string:
            string = string.replace(' ', '')
        return string

    def _parse_reaction_data(self, r: str) -> MolecularReaction:
        r = self.remove_spaces(r)
        rest, r = r.split(':')

        if r:
            reaction = MolecularReaction.from_string(r)
            return reaction
        else:
            raise Exception("You didn't specify the reaction, but indicated its presence by 'r:'.")

    def _parse_target_string(self, t: str) -> List[SSDatum]:
        t = self.remove_spaces(t)
        rest, t = t.split(':')

        if t:
            return self._parse_data_string(t)
        else:
            raise Exception("You didn't specify the target variable, but indicated its presence by 't:'.")

    def _parse_data_string(self, data: str) -> List[SSDatum]:
        variable: str
        formula: str
        value: float | int
        units: str

        ssd_list = list()

        data_no_spaces = self.remove_spaces(data)

        try:
            variable, rest = data_no_spaces.split('[')
            formulas, rest = rest.split(']')
            formulas = formulas.split(';')
            rest = rest.strip('=')
            value, units = self._get_units(rest)
        except (UnboundLocalError, ValueError):
            raise Exception(f'Failed to parse data string: "{data}".')

        formula_list = list()
        if formulas == ['']:
            if self.reaction is None:
                all_data = copy.deepcopy(self.data_list)
                all_data.extend(self.target_list)
                for substance in self.get_substances(all_data):
                    formula_list.append(substance.formula())
            else:
                for substance in self.reaction:
                    formula_list.append(substance.formula())
        else:
            formula_list = formulas

        for formula in formula_list:
            ssd_list.append( SSDatum(formula, variable, value, units) )
        return ssd_list

    @staticmethod
    def _get_units(string: str) -> Tuple[float, str]:
        value = ''
        units = ''

        for letter in string:
            if letter.isnumeric() or letter in ',.':
                value += letter
            else:
                units += letter

        return float(value), units

    def _parse_data(self,
                    data_string: str,
                    ) -> None:

        data_string = self.remove_spaces(data_string)
        data_string = data_string.strip().split('\n')
        data_string = sorted(data_string, key=lambda s: s.startswith('r:') or '[]' not in s, reverse=True)
        # because we need reaction to be first ,and the general data strings to be last to have all substances available
        # in both cases

        for line in data_string:
            if line.startswith('#'):
                continue

            elif line.startswith('r:'):
                self._reaction = self._parse_reaction_data(line)

            elif line.startswith('t:'):
                t = self._parse_target_string(line)
                self._targets.extend(t)

            elif line:
                g = self._parse_data_string(line)
                self._givens.extend(g)

    def same_substances(self,
                        data_list: List[SSDatum]
                        ) -> Dict[Molecule|Simple, List[SSDatum]]:
        selected = dict()
        substances = tuple({d.substance for d in data_list})

        for sub in substances:
            selected[sub] = list()

        for sub in substances:
            for datum in data_list:
                if datum.substance == sub:
                    selected[sub].append(datum)

        return selected

    def get_substances(self,
                       data_list: List[SSDatum]
                       ):
        substances = set()

        for datum in data_list:
            if datum.substance not in substances:
                substances.add(datum.substance)

        return substances

    def count_substances(self,
                         data_list: List[SSDatum]
                         ) -> int:
        return len(self.get_substances(data_list))

    @property
    def reaction(self) -> MolecularReaction:
        return self._reaction

    @property
    def target_list(self) -> List[SSDatum]:
        return self._targets

    @property
    def data_list(self) -> List[SSDatum]:
        return self._givens


if __name__ == '__main__':
    ### EXAMPLE ###
    data = """
    C[ Ba(NO3)2 ; Na2SO4 ] = 0.25 M
    Vsm[] = 150 mL
    r: Ba(NO3)2 + Na2SO4
    t: C[ BaSO4 ; NaNO3 ] = 0.001 M
    """

    pp = ProblemParser(data)

    print(pp.reaction.equation)
    print(*pp.target_list, sep=' | ')
    print(*pp.data_list, sep=' | ')
