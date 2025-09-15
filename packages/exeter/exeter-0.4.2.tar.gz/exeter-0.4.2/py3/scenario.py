#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Assorted Python languange tests for Scenarios"""

import dataclasses
from typing import Iterator

import exeter


@dataclasses.dataclass
class SimpleScenario(exeter.Scenario):
    val: bool

    @exeter.scenariotest
    def pass_if(self) -> None:
        assert self.val

    @exeter.scenariotest
    def fail_if(self) -> None:
        assert not self.val


@SimpleScenario.test
def setup_true() -> Iterator[SimpleScenario]:
    yield SimpleScenario(True)


@SimpleScenario.test
def setup_false() -> Iterator[SimpleScenario]:
    yield SimpleScenario(False)


@dataclasses.dataclass
class CompoundScenario(exeter.Scenario):
    val1: bool
    val2: bool

    @exeter.scenariotest
    def is_equal(self) -> None:
        assert self.val1 == self.val2

    @SimpleScenario.subscenario
    def test_val1(self) -> SimpleScenario:
        return SimpleScenario(self.val1)

    @SimpleScenario.subscenario
    def test_val2(self) -> SimpleScenario:
        return SimpleScenario(self.val2)


@CompoundScenario.test
def setup_ff() -> Iterator[CompoundScenario]:
    yield CompoundScenario(False, False)


@CompoundScenario.test
def setup_ft() -> Iterator[CompoundScenario]:
    yield CompoundScenario(False, True)


@CompoundScenario.test
def setup_tf() -> Iterator[CompoundScenario]:
    yield CompoundScenario(True, False)


@CompoundScenario.test
def setup_tt() -> Iterator[CompoundScenario]:
    yield CompoundScenario(True, True)


def outer_scenario_function() -> None:
    """Function to test Scenario.test decorator on local functions"""
    @SimpleScenario.test
    def local_scenario_setup() -> Iterator[SimpleScenario]:
        """Test that Scenario.test works on local functions"""
        yield SimpleScenario(True)


def outer_class_function() -> None:
    """Function to test local Scenario classes"""

    class LocalScenario(exeter.Scenario):
        @exeter.scenariotest
        def local_test(self) -> None:
            pass

    @LocalScenario.test
    def local_class_setup() -> Iterator[LocalScenario]:
        """Test that local Scenario classes work"""
        yield LocalScenario()


# Register the local scenario test by calling the outer function
outer_scenario_function()

# Register the local class test by calling the outer function
outer_class_function()


if __name__ == '__main__':
    exeter.main()
