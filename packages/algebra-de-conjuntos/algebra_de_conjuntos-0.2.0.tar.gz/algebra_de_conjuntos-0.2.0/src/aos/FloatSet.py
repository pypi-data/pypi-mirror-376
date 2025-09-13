from abc import ABC, abstractmethod
from typing import Union


# FloatSet interface
class IFloatSet(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def is_empty(self):
        pass

    @abstractmethod
    def get_min(self):
        pass

    @abstractmethod
    def get_max(self):
        pass


class FloatSet(IFloatSet):
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def execute(self):
        return self

    def is_empty(self):
        return self.min > self.max

    def get_min(self):
        return self.min

    def get_max(self):
        return self.max

    def __str__(self):
        return "FloatSet(" + str(self.min) + ", " + str(self.max) + ")"

    def __repr__(self):
        return "FloatSet(" + str(self.min) + ", " + str(self.max) + ")"

    def __contains__(self, x: Union[int, float, "FloatSet"]):
        if type(x) is float or type(x) is int:
            return self.min <= x <= self.max
        elif type(x) is type(self):
            print(self.min, x.min, self.max, x.max)
            return self.min <= x.min and self.max >= x.max
        return False

    def __eq__(self, other):
        if type(other) is not type(self):
            return False
        return self.min == other.min and self.max == other.max

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.min, self.max))
