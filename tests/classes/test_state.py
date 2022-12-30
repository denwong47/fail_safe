# -*- coding: utf-8 -*-
import random

import pytest

from fail_safe import FailSafeState, LocalStorage


class KillIterator(StopIteration):
    """
    Arbitrarily stop the Iterator.
    """


@pytest.mark.parametrize(
    "stop_at",
    (
        0,
        24,
        63,
        64,
    ),
)
def test_state_usage(tmpdir, stop_at):
    TOTAL: int = 64
    STOP_AT: int = stop_at

    # This is NOT to be attached.
    dumb_var = None

    my_records = [
        {
            "id": random.randint(0, 2**16),
            "data": "%08x" % random.randint(0, 2**32),
        }
        for _ in range(TOTAL)
    ]
    my_records_iter = iter(my_records)

    output = []

    with pytest.raises(KillIterator):
        with (
            FailSafeState()
            .uses(LocalStorage(tmpdir))
            .attach("my_records", "my_records_iter")
            .attach("output")
            .attach("TOTAL", "STOP_AT")
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

    assert "my_records" not in locals()
    assert "my_records_iter" not in locals()
    assert "output" not in locals()

    # ==================================================================================
    # Now we mimic the second execution of the script

    with (
        FailSafeState()
        .uses(LocalStorage(tmpdir))
        .attach("my_records", "my_records_iter")
        .attach("output")
        .attach("TOTAL", "STOP_AT")
    ) as state:
        assert len(tuple(my_records_iter)) == (TOTAL - STOP_AT)
        assert len(output) == STOP_AT

        for _original, _new in zip(my_records, output):
            assert _original["id"] == _new["old_id"]
            assert _original["data"] == _new["old_data"]

            assert "new_id" in _new
            assert _new["new_data"] == _original["data"].upper()
