# coding=utf-8

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# Most of this work is copyright (C) 2013-2015 David R. MacIver
# (david@drmaciver.com), but it contains contributions by other. See
# https://github.com/DRMacIver/hypothesis/blob/master/CONTRIBUTING.rst for a
# full list of people who may hold copyright, and consult the git log if you
# need to determine who owns an individual contribution.

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals

import sys
import math

import pytest
import hypothesis.strategies as st
from hypothesis import find, given, assume


@pytest.mark.parametrize(('l', 'r'), [
    # Exact values don't matter, but they're large enough so that x + y = inf.
    (9.9792015476736e+291, 1.7976931348623157e+308),
    (-sys.float_info.max, sys.float_info.max)
])
def test_floats_are_in_range(l, r):
    @given(st.floats(l, r))
    def test_is_in_range(t):
        assert l <= t <= r
    test_is_in_range()


def test_can_generate_both_zeros():
    find(
        st.tuples(st.floats(), st.floats()),
        lambda x: assume(x[0] == x[1]) and (
            math.copysign(1, x[0]) != math.copysign(1, x[1])
        )
    )


@pytest.mark.parametrize(('l', 'r'), [
    (-1.0, 1.0),
    (-0.0, 1.0),
    (-1.0, 0.0),
    (-sys.float_info.min, sys.float_info.min),
])
def test_can_generate_both_zeros_when_in_interval(l, r):
    interval = st.floats(l, r)
    find(interval, lambda x: assume(x == 0) and math.copysign(1, x) == 1)
    find(interval, lambda x: assume(x == 0) and math.copysign(1, x) == -1)


@given(st.floats(0.0, 1.0))
def test_does_not_generate_negative_if_right_boundary_is_positive(x):
    assert math.copysign(1, x) == 1


@given(st.floats(-1.0, -0.0))
def test_does_not_generate_positive_if_right_boundary_is_negative(x):
    assert math.copysign(1, x) == -1


@pytest.mark.parametrize(('l', 'r'), [
    (0.0, 1.0),
    (-1.0, 0.0),
    (-sys.float_info.min, sys.float_info.min),
])
def test_can_generate_interval_endpoints(l, r):
    interval = st.floats(l, r)
    find(interval, lambda x: x == l)
    find(interval, lambda x: x == r)


def test_half_bounded_generates_endpoint():
    find(st.floats(min_value=-1.0), lambda x: x == -1.0)
    find(st.floats(max_value=-1.0), lambda x: x == -1.0)


def test_half_bounded_generates_zero():
    find(st.floats(min_value=-1.0), lambda x: x == 0.0)
    find(st.floats(max_value=1.0), lambda x: x == 0.0)


@given(st.floats(max_value=-0.0))
def test_half_bounded_respects_sign_of_upper_bound(x):
    assert math.copysign(1, x) == -1


@given(st.floats(min_value=0.0))
def test_half_bounded_respects_sign_of_lower_bound(x):
    assert math.copysign(1, x) == 1