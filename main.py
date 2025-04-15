import re
import keyword

# Python keywords
KEYWORDS = set(keyword.kwlist)

# Python operators (sorted by length to match multi-char operators first)
OPERATORS = sorted([
    '**=', '//=', '==', '!=', '<=', '>=', '**', '//',
    '+=', '-=', '*=', '/=', '%=', '=', '<', '>', '+', '-', '*', '/', '%',
    'and', 'or', 'not', 'is', 'in'
], key=lambda x: -len(x))

DELIMITERS = {'(', ')', '[', ']', '{', '}', ':', ',', '.', ';', '@'}

def is_keyword(token):
    return token in KEYWORDS

def is_operator(token):
    return token in OPERATORS

def is_delimiter(ch):
    return ch in DELIMITERS

def is_identifier(token):
    return re.match(r'^[A-Za-z_][A-Za-z_0-9]*$', token) is not None

def is_integer(token):
    return re.match(r'^[+-]?\d+$', token) is not None

def is_float(token):
    return re.match(r'^[+-]?(\d+\.\d*|\.\d+)$', token) is not None

def is_string(token):
    return re.match(r'^(".*?"|\'.*?\')$', token) is not None

def tokenize_python_code(line):
    # Remove comments first
    line = re.sub(r'#.*', '', line)

    token_specification = [
        ('STRING',   r'(\".*?\"|\'.*?\')'),
        ('FLOAT',    r'[+-]?(\d+\.\d*|\.\d+)'),
        ('INTEGER',  r'[+-]?\d+'),
        ('IDENTIFIER', r'[A-Za-z_][A-Za-z_0-9]*'),
        ('OPERATOR', '|'.join(map(re.escape, OPERATORS))),
        ('DELIMITER', r'[()\[\]{}:;,\.@]'),
        ('SKIP',     r'\s+'),
        ('MISMATCH', r'.'),  # Any other character
    ]

    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
    tokens = []

    for mo in re.finditer(tok_regex, line):
        kind = mo.lastgroup
        value = mo.group()

        if kind == 'STRING':
            tokens.append((value, 'STRING'))
        elif kind == 'FLOAT':
            tokens.append((value, 'FLOAT'))
        elif kind == 'INTEGER':
            tokens.append((value, 'INTEGER'))
        elif kind == 'IDENTIFIER':
            if is_keyword(value):
                tokens.append((value, 'KEYWORD'))
            elif is_operator(value):  # 'and', 'or', 'not', 'is', 'in'
                tokens.append((value, 'OPERATOR'))
            else:
                tokens.append((value, 'IDENTIFIER'))
        elif kind == 'OPERATOR':
            tokens.append((value, 'OPERATOR'))
        elif kind == 'DELIMITER':
            tokens.append((value, 'DELIMITER'))
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            tokens.append((value, 'UNKNOWN'))

    return tokens

def main():
    test_lines = [
        'def greet(name):',
        '    print("Hello, " + name)',
        '    if name == "Alice":',
        '        print("Welcome back!")',
        'greet("Alice") # This is a comment'
    ]

    print("Lexical Analysis Output:")
    for line in test_lines:
        print(f"\nAnalyzing: {line}")
        tokens = tokenize_python_code(line)
        for token, token_type in tokens:
            print(f"{token:<15} --> {token_type}")

if __name__ == "__main__":
    main()
