#!/usr/bin/env python3.5
import sys
import textwrap

MESSAGE = '\n'.join([
    '',
    '{bubble}',
    '   \\',
    '    ~<:>>>>>>>>>',

])


def snakesay(*things):
    bubble = '\n'.join(speech_bubble_lines(' '.join(things)))
    return MESSAGE.format(bubble=bubble)


def speech_bubble_lines(speech):
    lines, width = rewrap(speech)
    if len(lines) <= 1:
        text = ''.join(lines)
        yield '< {text} >'.format(text=text)

    else:
        yield '  ' + '_' * width
        yield '/ ' + (' ' * width) + ' \\'
        for line in lines:
            yield '| {} |'.format(line)
        yield '\\ ' + (' ' * width) + ' /'
        yield '  ' + '-' * width


def rewrap(speech):
    lines = textwrap.wrap(speech)
    width = max(len(l) for l in lines) if lines else 0
    return [line.ljust(width) for line in lines], width



if __name__ == '__main__':
    print(snakesay(*sys.argv[1:]))
