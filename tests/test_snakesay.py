from snakesay import snakesay, MESSAGE


def test_nothing():
    assert "~<:>>>>>>>>>" in snakesay()
    assert snakesay() == MESSAGE.format(bubble='<  >')


def test_one_line():
    assert '< hi there >' in snakesay('hi there')


def test_two_lines():
    two_lines = 'a' * 81
    message = snakesay(two_lines)
    print(message)
    assert r'/ aaaaaa' in message
    assert 'aaaaaa \\' in message
    assert r'\ aaaaaa' in message


def test_three_lines():
    three_lines = 'a' * 80 * 2 + 'a'
    long_message = snakesay(three_lines)
    print(long_message)
    assert r'/ aaaaaa' in long_message
    assert 'aaaaaa \\' in long_message

    assert r'| aaaaaa' in long_message
    assert r'aaaaaa |' in long_message

    assert r'\ aaaaaa' in long_message


def test_multiple_arguments():
    assert '< hi there >' in snakesay('hi', 'there')
