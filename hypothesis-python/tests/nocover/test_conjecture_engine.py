# coding=utf-8
#
# This file is part of Hypothesis, which may be found at
# https://github.com/HypothesisWorks/hypothesis-python
#
# Most of this work is copyright (C) 2013-2018 David R. MacIver
# (david@drmaciver.com), but it contains contributions by others. See
# CONTRIBUTING.rst for a full list of people who may hold copyright, and
# consult the git log if you need to determine who owns an individual
# contribution.
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
#
# END HEADER

from __future__ import division, print_function, absolute_import

from random import Random

import pytest

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from tests.common.utils import no_shrink, non_covering_examples
from hypothesis.database import InMemoryExampleDatabase
from hypothesis.internal.compat import hbytes, hrange, int_from_bytes
from tests.cover.test_conjecture_engine import run_to_buffer
from hypothesis.internal.conjecture.data import Status, ConjectureData
from hypothesis.internal.conjecture.engine import RunIsComplete, \
    ConjectureRunner


def test_lot_of_dead_nodes():
    @run_to_buffer
    def x(data):
        for i in range(5):
            if data.draw_bytes(1)[0] != i:
                data.mark_invalid()
        data.mark_interesting()
    assert x == hbytes([0, 1, 2, 3, 4])


def test_saves_data_while_shrinking():
    key = b'hi there'
    n = 5
    db = InMemoryExampleDatabase()
    assert list(db.fetch(key)) == []
    seen = set()

    def f(data):
        x = data.draw_bytes(512)
        if sum(x) >= 5000 and len(seen) < n:
            seen.add(hbytes(x))
        if hbytes(x) in seen:
            data.mark_interesting()
    runner = ConjectureRunner(
        f, settings=settings(database=db), database_key=key)
    runner.run()
    assert runner.interesting_examples
    assert len(seen) == n
    in_db = non_covering_examples(db)
    assert in_db.issubset(seen)
    assert in_db == seen


@given(st.randoms(), st.random_module())
@settings(
    phases=no_shrink, deadline=None,
    suppress_health_check=[HealthCheck.hung_test]
)
def test_maliciously_bad_generator(rnd, seed):
    @run_to_buffer
    def x(data):
        for _ in range(rnd.randint(1, 100)):
            data.draw_bytes(rnd.randint(1, 10))
        if rnd.randint(0, 1):
            data.mark_invalid()
        else:
            data.mark_interesting()


def test_can_discard():
    n = 32

    @run_to_buffer
    def x(data):
        seen = set()
        while len(seen) < n:
            seen.add(hbytes(data.draw_bytes(1)))
        data.mark_interesting()
    assert len(x) == n


def test_exhaustive_enumeration_of_partial_buffer():
    seen = set()

    def f(data):
        k = data.draw_bytes(2)
        assert k[1] == 0
        assert k not in seen
        seen.add(k)

    seen_prefixes = set()

    runner = ConjectureRunner(
        f, settings=settings(database=None, max_examples=256, buffer_size=2),
        random=Random(0),
    )
    with pytest.raises(RunIsComplete):
        runner.cached_test_function(b'')
        for _ in hrange(256):
            p = runner.generate_novel_prefix()
            assert p not in seen_prefixes
            seen_prefixes.add(p)
            data = ConjectureData.for_buffer(hbytes(p + hbytes(2)))
            runner.test_function(data)
            assert data.status == Status.VALID
            node = 0
            for b in data.buffer:
                node = runner.tree[node][b]
            assert node in runner.dead
    assert len(seen) == 256


def test_regression_1():
    # This is a really hard to reproduce bug that previously triggered a very
    # specific exception inside one of the shrink passes. It's unclear how
    # useful this regression test really is, but nothing else caught the
    # problem.
    @run_to_buffer
    def x(data):
        data.write(hbytes(b'\x01\x02'))
        data.write(hbytes(b'\x01\x00'))
        v = data.draw_bits(41)
        if v >= 512 or v == 254:
            data.mark_interesting()
    assert list(x)[:-2] == [1, 2, 1, 0, 0, 0, 0, 0]

    assert int_from_bytes(x[-2:]) in (254, 512)
