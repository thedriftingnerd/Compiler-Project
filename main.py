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

    def peek(self): return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)
    def advance(self): self.pos += 1

    def expect(self, value):  # ensures current token == value
        tok, typ = self.peek()
        if tok != value:
            raise SyntaxError(f"Expected '{value}' but got '{tok}'")
        self.advance()
    
    def parse(self):
        ast = []
        while self.pos < len(self.tokens):
            ast.append(self.statement())
        return ast

    def statement(self):
        tok, typ = self.peek()
        if tok == 'print':
            self.advance()
            self.expect('(')
            expr = self.expr()
            self.expect(')')
            return Print(expr)
        elif typ == 'IDENTIFIER':
            name = tok
            self.advance()
            self.expect('=')
            expr = self.expr()
            return Assign(name, expr)
        elif tok == 'if':
            self.advance()
            cond = self.expr()
            self.expect(':')
            # Assume single statement body for simplicity
            return If(cond, self.statement())
        else:
            raise SyntaxError(f"Unexpected token: {tok}")

    def expr(self):
        node = self.term()
        while self.peek()[0] in ('+', '-'):
            op = self.peek()[0]
            self.advance()
            node = BinOp(node, op, self.term())
        return node

    def term(self):
        node = self.factor()
        while self.peek()[0] in ('*', '/', '%'):
            op = self.peek()[0]
            self.advance()
            node = BinOp(node, op, self.factor())
        return node

    def factor(self):
        tok, typ = self.peek()
        if typ == 'INTEGER':
            self.advance()
            return Number(tok)
        elif typ == 'STRING':
            self.advance()
            return String(tok)
        elif typ == 'IDENTIFIER':
            self.advance()
            return Var(tok)
        elif tok == '(':
            self.advance()
            node = self.expr()
            self.expect(')')
            return node
        else:
            raise SyntaxError(f"Unexpected factor: {tok}")

#Interpreter
class Interpreter:
    def __init__(self): self.env = {}

    def eval(self, node):
        if isinstance(node, Number): return node.value
        elif isinstance(node, String): return node.value
        elif isinstance(node, Var): return self.env.get(node.name, None)
        elif isinstance(node, BinOp):
            left = self.eval(node.left)
            right = self.eval(node.right)
            return self.apply_op(node.op, left, right)
        elif isinstance(node, Assign):
            val = self.eval(node.expr)
            self.env[node.name] = val
        elif isinstance(node, Print):
            print(self.eval(node.expr))
        elif isinstance(node, If):
            if self.eval(node.condition):
                self.eval(node.body)

    def apply_op(self, op, l, r):
        if op == '+': return l + r
        if op == '-': return l - r
        if op == '*': return l * r
        if op == '/': return l // r
        if op == '%': return l % r
        raise RuntimeError(f"Unsupported operator {op}")

#---------------
#Runner
def run_interpreter(source_lines):
    interpreter = Interpreter()
    for line_num, line in enumerate(source_lines, 1):
        try:
            tokens = tokenise_python_code(line)
            parser = Parser(tokens)
            ast = parser.parse()
            for node in ast:
                interpreter.eval(node)
        except Exception as e:
            print(f"Syntax error on line {line_num}: {e}")

#---------------
#Sample to test with
if __name__ == "__main__":
    code = [
        'x = 10',
        'y = 20',
        'print(x + y)',
        'if x: print("X is not zero")',
        'print("Done")'
    ]
    run_interpreter(code)