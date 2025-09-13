from src.aos.CompoundSet import Intersection, Union
from src.aos.constants import EMPTY_SET, UNIVERSE
from src.aos.FloatSet import FloatSet


class TestIntersection:
    def test_intersection_of_identical_floatsets_returns_same(self):
        assert Intersection(
            [FloatSet(1, 2), FloatSet(1, 2), FloatSet(1, 2)]
        ).execute() == FloatSet(1, 2)

    def test_intersection_of_nested_intersection_and_floatset(self):
        assert Intersection(
            [Intersection([FloatSet(1, 2), FloatSet(1, 2)]), FloatSet(1, 2)]
        ).execute() == FloatSet(1, 2)

    def test_intersection_of_overlapping_floatsets(self):
        assert Intersection(
            [FloatSet(1, 3), FloatSet(2, 7), FloatSet(1, 3)]
        ).execute() == FloatSet(2, 3)

    def test_intersection_of_subset_floatsets(self):
        assert Intersection(
            [FloatSet(0, 10), FloatSet(4, 6), FloatSet(4, 6)]
        ).execute() == FloatSet(4, 6)

    def test_intersection_of_disjoint_floatsets_is_empty(self):
        assert Intersection([FloatSet(0, 2), FloatSet(4, 7)]).execute().is_empty()

    def test_intersection_with_single_point_overlap(self):
        assert Intersection([FloatSet(4, 7), FloatSet(5, 5)]).execute() == FloatSet(
            5, 5
        )

    def test_intersection_with_full_overlap_returns_subset(self):
        assert Intersection([FloatSet(4, 6), FloatSet(0, 10)]).execute() == FloatSet(
            4, 6
        )

    def test_intersection_of_multiple_disjoint_sets_is_empty(self):
        assert (
            Intersection([FloatSet(0, 2), FloatSet(4, 7), FloatSet(5, 5)])
            .execute()
            .is_empty()
        )

    def test_intersection_with_empty_set_is_empty(self):
        assert Intersection([EMPTY_SET, UNIVERSE]).execute().is_empty()

    def test_intersection_of_universe_sets_returns_universe(self):
        assert Intersection([UNIVERSE, UNIVERSE]).execute() == UNIVERSE

    def test_intersection_is_empty(self):
        assert Intersection([EMPTY_SET, UNIVERSE]).is_empty()
        assert Intersection([FloatSet(1, 2), FloatSet(1, 2)]).is_empty() is False
        assert Intersection([FloatSet(1, 5), FloatSet(3, 9)]).is_empty() is False
        assert Intersection(
            [FloatSet(1, 5), FloatSet(6, 9), FloatSet(20, 30)]
        ).is_empty()

    def test_intersection_of_multiple_overlapping_sets(self):
        assert Intersection(
            [FloatSet(0, 10), FloatSet(2, 8), FloatSet(5, 6)],
        ).execute() == FloatSet(5, 6)
        assert Intersection(
            [FloatSet(0, 10), FloatSet(2, 8), FloatSet(5, 6), FloatSet(4, 7)],
        ).execute() == FloatSet(5, 6)

    def test_intersection_with_not_single_union(self):
        assert Intersection(
            [FloatSet(0, 10), Union([FloatSet(2, 4), FloatSet(6, 8)])]
        ).execute() == Union([FloatSet(2, 4), FloatSet(6, 8)])
        assert (
            Intersection(
                [
                    FloatSet(0, 10),
                    Union([FloatSet(2, 4), FloatSet(6, 8)]),
                    FloatSet(3, 7),
                ]
            ).execute()
            == Union([FloatSet(3, 4), FloatSet(6, 7)]).execute()
        )
