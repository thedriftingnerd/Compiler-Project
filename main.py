import re
import keyword
import subprocess

# Lexer definitions
KEYWORDS = set(keyword.kwlist)
OPERATORS = sorted([
    '**=', '//=', '==', '!=', '<=', '>=', '**', '//',
    '+=', '-=', '*=', '/=', '%=', '=', '<', '>', '+', '-', '*', '/', '%',
    'and', 'or', 'not', 'is', 'in'
], key=lambda x: -len(x))  # sort by length to match longest operator first

# Tokenizer
def tokenise_python_code(line):
    """Convert a line of Python source into (token, kind) pairs."""
    line = re.sub(r'#.*', '', line)  # strip comments
    token_spec = [
        ('STRING',   r'(\".*?\"|\'.*?\')'),
        ('FLOAT',    r'[+-]?(\d+\.\d*|\.\d+)'),
        ('INTEGER',  r'[+-]?\d+'),
        ('IDENT',    r'[A-Za-z_][A-Za-z0-9_]*'),
        ('OP',       '|'.join(map(re.escape, OPERATORS))),
        ('SKIP',     r'\s+'),
        ('MISMATCH', r'.'),
    ]
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_spec)
    tokens = []
    for mo in re.finditer(tok_regex, line):
        kind, val = mo.lastgroup, mo.group()
        if kind == 'SKIP':
            continue
        if kind == 'IDENT':
            if val in KEYWORDS:
                kind = 'KEYWORD'
            elif val in OPERATORS:
                kind = 'OP'
        tokens.append((val, kind))
    return tokens

# AST node classes
class Node: pass
class Number(Node):
    def __init__(self, v): self.value = int(v)
class String(Node):
    def __init__(self, v): self.value = v[1:-1]
class Var(Node):
    def __init__(self, n): self.name = n
class BinOp(Node):
    def __init__(self, l, o, r): self.left, self.op, self.right = l, o, r
class Assign(Node):
    def __init__(self, n, e): self.name, self.expr = n, e
class Print(Node):
    def __init__(self, e): self.expr = e
class If(Node):
    def __init__(self, c, b): self.cond, self.body = c, b

# Recursive-descent Parser
class Parser:
    def __init__(self, tokens):
        self.toks, self.pos = tokens, 0
    def peek(self):
        return self.toks[self.pos] if self.pos < len(self.toks) else (None, None)
    def advance(self):
        self.pos += 1
    def expect(self, val):
        t, _ = self.peek()
        if t != val:
            raise SyntaxError(f"Expected {val}, got {t}")
        self.advance()
    def parse(self):
        stmts = []
        while self.pos < len(self.toks):
            stmts.append(self.statement())
        return stmts
    def statement(self):
        t, typ = self.peek()
        if t == 'print':
            self.advance(); self.expect('(')
            e = self.expr(); self.expect(')')
            return Print(e)
        if typ == 'IDENT':
            name = t; self.advance(); self.expect('=')
            e = self.expr(); return Assign(name, e)
        if t == 'if':
            self.advance(); cond = self.expr(); self.expect(':')
            body = self.statement(); return If(cond, body)
        raise SyntaxError(f"Unexpected {t}")
    def expr(self):
        node = self.term()
        while self.peek()[0] in ('+', '-'):
            op = self.peek()[0]; self.advance()
            right = self.term(); node = BinOp(node, op, right)
        return node
    def term(self):
        node = self.factor()
        while self.peek()[0] in ('*', '/', '%'):
            op = self.peek()[0]; self.advance()
            right = self.factor(); node = BinOp(node, op, right)
        return node
    def factor(self):
        t, typ = self.peek()
        if typ == 'INTEGER': self.advance(); return Number(t)
        if typ == 'STRING': self.advance(); return String(t)
        if typ == 'IDENT':  self.advance(); return Var(t)
        if t == '(':
            self.advance(); node = self.expr(); self.expect(')'); return node
        raise SyntaxError(f"Unexpected factor {t}")

# C code generator
class CGen:
    def __init__(self): self.lines = []
    def gen(self, stmts):
        self.lines = ['#include <stdio.h>', '', 'int main() {']
        for s in stmts: self.emit(s)
        self.lines.append('    return 0;'); self.lines.append('}')
        return '\n'.join(self.lines)
    def emit(self, node):
        if isinstance(node, Assign):
            expr = self.e(node.expr)
            self.lines.append(f'    int {node.name} = {expr};')
        elif isinstance(node, Print):
            expr = self.e(node.expr)
            self.lines.append(f'    printf("%d\\n", {expr});')
        elif isinstance(node, If):
            cond = self.e(node.cond)
            self.lines.append(f'    if ({cond}) {{')
            self.emit(node.body)
            self.lines.append('    }')
    def e(self, node):
        if isinstance(node, Number): return str(node.value)
        if isinstance(node, Var): return node.name
        if isinstance(node, BinOp):
            return f'({self.e(node.left)} {node.op} {self.e(node.right)})'
        return '0'

# Simple Interpreter to execute AST
class Interpreter:
    def __init__(self): self.env = {}
    def eval(self, node):
        if isinstance(node, Number): return node.value
        if isinstance(node, Var): return self.env.get(node.name)
        if isinstance(node, BinOp):
            l, r = self.eval(node.left), self.eval(node.right)
            if node.op == '+': return l + r
            if node.op == '-': return l - r
            if node.op == '*': return l * r
            if node.op == '/': return l // r
            if node.op == '%': return l % r
        if isinstance(node, Assign): self.env[node.name] = self.eval(node.expr)
        if isinstance(node, Print): print(self.eval(node.expr))
        if isinstance(node, If) and self.eval(node.cond): self.eval(node.body)

# Runner
def run_py2c(source):
    toks, errs = [], []
    for i, ln in enumerate(source, 1):
        try: toks.extend(tokenise_python_code(ln))
        except Exception as e: errs.append(f'Line {i}: {e}')
    stmts = Parser(toks).parse()
    # Generate C and assembly
    c_code = CGen().gen(stmts)
    with open('output.c', 'w') as f: f.write(c_code)
    try:
        subprocess.run(['gcc', '-S', 'output.c', '-o', 'output.s'], check=True)
        print('Wrote output.c and output.s')
    except subprocess.CalledProcessError as e:
        print('GCC failed:', e)
    for err in errs: print(err)

    # Execute Python code and print its output
    print('\n-- Python execution output --')
    interp = Interpreter()
    for node in stmts:
        interp.eval(node)

if __name__ == '__main__':
    sample = [
        'x = 10',
        'y = 20',
        'print(x + y)',
        'if x: print("X")'
    ]
    run_py2c(sample)
