from typing import List


def flatten(sets: List):
    flat_sets = []
    for subset in sets:
        if type(subset) is list:
            flat_sets.extend(subset)
        else:
            flat_sets.append(subset)
    return flat_sets


def __flatten_recursive(sets: List):
    flat_list = flatten(sets)
    if flat_list == sets:
        return sets
    return __flatten_recursive(flat_list)
