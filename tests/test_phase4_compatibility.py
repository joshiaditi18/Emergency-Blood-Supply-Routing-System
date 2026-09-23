from backend.app.utils.blood_compatibility import compatible_donor_groups, is_compatible_donor


def test_red_cell_compatibility_matrix():
    assert compatible_donor_groups("O+") == frozenset({"O+", "O-"})
    assert compatible_donor_groups("O-") == frozenset({"O-"})
    assert compatible_donor_groups("A+") == frozenset({"A+", "A-", "O+", "O-"})
    assert compatible_donor_groups("AB+") == frozenset({"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"})
    assert is_compatible_donor("A+", "A-")
    assert not is_compatible_donor("O-", "O+")
