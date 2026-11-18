import pytest
from render import fog_volume as mod

CASES = [
    ("slice_near", "m.slice_depth(0, 4, 1.0, 100.0) >= 1.0"),
    ("slice_monotonic", "m.slice_depth(1, 4, 1.0, 100.0) > m.slice_depth(0, 4, 1.0, 100.0)"),
    ("slice_below_far", "m.slice_depth(3, 4, 1.0, 100.0) < 100.0"),
    ("spot_outside", "m.spot_weight(-1.0, 0.866, 0.985) == 0.0"),
    ("spot_inside", "m.spot_weight(1.0, 0.866, 0.985) == 1.0"),
    ("spot_mid", "0.0 < m.spot_weight(0.94, 0.866, 0.985) < 1.0"),
    ("upsample_sum", "m.upsample_weight(1.0, 2.0) + m.upsample_weight(2.0, 1.0) == approx(1.0)"),
    ("upsample_near", "m.upsample_weight(1.0, 2.0) > m.upsample_weight(2.0, 1.0)"),
    ("history_same", "m.history_is_valid(1.0, 1.0) is True"),
    ("history_change", "m.history_is_valid(1.0, 1.2) is False"),
    ("tri_sum", "sum(m.triplanar_weight(1.0, 2.0, 3.0)) == approx(1.0)"),
    ("tri_dominant", "m.triplanar_weight(1.0, 2.0, 3.0)[1] == max(m.triplanar_weight(1.0, 2.0, 3.0))"),
    ("box_inside", "m.density_in_box((0.5, 0.5, 0.5), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)) is True"),
    ("box_outside", "m.density_in_box((2.0, 0.5, 0.5), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)) is False"),
    ("tri_zero", "sum(m.triplanar_weight(0.0, 0.0, 0.0)) == approx(1.0)")
]

@pytest.mark.parametrize("name,expr", CASES, ids=[c[0] for c in CASES])
def test_contract(name, expr):
    assert eval(expr, {"m": mod, "approx": pytest.approx})
