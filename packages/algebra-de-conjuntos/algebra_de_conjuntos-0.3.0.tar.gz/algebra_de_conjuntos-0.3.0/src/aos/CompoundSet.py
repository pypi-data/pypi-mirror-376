from typing import List

from .constants import EMPTY_SET
from .FloatSet import FloatSet, IFloatSet
from .operations import flatten


class CompoundSet(IFloatSet):
    def __init__(self, sets: List[IFloatSet]):
        self.sets = sets

    def __eq__(self, other):
        return self.sets == other

    def execute(self):
        """Execute the compound set operation."""
        executed_sets = [set.execute() for set in self.sets]
        return flatten(executed_sets)

    def is_empty(self):
        return all(set.is_empty() for set in self.sets)

    def get_min(self):
        executed_set = self.execute()
        if hasattr(executed_set, "sets"):
            return min(set.get_min() for set in executed_set.sets)
        return executed_set.get_min()

    def get_max(self):
        executed_set = self.execute()
        if hasattr(executed_set, "sets"):
            return max(set.get_max() for set in executed_set.sets)
        return executed_set.get_max()

    def binary_intersection(self, A: FloatSet, B: FloatSet):
        new_min = max(A.get_min(), B.get_min())
        new_max = min(A.get_max(), B.get_max())
        if new_min > new_max:
            return EMPTY_SET
        return FloatSet(new_min, new_max)

    def flatten(sets: List):
        flat_sets = []
        for subset in sets:
            if type(subset) is list:
                flat_sets.extend(subset)
            else:
                flat_sets.append(subset)
        return flat_sets

    def flatten_recursive(self, sets: List):
        flat_list = flatten(sets)
        if flat_list == sets:
            return sets
        return self.flatten_recursive(flat_list)


class Union(CompoundSet):
    def __init__(self, sets):
        super().__init__(sets)

    def is_empty(self):
        executed_set = self.execute()
        if hasattr(executed_set, "sets"):
            return all(set.is_empty() for set in executed_set.sets)
        return executed_set.is_empty()

    def execute(self):
        """Execute the union operation."""
        executed_sets = super().execute()
        # Aplanar posibles Unions anidados
        flat_sets = []
        for s in executed_sets:
            if isinstance(s, Union):
                flat_sets.extend(s.sets)
            else:
                flat_sets.append(s)
        # Ordenar por mínimo
        flat_sets.sort(key=lambda x: x.get_min())
        # Fusionar intervalos solapados
        merged = []
        for s in flat_sets:
            if not merged:
                merged.append(s)
            else:
                last = merged[-1]
                # Si se solapan o son adyacentes, fusionar
                if last.get_max() >= s.get_min() - 1e-9:
                    merged[-1] = FloatSet(
                        min(last.get_min(), s.get_min()),
                        max(last.get_max(), s.get_max()),
                    )
                else:
                    merged.append(s)
        if len(merged) == 1:
            return merged[0]
        return Union(merged)

    def __repr__(self):
        return "Union(" + repr(self.sets) + ")"


class Intersection(CompoundSet):
    def __init__(self, sets):
        super().__init__(sets)

    def is_empty(self):
        return self.execute().is_empty()

    def execute(self):
        executed_sets = super().execute()
        return self.__intersection(executed_sets)

    def __intersection(self, sets: List[IFloatSet]) -> IFloatSet:
        # Si hay una Union en los sets, intersectar cada subconjunto
        result = sets[0]
        for s in sets[1:]:
            if isinstance(result, Union):
                new_sets = []
                for subset in result.sets:
                    inter = self.binary_intersection(subset, s)
                    if not inter.is_empty():
                        new_sets.append(inter)
                if not new_sets:
                    return EMPTY_SET
                result = Union(new_sets) if len(new_sets) > 1 else new_sets[0]
            elif isinstance(s, Union):
                new_sets = []
                for subset in s.sets:
                    inter = self.binary_intersection(result, subset)
                    if not inter.is_empty():
                        new_sets.append(inter)
                if not new_sets:
                    return EMPTY_SET
                result = Union(new_sets) if len(new_sets) > 1 else new_sets[0]
            else:
                result = self.binary_intersection(result, s)
                if result.is_empty():
                    return EMPTY_SET
        return result

    def __repr__(self):
        return "Intersection(" + repr(self.sets) + ")"
