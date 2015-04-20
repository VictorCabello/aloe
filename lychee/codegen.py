# Lychee - Cucumber runner for Python based on Lettuce and Nose
# Copyright (C) <2015> Alexey Kotlyarov <a@koterpillar.com>
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

# Code generation helpers

import ast
import re


FUNCTION_DEF_SAMPLE = ast.parse('def func(): pass')


def make_function(source, context=None, source_file=None, name=None):
    """
    Compile and evaluate given source to a function given the specified
    globals.
    Optionally set the file and name of the function.
    """

    func = ast.parse(source)

    # TODO: Check that generated code is a function
    if type(func) != type(FUNCTION_DEF_SAMPLE) \
            or len(func.body) != 1 \
            or type(func.body[0]) != type(FUNCTION_DEF_SAMPLE.body[0]):
        raise ValueError("source must be a function definition.")

    # Set or record the function name
    if name is not None:
        func.body[0].name = name
    else:
        name = func.body[0].name

    # TODO: What's a better default for file?
    if source_file is None:
        source_file = '<generated>'

    context = context or {}

    code = compile(func, source_file, 'exec')
    eval(code, context)

    return context[name]


def indent(source, count=1):
    """
    Indent the source by count*4 spaces.
    """

    prepend = ' ' * 4 * count
    return '\n'.join(
        # Only indent the non-empty lines
        prepend + line if line else line
        for line in source.split('\n')
    )


NOT_SPACE = re.compile('[^ ]')


def remove_indent(source):
    """
    Remove as much indentation as possible from the code.
    """

    lines = source.split('\n')
    min_indent = min(
        match.start() for match in (
            NOT_SPACE.search(line)
            for line in lines
        ) if match
    )

    return '\n'.join(
        line[min_indent:]
        for line in lines
    )
