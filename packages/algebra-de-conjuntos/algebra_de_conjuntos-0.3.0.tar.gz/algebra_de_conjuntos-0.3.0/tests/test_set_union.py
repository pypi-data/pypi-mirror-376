from src.aos.CompoundSet import Union
from src.aos.constants import EMPTY_SET, UNIVERSE
from src.aos.FloatSet import FloatSet


class TestUnionClass:
    def test_union_identical_sets(self):
        assert Union(
            [FloatSet(1, 2), FloatSet(1, 2), FloatSet(1, 2)]
        ).execute() == FloatSet(1, 2)

    def test_union_overlapping_sets(self):
        assert Union(
            [FloatSet(1, 3), FloatSet(2, 7), FloatSet(1, 3)]
        ).execute() == FloatSet(1, 7)

    def test_union_subset_sets(self):
        assert Union(
            [FloatSet(0, 10), FloatSet(4, 6), FloatSet(4, 6)]
        ).execute() == FloatSet(0, 10)

    def test_union_disjoint_sets(self):
        assert Union([FloatSet(0, 2), FloatSet(4, 7)]).execute() == Union(
            [FloatSet(0, 2), FloatSet(4, 7)]
        )

    def test_union_disjoint_sets_order(self):
        assert Union([FloatSet(3, 7), FloatSet(0, 2)]).execute() == Union(
            [FloatSet(0, 2), FloatSet(3, 7)]
        )

    def test_union_is_empty(self):
        assert Union([EMPTY_SET, EMPTY_SET]).is_empty()
        assert Union([EMPTY_SET, UNIVERSE]).is_empty() is False
        assert Union([FloatSet(1, 2), FloatSet(1, 2)]).is_empty() is False
        assert Union([FloatSet(1, 5), FloatSet(3, 9)]).is_empty() is False

    def test_union_multiple_overlapping_sets(self):
        assert Union(
            [FloatSet(0, 3), FloatSet(2, 8), FloatSet(5, 26)],
        ).execute() == FloatSet(0, 26)
        assert Union(
            [FloatSet(0, 3), FloatSet(2, 8), FloatSet(5, 26), FloatSet(20, 30)],
        ).execute() == FloatSet(0, 30)
