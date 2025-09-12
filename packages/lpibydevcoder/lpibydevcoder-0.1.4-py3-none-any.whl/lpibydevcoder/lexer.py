import re

token_specs = [
    ("NUMBER", r"^\d+"),
    ("PR", r"^pr\b"),
    ("IND", r"^ind\b"),
    ("ST", r"^st\b"),
    ("IN", r"^in\b"),
    ("LEN", r"^len\b"),
    ("SR", r"^sr\b"),
    ("SQUARE", r"^square\b"),
    ("SQ", r"^nosq\b"),
    ("DEF", r"^def\b"),
    ("HELP", r"^help\b"),
    ("BIT", r"^bit\b"),
    ("ID", r"^[a-zA-Z_][a-zA-Z0-9_]*"),
    ("PLUS", r"^\+"),
    ("MINUS", r"^-"),
    ("MUL", r"^\*"),
    ("DIV", r"^/"),
    ("LPAREN", r"^\("),
    ("RPAREN", r"^\)"),
    ("STRING", r'^"[^"]*"'),
    ("COMMA", r"^,"),
    ("RAV", r"^="),
    ("WHITESPACE", r"^\s+"),  
]

def tokenize(code):
    tokens = []
    while code:
        for name, pattern in token_specs:
            match = re.match(pattern, code)
            if match:
                value = match.group(0)
                if name != "WHITESPACE":
                    tokens.append((name, value))
                code = code[len(value):]
                break
        else:
            raise SyntaxError(f"Unknown symbol: {code[0]}")
    return tokens


