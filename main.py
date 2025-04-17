import re
import keyword

#Lexer
KEYWORDS = set(keyword.kwlist)
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

def tokenise_python_code(line):
    line = re.sub(r'#.*', '', line)
    token_specification = [
        ('STRING',   r'(\".*?\"|\'.*?\')'),
        ('FLOAT',    r'[+-]?(\d+\.\d*|\.\d+)'),
        ('INTEGER',  r'[+-]?\d+'),
        ('IDENTIFIER', r'[A-Za-z_][A-Za-z_0-9]*'),
        ('OPERATOR', '|'.join(map(re.escape, OPERATORS))),
        ('DELIMITER', r'[()\[\]{}:;,\.@]'),
        ('SKIP',     r'\s+'),
        ('MISMATCH', r'.'),
    ]
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
    tokens = []

    for mo in re.finditer(tok_regex, line):
        kind = mo.lastgroup
        value = mo.group()

        if kind == 'SKIP':
            continue
        elif kind == 'IDENTIFIER' and is_keyword(value):
            tokens.append((value, 'KEYWORD'))
        elif kind == 'IDENTIFIER' and is_operator(value):
            tokens.append((value, 'OPERATOR'))
        else:
            tokens.append((value, kind))

    return tokens

#Syntax tree nodes
class Node: pass
class Number(Node):
    def __init__(self, value):
        self.value = int(value)
class String(Node):
    def __init__(self, value):
        self.value = value.strip('"').strip('"')
class BinOp(Node):
    def __init__(self, left, op, right):
        self.value = self.left, self.op, self.right = left, op, right
class Var(Node):
    def __init__(self, name):
        self.name = self.name = name
class Assign(Node):
    def __init__(self, name, expr):
        self.name, self.expr = name, expr
class Print(Node):
    def __init__(self, expr):
        self.expr = expr        
class If(Node):
    def __init__(self, condition, body):
        self.condition, self.body = condition, body

#Parser
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens 
        self.pos = 0
        
#Interpreter
class Interpreter:
