import sys
from .lexer import tokenize
from .parser import Parser
from .interpreter import evaluate

def run_code(code):
    tokens = tokenize(code)
    parser = Parser(tokens)
    ast = parser.parse()
    return evaluate(ast)

if __name__ == "__main__":
    input_code = sys.stdin.read()  
    run_code(input_code)














