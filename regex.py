import re

# Token class to represent each token in the regex
class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

# Tokenizer class to break the regex string into tokens
class Tokenizer:
    def __init__(self, regex):
        self.regex = regex
        self.pos = 0

    # Get the next token from the regex string
    def get_next_token(self):
        if self.pos >= len(self.regex):
            return None

        current_char = self.regex[self.pos]

        if current_char.isalnum() or current_char in {'@', '-', '_', '%', '+', '.'}:
            token = Token('CHAR', current_char)
        elif current_char == '\\':
            self.pos += 1
            if self.pos < len(self.regex):
                next_char = self.regex[self.pos]
                token = Token('ESCAPED_CHAR', next_char)
            else:
                raise ValueError("Backslash at end of regex")
        elif current_char == '*':
            token = Token('STAR', current_char)
        elif current_char == '|':
            token = Token('ALT', current_char)
        elif current_char == '.':
            token = Token('DOT', current_char)
        elif current_char == '^':
            token = Token('START', current_char)
        elif current_char == '$':
            token = Token('END', current_char)
        elif current_char == '[':
            self.pos += 1
            char_class = ''
            while self.pos < len(self.regex) and self.regex[self.pos] != ']':
                char_class += self.regex[self.pos]
                self.pos += 1
            if self.pos >= len(self.regex) or self.regex[self.pos] != ']':
                raise ValueError("Unclosed character class")
            token = Token('CLASS', char_class)
        elif current_char == '{':
            quantifier = '{'
            self.pos += 1
            while self.pos < len(self.regex) and self.regex[self.pos] != '}':
                quantifier += self.regex[self.pos]
                self.pos += 1
            if self.pos >= len(self.regex) or self.regex[self.pos] != '}':
                raise ValueError("Unclosed quantifier")
            quantifier += '}'
            token = Token('QUANT', quantifier)
        elif current_char == '(':
            token = Token('LPAREN', current_char)
        elif current_char == ')':
            token = Token('RPAREN', current_char)
        else:
            raise ValueError(f"Unknown character: {current_char}")

        self.pos += 1
        return token

    # Tokenize the entire regex string into a list of tokens
    def tokenize(self):
        tokens = []
        while self.pos < len(self.regex):
            token = self.get_next_token()
            if token:
                tokens.append(token)
        return tokens

# Parser class to convert tokens into a syntax tree
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos] if self.tokens else None

    # Parse the entire token list into a syntax tree
    def parse(self):
        return self.regex()

    # Parse a regex expression
    def regex(self):
        term = self.term()
        while self.current_token is not None and self.current_token.type == 'ALT':
            self.advance()
            term = Node('ALT', term, self.term())
        return term

    # Parse a term (sequence of factors)
    def term(self):
        factor = self.factor()
        while self.current_token is not None and self.current_token.type in {'CHAR', 'CLASS', 'DOT', 'START', 'END', 'ESCAPED_CHAR', 'LPAREN'}:
            factor = Node('CONCAT', factor, self.factor())
        return factor

    # Parse a factor (atom followed by zero or more * or quantifiers)
    def factor(self):
        atom = self.atom()
        while self.current_token is not None and self.current_token.type in {'STAR', 'QUANT'}:
            if self.current_token.type == 'STAR':
                self.advance()
                atom = Node('STAR', atom)
            elif self.current_token.type == 'QUANT':
                quant = self.current_token
                self.advance()
                atom = Node('QUANT', atom, quant)
        return atom

    # Parse an atom (CHAR, CLASS, DOT, START, END, ESCAPED_CHAR, sub-regex)
    def atom(self):
        if self.current_token.type in {'CHAR', 'CLASS', 'DOT', 'START', 'END', 'ESCAPED_CHAR'}:
            node = self.current_token
            self.advance()
            return node
        elif self.current_token.type == 'LPAREN':
            self.advance()
            node = self.regex()
            if self.current_token is None or self.current_token.type != 'RPAREN':
                raise ValueError("Unclosed parenthesis")
            self.advance()
            return Node('GROUP', node)
        raise ValueError(f"Unexpected token: {self.current_token}")

    # Move to the next token
    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

# Node class to represent each node in the syntax tree
class Node:
    def __init__(self, type, left=None, right=None):
        self.type = type
        self.left = left
        self.right = right

    def __repr__(self):
        return f"Node({self.type}, {repr(self.left)}, {repr(self.right)})"

# Compile the syntax tree into a regex string
def compile(tree):
    if tree.type == 'CHAR':
        return tree.value
    elif tree.type == 'STAR':
        return f"({compile(tree.left)})*"
    elif tree.type == 'CONCAT':
        return f"{compile(tree.left)}{compile(tree.right)}"
    elif tree.type == 'ALT':
        return f"({compile(tree.left)}|{compile(tree.right)})"
    elif tree.type == 'CLASS':
        return f"[{tree.value}]"
    elif tree.type == 'DOT':
        return '.'
    elif tree.type == 'START':
        return '^'
    elif tree.type == 'END':
        return '$'
    elif tree.type == 'ESCAPED_CHAR':
        return f"\\{tree.value}"
    elif tree.type == 'QUANT':
        return f"{compile(tree.left)}{tree.right.value}"
    elif tree.type == 'GROUP':
        return f"({compile(tree.left)})"
    else:
        raise ValueError(f"Unknown node type: {tree.type}")

# Match the compiled regex against input text
def match(regex, text):
    compiled = re.compile(regex)
    return compiled.match(text)

# Get user input for the regex string and the input text
user_regex = input("Enter the regex string: ")
user_text = input("Enter the input text to match: ")

# Tokenize the user-provided regex
tokenizer = Tokenizer(user_regex)
tokens = tokenizer.tokenize()
print(f"Tokens: {tokens}")

# Parse the tokens into a syntax tree
parser = Parser(tokens)
tree = parser.parse()
compiled_regex = compile(tree)
print(f"Compiled regex: {compiled_regex}")

# Match the compiled regex against the user-provided input text
match_result = match(compiled_regex, user_text)
if match_result:
    print(f"Match found: {match_result.group()}")
    print(f"Span of match: {match_result.span()}")
else:
    print("No match found.")
