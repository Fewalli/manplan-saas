import pytest

from app.services.time_rules import dhm_to_minutes


def test_dhm_to_minutes_success() -> None:
    assert dhm_to_minutes(1, 2, 3) == 1563


@pytest.mark.parametrize(
    ("days", "hours", "minutes"),
    [
        (-1, 0, 0),
        (31, 0, 0),
        (0, 24, 0),
        (0, -1, 0),
        (0, 0, 60),
        (0, 0, -1),
    ],
)
def test_dhm_to_minutes_invalid_limits(days: int, hours: int, minutes: int) -> None:
    with pytest.raises(ValueError):
        dhm_to_minutes(days, hours, minutes)