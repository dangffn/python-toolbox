from toolbox.functions.misc import largest_first_distribution




def test_distribution():
    grp_10 = list(largest_first_distribution(range(100), 10, lambda i: i))
    grp_5 = list(largest_first_distribution(range(5), 10, lambda i: i))
    grp_0 = list(largest_first_distribution(range(0), 10, lambda i: i))

    assert len(grp_10) == 10, "Correct number of groups created"
    assert len(grp_5) == 5, "Correct number of groups created"
    assert len(grp_0) == 0, "No groups created"
