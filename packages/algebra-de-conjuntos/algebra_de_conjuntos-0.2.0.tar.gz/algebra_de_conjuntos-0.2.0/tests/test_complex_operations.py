from src.aos.CompoundSet import Intersection, Union
from src.aos.FloatSet import FloatSet


def test_operations():
    assert Intersection(
        [Union([FloatSet(2, 7), FloatSet(7, 13)]), FloatSet(5, 8)]
    ).execute() == FloatSet(5, 8)
    assert Intersection(
        [FloatSet(2, 7), Union([FloatSet(7, 13), FloatSet(5, 8)])]
    ).execute() == FloatSet(5, 7)
    assert Union(
        [Intersection([FloatSet(2, 7), FloatSet(7, 13)]), FloatSet(5, 8)]
    ).execute() == FloatSet(5, 8)
