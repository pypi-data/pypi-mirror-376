class Interpreter:
    def __init__(self):
        self.variables = {}
        self.help_docs = {
            "pr": "pr(expr) - выводит значение выражения",
            "ind": "ind() - ввод с клавиатуры",
            "sr": "sr(expr) - преобразует expr в строку",
            "in": "in(expr) - преобразует expr в целое число",
            "len": "len(expr) - возвращает длину строки или массива",
            "square": "square(expr) - возводит expr в квадрат",
            "nosq": "nosq(expr) - expr / expr, проверка ненулевого значения",
            "help": "help([name]) - выводит справку по функциям",
        }

    def evaluate(self, node):
        if node is None:
            raise Exception("Unexpected None node")

        if node.type == "NUMBER":
            return node.value
        elif node.type == "ASSIGN":
            value = self.evaluate(node.right)
            self.variables[node.value] = value
            return value
        elif node.type == "ID":
            if node.value in self.variables:
                return self.variables[node.value]
            else:
                raise Exception(f"Undefined variable '{node.value}'")
        elif node.type == "PLUS":
            return self.evaluate(node.left) + self.evaluate(node.right)
        elif node.type == "MINUS":
            return self.evaluate(node.left) - self.evaluate(node.right)
        elif node.type == "MUL":
            return self.evaluate(node.left) * self.evaluate(node.right)
        elif node.type == "DIV":
            divisor = self.evaluate(node.right)
            if divisor == 0:
                raise Exception("Division by zero")
            return self.evaluate(node.left) / divisor
        elif node.type == "PR":
            value = self.evaluate(node.left[0]) if node.left else None
            print(value)
            return value
        elif node.type == "IND":
            return input()
        elif node.type == "SR":
            value = self.evaluate(node.left[0]) if node.left else None
            return str(value)
        elif node.type == "IN":
            value = self.evaluate(node.left[0]) if node.left else None
            return int(value)
        elif node.type == "LEN":
            value = self.evaluate(node.left[0]) if node.left else None
            return len(value)
        elif node.type == "STRING":
            return node.value
        elif node.type == "SQUARE":
            value = self.evaluate(node.left[0]) if node.left else None
            return value * value
        elif node.type == "SQ":
            value = self.evaluate(node.left[0]) if node.left else None
            if value == 0:
                raise Exception("Division by zero in nosq function")
            return value / value
        elif node.type == "HELP":
            if not node.left:
                print("Доступные функции и команды:")
                for k, v in self.help_docs.items():
                    print(f"- {k}: {v}")
            else:
                name = self.evaluate(node.left[0])
                doc = self.help_docs.get(name, f"Справка по функции '{name}' не найдена.")
                print(doc)
            return None
        elif node.type == "FUNC_CALL":
            func_name = node.value
            args = [self.evaluate(arg) for arg in (node.left or [])]
            if func_name == "help":
                if not args:
                    print("Доступные функции и команды:")
                    for k, v in self.help_docs.items():
                        print(f"- {k}: {v}")
                else:
                    name = args[0]
                    doc = self.help_docs.get(name, f"Справка по функции '{name}' не найдена.")
                    print(doc)
                return None
            else:
                raise Exception(f"Неизвестная функция '{func_name}'")
        else:
            raise Exception(f"Unknown node type '{node.type}'")











