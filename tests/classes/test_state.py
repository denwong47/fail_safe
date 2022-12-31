# -*- coding: utf-8 -*-
import random

import pytest

from fail_safe import FailSafeState, LocalStorage, storage


class KillIterator(StopIteration):
    """
    Arbitrarily stop the Iterator.
    """


TOTAL: int = 64


@pytest.fixture
def records():
    return [
        {
            "id": random.randint(0, 2**16),
            "data": "%08x" % random.randint(0, 2**32),
        }
        for _ in range(TOTAL)
    ]


@pytest.mark.parametrize(
    "stop_at",
    (
        0,
        24,
        TOTAL - 1,
        TOTAL,
    ),
)
def test_state_usage(tmpdir, stop_at, records):
    STOP_AT: int = stop_at

    # This is NOT to be attached.
    dumb_var = None

    my_records = records.copy()
    my_records_iter = iter(my_records)

    output = []

    with pytest.raises(KillIterator):
        with (
            FailSafeState()
            .uses(LocalStorage(tmpdir))
            .attach("my_records", "my_records_iter")
            .attach("output")
            .attach("STOP_AT")
        ) as state:
            for _i, _item in zip(range(STOP_AT), my_records_iter):
                """
                Consume some elements of the the iterator.
                """
                output.append(
                    {
                        "old_id": _item.get("id"),
                        "new_id": _i,
                        "old_data": _item.get("data"),
                        "new_data": _item.get("data").upper(),
                    }
                )

            raise KillIterator("Iterator Killed.")

    # ==================================================================================
    # Wipe the slate

    del my_records
    del my_records_iter
    del output
    del dumb_var

    assert "my_records" not in locals()
    assert "my_records_iter" not in locals()
    assert "output" not in locals()

    # ==================================================================================
    # Now we mimic the second execution of the script

    with (
        FailSafeState()
        .uses(LocalStorage(tmpdir))
        .attach("my_records_iter")  # my_records is missing here
        .attach("output")
        .attach("STOP_AT")
    ) as state:
        assert len(tuple(my_records_iter)) == (TOTAL - STOP_AT)
        assert len(output) == STOP_AT

        # This should be filtered out, even if the
        # state contains the data
        assert "my_records" not in locals()
        assert "dumb_var" not in locals()

        # Now we reinstate it after the asserting that the filtering works.
        my_records = records.copy()

        for _original, _new in zip(my_records, output):
            assert _original["id"] == _new["old_id"]
            assert _original["data"] == _new["old_data"]

            assert "new_id" in _new
            assert _new["new_data"] == _original["data"].upper()

    # ==================================================================================
    # Now we set `when_complete(storage.RETAIN)`, and see if the data persisted.

    with (
        FailSafeState()
        .uses(store := LocalStorage(tmpdir))
        .attach("my_records", "my_records_iter")
        .attach("output")
        .attach("STOP_AT")
        .when_complete(storage.RETAIN)
    ) as state:
        # At this point, no cache should exist until __exit__.
        assert not store.load_data(state.name)

    del my_records
    del my_records_iter
    del output

    with (
        FailSafeState()
        .uses(LocalStorage(tmpdir))
        .attach("my_records", "my_records_iter")
        .attach("output")
        .attach("STOP_AT")
    ) as state:
        # Check if the data is retained even when successful
        for _original, _new in zip(my_records, output):
            assert _original["id"] == _new["old_id"]
            assert _original["data"] == _new["old_data"]

            assert "new_id" in _new
            assert _new["new_data"] == _original["data"].upper()

        # This time we have when_complete(storage.DELETE) as default

    # ==================================================================================
    # Because the last execution was successful, there should not be any states to be
    # loaded

    del my_records
    del my_records_iter
    del output

    assert "my_records" not in locals()
    assert "my_records_iter" not in locals()
    assert "output" not in locals()

    with (
        FailSafeState()
        .uses(LocalStorage(tmpdir))
        .attach("my_records", "my_records_iter")
        .attach("output")
        .attach("STOP_AT")
    ) as state:
        assert "my_records" not in locals()
        assert "my_records_iter" not in locals()
        assert "output" not in locals()


@pytest.mark.parametrize(
    "case",
    range(5),
)
def test_state_edge_cases(case, tmpdir):
    dumb_var = 1

    if case == 0:
        # Bad directory
        with pytest.raises(OSError):
            with (
                FailSafeState()
                .uses(store := LocalStorage(tmpdir / "/bad_dir"))
                .attach("dumb_var")
            ) as state:
                pass

    elif case == 1:
        # No StateStorage used
        with pytest.raises(ValueError):
            with (FailSafeState().attach("dumb_var")) as state:
                pass

    elif case == 2:
        # No attachments
        with pytest.raises(KillIterator):
            with (FailSafeState().uses(LocalStorage(tmpdir))) as state:
                raise KillIterator("Iterator killed.")

        del dumb_var
        with (FailSafeState().uses(LocalStorage(tmpdir))) as state:
            assert dumb_var == 1

    elif case == 3:
        # Attaching non-string
        with pytest.raises(TypeError):
            with (FailSafeState().uses(LocalStorage(tmpdir)).attach(0)) as state:
                pass

    elif case == 4:
        # Repeated errors
        for _ in range(8):
            with pytest.raises(KillIterator):
                with (
                    FailSafeState().uses(LocalStorage(tmpdir)).attach("dumb_var")
                ) as state:
                    dumb_var += 1
                    raise KillIterator("Iterator killed.")

            del dumb_var  # WTF

        with (FailSafeState().uses(LocalStorage(tmpdir)).attach("dumb_var")) as state:
            assert dumb_var == 9


@pytest.mark.parametrize(
    ("reset_condition", "reset"),
    [
        (True, True),
        (False, False),
        (lambda: True, True),
        (lambda: False, False),
    ],
)
def test_state_reset_condition(reset_condition, reset, tmpdir):
    """
    See if :meth:`FailSafeState.reset_if` is working.
    """
    dumb_var = 0
    state = (
        FailSafeState()
        .uses(LocalStorage(tmpdir))
        .attach("dumb_var")
        .when_complete(storage.RETAIN)
        .reset_if(reset_condition)
    )

    with state:
        dumb_var += 1

    # reset variable to 0
    dumb_var = 0

    with state:
        assert dumb_var == (0 if reset else 1)
