from __future__ import annotations

from miniChemistry.Core.Substances import Molecule, Simple, Ion, IonGroup
from miniChemistry.Core.Substances.Particle import Particle
from miniChemistry.Core.Tools.parser import parse
from QCalculator import Datum

from typing import Union
from pint import Unit


class SSDatum(Datum):
    """
    SSDatum stands for "Substance–Specific Datum". This class extends the Datum class by adding a substance as another
    data point. The constructor then takes in an additional parameter ("substance", which will always go the first one).
    """

    
    def __init__(self,
                 substance: Molecule |Simple | Ion | IonGroup | str,
                 variable: str,
                 value: float,
                 units: Union[str, Unit] = 'dimensionless') -> None:

        if isinstance(substance, Particle):
            self._substance = substance
        else:
            self._substance = parse(substance)

        super().__init__(variable, value, units)

    def __eq__(self, other: SSDatum):
        return self.datum == other.datum and self.substance == other.substance

    def __getitem__(self, item):
        item_list = [self.substance, *self.datum, str(self.datum.unit)]
        return item_list[item]

    def __iter__(self):
        iter_list = [self.substance, *self.datum]
        return iter_list.__iter__()

    def __str__(self):
        return_str = f'{self.symbol}({self.substance.formula()}) = {self.value} {self.unit}'
        return return_str

    def to(self, unit: str, in_place: bool = False) -> SSDatum | None:
        if in_place:
            super().to(unit, in_place=True)
            return None
        else:
            new_self = super().to(unit, in_place=False)
            return SSDatum(self.substance, new_self.symbol, new_self.value, new_self.unit)


    @property
    def datum(self) -> Datum:
        return Datum(self.symbol, self.value, self.unit)

    @property
    def substance(self) -> Molecule | Simple | Ion | IonGroup:
        return self._substance


if __name__ == '__main__':
    sub = Ion.from_string('Ag', 1)
    # sub = Molecule.water
    ssd = SSDatum(sub, 'mps', 18, 'g')
    print(ssd)
