from datetime import timedelta

from toolbox import utils


def test_time_delta_string():
    # > 1s.
    assert utils.timedelta_str(0) == "0 seconds"
    assert utils.timedelta_str(60) == "1 minute"
    assert utils.timedelta_str(120) == "2 minutes"
    assert utils.timedelta_str(3_600) == "1 hour"
    assert utils.timedelta_str(-3_600) == "-1 hour"
    assert (
        utils.timedelta_str(111111111111)
        == "3,523 years 16 weeks 1 day 5 hours 31 minutes 51 seconds"
    )

    # Sub 1s.
    assert utils.timedelta_str(0.01) == "10 ms"
    assert utils.timedelta_str(0.000000001) == "1 ns"
    assert utils.timedelta_str(0.000000000001) == "1 ps"
    assert (
        utils.timedelta_str(111111111111.111111111111)
        == "3,523 years 16 weeks 1 day 5 hours 31 minutes 51 seconds 111 ms 114 μs 501 ns 953 ps"
    )
    
    # Timedelta.
    assert utils.timedelta_str(timedelta(hours=1)) == "1 hour"


def test_bytes_str():
    assert utils.bytes_str(0) == "0 bytes"
    assert utils.bytes_str(1) == "1 byte"
    assert utils.bytes_str(1024) == "1 KB"
    assert utils.bytes_str(2048) == "2 KB"
    assert utils.bytes_str(1023) == "1,023 bytes"
    assert utils.bytes_str(-1024) == "-1 KB"


def test_find():
    assert utils.find([1, 2, 3, 4], lambda n: n > 2) == 3
    assert utils.find([1, 2, 3, 4], lambda n: n < 0) is None
    assert utils.find([1, 2, 3, 4], lambda n: n > 4) is None
