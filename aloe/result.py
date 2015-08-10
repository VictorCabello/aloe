# Aloe - Cucumber runner for Python based on Lettuce and Nose
# Copyright (C) <2015> Danielle Madeley <danielle@madeley.id.au>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Cucumber-esque outputter for Nose.
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
# pylint:disable=redefined-builtin, unused-wildcard-import, wildcard-import
from builtins import *
# pylint:enable=redefined-builtin, unused-wildcard-import, wildcard-import
from future import standard_library
standard_library.install_aliases()

from contextlib import contextmanager
from functools import wraps

from aloe.registry import (
    CallbackDecorator,
    CALLBACK_REGISTRY,
    PriorityClass,
)
from aloe.strings import represent_table
from aloe.tools import hook_not_reentrant, _empty_generator
from blessings import Terminal
from nose.result import TextTestResult

# A decorator to add callbacks which wrap the steps looser than all the other
# callbacks.
# pylint:disable=invalid-name
outer_around = CallbackDecorator(CALLBACK_REGISTRY, 'around',
                                 priority_class=PriorityClass.DISPLAY)
# pylint:enable=invalid-name


TERMINAL = [None]


class OutputTerminal(Terminal):
    """
    Terminal object.
    """

    def write(self, arg='', return_=False):
        """
        Write to the stream.

        Takes an optional parameter `return_`
        """
        self.stream.write(arg)

        if return_:
            self.stream.write(self.move_up * arg.count('\n'))

    def writeln(self, arg='', return_=False):
        """Convenience function to write a line to the stream."""
        self.write(arg + '\n', return_=return_)

    @classmethod
    def required(cls, func):
        """Decorate this hook to only execute if term is available"""

        @wraps(func)
        def inner(*args, **kwargs):
            """Wrap func to check for term."""
            if not TERMINAL[0]:
                return _empty_generator()

            return func(TERMINAL[0], *args, **kwargs)

        return inner


@outer_around.each_feature
@contextmanager
@OutputTerminal.required
def feature_wrapper(term, feature):
    """Display feature execution."""

    try:
        if feature.tags:
            term.writeln(term.cyan(feature.represent_tags()))

        lines = feature.represented(annotate=False).splitlines()
        term.writeln(term.bold_white(lines[0]))
        term.writeln()
        term.writeln(term.white('\n'.join(lines[1:])))
        term.writeln()

        yield
    finally:
        pass


@outer_around.each_example
@contextmanager
@OutputTerminal.required
def example_wrapper(term, scenario, outline, steps):
    """Display scenario execution."""

    try:
        if scenario.tags:
            term.writeln(term.cyan(scenario.represent_tags()))

        # blessings doesn't degrade term.color nicely if there's no styling
        # available
        gray = term.color(8) if term.does_styling else str

        start, end = scenario.represented().rsplit('#')
        term.write(term.bold_white(start))
        term.writeln(gray(end))

        if outline:
            term.writeln(represent_table([outline.keys(),
                                          outline.values()],
                                         indent=6,
                                         cell_wrap=term.white))
            term.writeln()

        # write a preview of the steps
        if term.is_a_tty:
            steps_ = []

            if scenario.feature.background:
                steps_ += scenario.feature.background.steps

            steps_ += steps

            term.writeln(
                gray('\n'.join(
                    step.represented(annotate=False)
                    for step in steps_
                ) + '\n'),
                return_=True
            )

        yield
    finally:
        term.writeln()


@outer_around.each_step
@contextmanager
@OutputTerminal.required
@hook_not_reentrant
def step_wrapper(term, step):
    """Display step execution."""

    try:
        if term.is_a_tty:
            term.writeln(
                step.represented(annotate=False, color=term.color(11)),
                return_=True)

        yield
    finally:
        if step.passed:
            color = term.bold_green
        elif step.failed:
            color = term.bold_red
        else:
            color = term.yellow

        term.writeln(
            step.represented(annotate=False, color=color)
        )


class AloeTestResult(TextTestResult):
    """
    Cucumber test progress display (verbosity level 3).
    """
    # pylint:disable=too-many-arguments
    def __init__(self, stream, descriptions, verbosity,
                 config=None, errorClasses=None):
        super().__init__(stream, descriptions, verbosity,
                         config=config, errorClasses=errorClasses)
        self.showAll = verbosity == 2
        self.showSteps = verbosity >= 3  # pylint:disable=invalid-name

        if self.showSteps:
            TERMINAL[0] = OutputTerminal(
                stream=stream,
                force_styling=config.force_color)
        else:
            TERMINAL[0] = None  # unset the global
