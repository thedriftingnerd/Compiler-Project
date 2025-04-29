import re
import keyword
import subprocess

#Lexer definitions
KEYWORDS = set(keyword.kwlist)
OPERATORS = sorted([
    '**=', '//=', '==', '!=', '<=', '>=', '**', '//',
    '+=', '-=', '*=', '/=', '%=', '=', '<', '>', '+', '-', '*', '/', '%',
    'and', 'or', 'not', 'is', 'in'
],
key = lambda x: -len(x)) #sorts by length to match the longest operator first

#Tokenizer
def tokenise_python_code(line): #converts a line of python source code into a list 
    line = re.sub(r'#.*', '', line) #removes python comments
    token_spec = [ #defines token patterns
        ('STRING',   r'(".*?"|\'.*?\')'), #double or single quoted strings
        ('FLOAT',    r'[+-]?(\d+\.\d*|\.\d+)'), #floating point literals
        ('INTEGER',  r'[+-]?\d+'), #integer literals
        ('IDENT',    r'[A-Za-z_][A-Za-z0-9_]*'), #identifiers
        ('OP',       '|'.join(map(re.escape, OPERATORS))), #operators
        ('SKIP',     r'\s+'), #whitetspace
        ('MISMATCH', r'.'), #other single characters
    ]
    #compiles combined regex with named groups
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_spec)
    tokens = []
    for mo in re.finditer(tok_regex, line): #iterates over all the matches in a line
        kind, val = mo.lastgroup, mo.group()
        if(kind == 'SKIP'): continue #ignores whitespace
        if(kind == 'IDENT'):
            if(val in KEYWORDS): kind = 'KEYWORD' #reclassify identifiers as KEYWORD or OP if they match
            elif(val in OPERATORS): kind = 'OP'
        tokens.append((val, kind))
    return tokens

# AST nodes
class Node: pass
class Number(Node): #integer literal
    def __init__(self, v): self.value = int(v)
class String(Node): #string literal
    def __init__(self, v): self.value = v[1:-1]
class Var(Node): #variable reference
    def __init__(self, n): self.name = n
class BinOp(Node): #bianry operation
    def __init__(self, l, o, r): self.left, self.op, self.right = l, o, r
class Assign(Node): #variable assignment
    def __init__(self, n, e): self.name, self.expr = n, e
class Print(Node): #print statements
    def __init__(self, e): self.expr = e
class If(Node): #single statement if statement
    def __init__(self, c, b): self.cond, self.body = c, b

#Recursive Descent Parser
class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.pos = 0
    def peek(self): #returns the current token or none at the end of stream
        return self.toks[self.pos] if self.pos < len(self.toks) else (None, None)
    def advance(self): #takes current token
        self.pos += 1
    def expect(self, val): #checks that the current token matches val and then takes it
        t,_ = self.peek()
        if(t != val): raise SyntaxError(f"Expected {val}, got {t}")
        self.advance()
    def parse(self): #parses statements until tokens are exhausted
        statements=[]
        while(self.pos < len(self.toks)): statements.append(self.statement())
        return statements

    def statement(self): #parses a single statment such as print, assign, or if
        t, typ = self.peek()
        if(t == 'print'):
            self.advance()
            self.expect('(')
            e = self.expr()
            self.expect(')')
            return Print(e)
        if(typ == 'IDENT'):
            name = t
            self.advance()
            self.expect('=')
            e = self.expr()
            return Assign(name, e)
        if(t == 'if'):
            self.advance()
            cond = self.expr()
            self.expect(':')
            body = self.statement()
            return If(cond, body)
        raise SyntaxError(f"Unexpected {t}")

    def expr(self): #expression handling + and -
        node = self.term()
        while(self.peek()[0] in ('+', '-')):
            op = self.peek()[0]
            self.advance()
            right = self.term()
            node = BinOp(node, op, right)
        return node

    def term(self): #parses term handling *,/,%
        node = self.factor()
        while(self.peek()[0] in ('*', '/', '%')):
            op = self.peek()[0]
            self.advance()
            right = self.factor()
            node = BinOp(node, op, right)
        return node

    def factor(self): #parses integer, string, var, or parenthesised expression
        t, typ = self.peek()
        if(typ == 'INTEGER'):
            self.advance()
            return Number(t)
        if(typ == 'STRING'):
            self.advance()
            return String(t)
        if(typ == 'IDENT'):
            self.advance()
            return Var(t)
        if(t == '('):
            self.advance()
            node = self.expr()
            self.expect(')')
            return node
        raise SyntaxError(f"Unexpected factor {t}")

#C code generator
class CGen: #converts sample Python code to C
    def __init__(self): self.lines = []
    def gen(self, statements): #emits a C program from the abstract syntax tree
        self.lines = ['#include <stdio.h>', '', 'int main() {']
        for s in statements: self.emit(s)
        self.lines.append('    return 0;')
        self.lines.append('}')
        return '\n'.join(self.lines)

    def emit(self, node): #appends C code lines for a single AST node
        if(isinstance(node, Assign)):
            expr = self.e(node.expr)
            self.lines.append(f'    int {node.name} = {expr};')
        elif(isinstance(node, Print)):
            expr = self.e(node.expr)
            self.lines.append(f'    printf("%d\\n", {expr});')
        elif(isinstance(node, If)):
            cond = self.e(node.cond)
            self.lines.append(f'    if ({cond}) {{')
            self.emit(node.body)
            self.lines.append('    }')

    def e(self, node): #recursively generates C expressions from AST nodes
        if(isinstance(node, Number)): return str(node.value)
        if(isinstance(node, Var)): return node.name
        if(isinstance(node, BinOp)):
            left = self.e(node.left)
            right = self.e(node.right)
            return f'({left} {node.op} {right})'
        return '0'
    
class Interpreter: #interpreter that executes the AST
    def __init__(self): self.env = {}
    def eval(self, node):
        if isinstance(node, Number): return node.value #integer literal
        if isinstance(node, Var): return self.env.get(node.name) #variable lookup
        if isinstance(node, BinOp): #binary operations
            l, r = self.eval(node.left), self.eval(node.right)
            if node.op == '+': return l + r
            if node.op == '-': return l - r
            if node.op == '*': return l * r
            if node.op == '/': return l // r
            if node.op == '%': return l % r
        if isinstance(node, Assign): self.env[node.name] = self.eval(node.expr) #looks at right side for variable assignment
        if isinstance(node, Print): print(self.eval(node.expr)) #prints outputs to console
        if isinstance(node, If) and self.eval(node.cond): self.eval(node.body) #if condition stuff

#Runner
def run_py2c(source): #tokenise, parse, generate C, and then invoke GCC to produce the assembly
    toks, errs = [], []
    for i, ln in enumerate(source, 1): #lex each line and then collect tokens and errors
        try: toks.extend(tokenise_python_code(ln))
        except Exception as e: errs.append(f'Line {i}: {e}')
    statements = Parser(toks).parse() #build AST and generate C source
    c_code = CGen().gen(statements)
    with(open('output.c', 'w') as f): f.write(c_code)
    try: #invoke GCC to compile assembly
        subprocess.run(['gcc', '-S', 'output.c', '-o', 'output.s'], check=True)
        print('Wrote output.c and output.s')
    except subprocess.CalledProcessError as e: print('GCC failed:', e)

if __name__ == '__main__':
    sample = [
        'x = 10',
        'y = 20',
        'print(x + y)',
        'if x: print("X")'
    ]
    run_py2c(sample)
