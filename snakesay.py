#!/usr/bin/env python3.6
import sys
import textwrap


def snakesay(*things):
    return '\n'.join(speech_bubble_lines(' '.join(things))) + r"""
         \
          ~<:>>>>>>>>>
    """


def speech_bubble_lines(speech):
    lines, width = rewrap(speech)
    yield "  " + "_" * width

    if len(lines) <= 1:
        text = ''.join(lines)
        yield f'< {text} >'

    else:
        yield f'/{lines[0]}\\'
        for line in lines[1:-1]:
            yield f"|{line}|"
        yield f'\{lines[-1]}/'

    yield "  " + "-" * width


def rewrap(speech):
    lines = textwrap.wrap(speech)
    width = max(len(l) for l in lines)
    return [line.ljust(width) for line in lines], width


if __name__ == '__main__':
    print(snakesay(*sys.argv[1:]))
