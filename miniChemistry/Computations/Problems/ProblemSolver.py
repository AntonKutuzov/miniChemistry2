from miniChemistry.Computations.Problems.ProblemParser import ProblemParser
from miniChemistry.Computations.ReactionCalculator import ReactionCalculator
from miniChemistry.Computations.SSDatum import SSDatum

from TinyDB.File import File
from QCalculator import LinearIterator
from QCalculator.database import add_formula, add_variable
from QCalculator.Exceptions.LinearIteratorExceptions import SolutionNotFound

from typing import List, Optional


class ProblemSolver(ProblemParser):
    def __init__(self,
                 data_string: str,
                 round_result: bool = True,
                 ignore_failures: bool = False
                 ):
        super().__init__(data_string)

        if self.reaction is not None:
            self._rc = self._init_rc()
        else:
            self._load_from_file()
            self._li = self._init_li()

        # SETTINGS
        self._rounding = round_result
        self._ignore_failures = ignore_failures

    def _init_rc(self) -> ReactionCalculator:
        self._rc = ReactionCalculator(self.reaction)
        self._rc.write(*self.data_list)
        return self._rc

    def _init_li(self) -> LinearIterator:
        return LinearIterator()

    def _load_from_file(self) -> None:
        file = File('formulas.txt', caller=__file__, rel_path='CalculatorFiles', parent_cycles=2)
        file.open('r')
        for line in file.read_all():
            add_formula(line)
        file.close()

        file = File('units_and_names.txt', caller=__file__, rel_path='CalculatorFiles', parent_cycles=2)
        file.open('r')
        for line in file.read_all():
            var, name, units, default = line.split(':')
            add_variable(var, units)
        file.close()

    def solve(self) -> List[SSDatum]:
        if self.reaction is None:
            return self.solve_QC()
        else:
            reagent_moles = self._rc.compute_moles_of(*self.reaction.reagents, exception_if='all')

            if len(reagent_moles) > 1:
                return self.solve_LR()
            elif 1 >= len(reagent_moles) > 0:
                return self.solve_S()
            else:
                raise Exception(f'Could not detect a solution strategy for the data string: {self._data_string}.')

    def solve_LR(self) -> List[SSDatum]:
        self._rc.compute_moles_of(*self.reaction.reagents, exception_if='all')
        lr = self._rc.limiting_reagent(*self.reaction.reagents)
        self._rc.derive_moles_of(*self.reaction.products, use=lr.substance)
        self._rc.derive_moles_of(*self.reaction.reagents, use=lr.substance, ignore_rewriting=True)
        result = self._rc.compute(*self.target_list, rounding=self._rounding)
        return result

    def solve_S(self) -> List[SSDatum]:
        reagent_moles = self._rc.compute_moles_of(*self.reaction.reagents, exception_if='all')
        moles = reagent_moles[0]
        self._rc.derive_moles_of(*self.reaction.products, use=moles.substance)
        self._rc.derive_moles_of(*self.reaction.reagents, use=moles.substance, ignore_rewriting=True)
        result = self._rc.compute(*self.target_list, rounding=self._rounding)
        return result

    def solve_QC(self,
                 data_list: Optional[List[SSDatum]] = None,
                 target_list: Optional[List[SSDatum]] = None
                 ) -> List[SSDatum]:

        data_list = data_list if data_list is not None else self.data_list
        target_list = target_list if target_list is not None else self.target_list

        data_subs = self.count_substances(data_list)
        target_subs = self.count_substances(target_list)

        if data_subs > 1 or target_subs > 1:
            result = list()
            data = self.same_substances(data_list)
            target = self.same_substances(target_list)

            for sub, ssd_list in data.items():
                t_list = target[sub]
                result.extend(self.solve_QC(ssd_list, t_list))

            if (not self.get_substances(result) == self.get_substances(self.target_list)
                    and
                not self._ignore_failures):
                failed_substances = self.get_substances(self.target_list).difference(self.get_substances(result))
                raise Exception(f'Could not compute all the targets. Failed at: '
                                f'{", ".join([s.formula() for s in failed_substances])}')
            return result

        else:
            answers = list()

            for target in target_list:
                self._li.clear()
                for datum in data_list:
                    self._li.write(datum)

                self._li.target = target

                try:
                    ans = self._li.solve(stop_at_target=True, alter_target=True, rounding=self._rounding)
                except SolutionNotFound as e:
                    print(f'Failed at: "{str(target)}".')
                    raise e

                ans = SSDatum(target.substance, ans.symbol, ans.value, ans.unit)
                answers.append(ans)

            self._li.clear()
            return answers

'''
if __name__ == '__main__':
    data_string = """
Vpg[H2] = 10 L
V0[] = 24.4 L/mole
t: V[] = 0.001 L
r: H2 + O2
    """

    ps = ProblemSolver(data_string)
    res = ps.solve()

    print(*res, sep='\n')
'''