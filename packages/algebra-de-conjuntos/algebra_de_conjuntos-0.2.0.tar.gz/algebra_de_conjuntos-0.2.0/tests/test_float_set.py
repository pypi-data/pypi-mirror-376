from src.aos.constants import EMPTY_SET, UNIVERSE


def test_float_set():
    from src.aos.FloatSet import FloatSet

    assert FloatSet(1, 2) == FloatSet(1, 2)
    assert FloatSet(1, 2) != FloatSet(1, 3)
    assert FloatSet(1, 2) != FloatSet(2, 3)
    assert FloatSet(1, 2) != FloatSet(3, 4)
    assert EMPTY_SET == FloatSet(float("inf"), -float("inf"))
    assert UNIVERSE == FloatSet(-float("inf"), float("inf"))
    assert UNIVERSE == FloatSet(float("-inf"), float("inf"))
    assert UNIVERSE == UNIVERSE
    assert EMPTY_SET == EMPTY_SET
    assert EMPTY_SET.is_empty()
    assert FloatSet(-20, 50).is_empty() is False


def test_float_set_contains():
    from src.aos.FloatSet import FloatSet

    assert 1 in FloatSet(1, 2)
    assert FloatSet(1, 2) in FloatSet(1, 3)
    assert FloatSet(2, 2) in FloatSet(2, 3)
    assert FloatSet(1, 2) in FloatSet(0, 4)
    assert FloatSet(1, 2) in FloatSet(-10, 4)


def test_float_set_not_contains():
    from src.aos.FloatSet import FloatSet

    assert 0 not in FloatSet(1, 3)
    assert FloatSet(1, 2) not in FloatSet(2, 3)
    assert FloatSet(1, 2) not in FloatSet(3, 4)
