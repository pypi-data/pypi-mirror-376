import numpy as np
from seiscod.trace import Trace


def test_trace_init():

    # empty initiation
    tr = Trace()
    assert isinstance(tr, Trace)

    # with attributes
    tr = Trace(
        seedid="ABCD",
        delta=0.1,
        starttime=1.0,
        longitude=2.0,
        latitude=3.0,
        elevation=4.0,
        distance=5.0,
        data=np.arange(10))
    assert isinstance(tr, Trace)


def test_trace_headerkeys():
    tr = Trace()
    for key in tr.header_keys:
        assert hasattr(tr, key)


def test_trace_datakeys():
    tr = Trace()
    for key in tr.data_keys:
        assert hasattr(tr, key)


def test_trace_additionalkeys():
    tr = Trace()
    tr.much = 1
    tr.more = 2

    assert "more" in tr.additional_keys
    assert "much" in tr.additional_keys
    assert len(tr.additional_keys) == 2


def test_trace_copy():
    tr = Trace(
        seedid="ABCD",
        delta=0.1,
        starttime=1.0,
        longitude=2.0,
        latitude=3.0,
        elevation=4.0,
        distance=5.0,
        data=np.arange(10))
    tr.more = 123

    copy = tr.copy()
    assert isinstance(copy, Trace)
    assert id(copy) != id(tr)

    # modify the copy
    copy.seedid="DEFG"
    copy.delta=0.2
    copy.starttime=2.0
    copy.longitude=4.0
    copy.latitude=6.0
    copy.elevation=8.0
    copy.distance=10.0
    copy.data=np.arange(20)
    copy.more = 456

    # make sure tr is unchanged
    assert tr.seedid == "ABCD"
    assert tr.delta == 0.1
    assert tr.starttime == 1.0
    assert tr.longitude == 2.0
    assert tr.latitude == 3.0
    assert tr.elevation == 4.0
    assert tr.distance == 5.0
    assert tr.more == 123
    assert np.all(tr.data == np.arange(10))


def test_trace_copy_except_data():
    tr = Trace(
        seedid="ABCD",
        delta=0.1,
        starttime=1.0,
        longitude=2.0,
        latitude=3.0,
        elevation=4.0,
        distance=5.0,
        data=np.arange(10))
    tr.more = 123

    copy = tr.copy(data=False)
    assert len(copy.data) == 0


def test_shallow_copy():
    tr = Trace(
        seedid="ABCD",
        delta=0.1,
        starttime=0.0,
        longitude=2.0,
        latitude=3.0,
        elevation=4.0,
        distance=5.0,
        data=np.arange(10))
    tr.more = 123

    tr1 = tr.shallow_copy_between(
        starttime=tr.starttime + 0.5 * tr.delta,
        endtime=tr.endtime - 0.5 * tr.delta)
    tr1.data[:] = 10.

    # make sure that tr has been modified has well
    assert (tr.data == np.array([0,10,10,10,10,10,10,10,10,9])).all()

