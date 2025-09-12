class Node:
    def __init__(self, type_, value=None, left=None, right=None):
        self.type = type_
        self.value = value
        self.left = left
        self.right = right


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def eat(self, token_type):
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == token_type:
            self.pos += 1
        else:
            raise SyntaxError(f"Expected token {token_type} but got {self.tokens[self.pos][0]}")

    def factor(self):
        if self.pos >= len(self.tokens):
            raise SyntaxError("Unexpected end of input")

        token = self.tokens[self.pos]

        if token[0] == "NUMBER":
            self.eat("NUMBER")
            return Node("NUMBER", int(token[1]))

        elif token[0] in ("PR", "IND", "SR", "IN", "LEN", "SQUARE", "SQ", "HELP", "BIT"):
            func_type = token[0]
            self.eat(func_type)
            self.eat("LPAREN")

            args = []
            if func_type not in ("IND",):
                if self.tokens[self.pos][0] != "RPAREN":
                    args.append(self.expr())
                    while self.pos < len(self.tokens) and self.tokens[self.pos][0] == "COMMA":
                        self.eat("COMMA")
                        args.append(self.expr())

            self.eat("RPAREN")

            return Node(func_type, left=args)

        elif token[0] == "STRING":
            self.eat("STRING")
            return Node("STRING", token[1][1:-1])

        elif token[0] == "LPAREN":
            self.eat("LPAREN")
            node = self.expr()
            self.eat("RPAREN")
            return node

        elif token[0] == "ID":
            self.eat("ID")
            if self.pos < len(self.tokens) and self.tokens[self.pos][0] == "LPAREN":
                self.eat("LPAREN")
                args = []
                if self.tokens[self.pos][0] != "RPAREN":
                    args.append(self.expr())
                    while self.pos < len(self.tokens) and self.tokens[self.pos][0] == "COMMA":
                        self.eat("COMMA")
                        args.append(self.expr())
                self.eat("RPAREN")
                return Node("FUNC_CALL", token[1], args)
            else:
                return Node("ID", token[1])

        else:
            raise SyntaxError(f"Unexpected token {token[0]}")

    def term(self):
        node = self.factor()
        while self.pos < len(self.tokens) and self.tokens[self.pos][0] in ("MUL", "DIV"):
            token = self.tokens[self.pos]
            if token[0] == "MUL":
                self.eat("MUL")
                node = Node("MUL", left=node, right=self.factor())
            elif token[0] == "DIV":
                self.eat("DIV")
                node = Node("DIV", left=node, right=self.factor())
        return node

    def expr(self):
        node = self.term()
        while self.pos < len(self.tokens) and self.tokens[self.pos][0] in ("PLUS", "MINUS"):
            token = self.tokens[self.pos]
            if token[0] == "PLUS":
                self.eat("PLUS")
                node = Node("PLUS", left=node, right=self.term())
            elif token[0] == "MINUS":
                self.eat("MINUS")
                node = Node("MINUS", left=node, right=self.term())
        return node

    def assignment(self):
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == "ID":
            var_name = self.tokens[self.pos][1]
            self.eat("ID")
            if self.pos < len(self.tokens) and self.tokens[self.pos][0] == "RAV":
                self.eat("RAV")
                expr_node = self.expr()
                return Node("ASSIGN", var_name, expr_node)
            else:
                return Node("ID", var_name)
        else:
            return self.expr()

    def parse(self):
        return self.assignment()





