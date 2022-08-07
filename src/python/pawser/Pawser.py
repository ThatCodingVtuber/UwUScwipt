

from enum import Enum
from typing import Any, List, Union
from pawser.Tokenizer import Tokenizer, Token, TokenType, SwyntaxError

class UnexpectedToken(SwyntaxError):
    def __init__(self, line: int, expected: str, token: Token) -> None:
        super().__init__(line, f"Expwected {expected}, got {token}")
        self.got = token

class NodeType(Enum):
    FILE = 0
    SET = 1
    CAWL = 2
    GIVE = 3
    REPEAT = 4
    MWETHOD = 5
    NEW = 6
    EXTENDS = 7
    IDENTIFIER = 8
    IDENTIFIER_EXPR = 9
    EXPWESSION = 11
    ARGLIST = 12
    EXPWESSIONLIST = 13
    FCALL = 14
    FDEF = 15
    BWEAK = 16
    CLASSDEF = 17

    IFFU = 30
    COND = 31

    WOAD = 50

    CONST_NUMBWER = 100
    CONST_STWING = 101
    CONST_BWOOLEAN = 102
    CONST_NWULL = 103

class Node:
    def __init__(self, node: NodeType, data=None) -> None:
        self.type = node
        self.data = data
        self.children: List[Node] = []
        self.line = None
    def __repr__(self, tabs="") -> str:
        if self.data is not None:
            this_node = f"{self.type.name}: <{type(self.data).__name__}> {self.data}"
        else:
            this_node = f"{self.type.name}"
        return '\n'.join([ this_node ] + [ tabs + ('├─' if i < len(self.children) - 1 else '└─') + c.__repr__(tabs + ('│ ' if i < len(self.children) - 1 else '  ')) for i,c in enumerate(self.children) ])

class Tree:
    def __init__(self, tokenizer: Tokenizer) -> None:
        self.base = Node(NodeType.FILE)
        self.stack = []
        self.current = self.base
        self.t = tokenizer
    def push(self, node: Node) -> None:
        node.line = self.t.getCurrentLine()
        self.stack.append(self.current)
        self.current.children.append(node)
        self.current = node
    def shift(self, node: Node) -> None:
        node.line = self.t.getCurrentLine()
        self.current.children.append(node)
    def pop(self) -> Node:
        self.current = self.stack.pop()
        return self.current
    def __repr__(self) -> str:
        return self.base.__repr__()

class Pawser:
    def __init__(self, tokenizer: Tokenizer) -> None:
        self.tokens = tokenizer
        self.token = self.tokens.getToken()
        
        self.tree = Tree(tokenizer)

    def GT(self) -> None:
        self.token = self.tokens.getToken()

    def assertIdent(self) -> None:
        if not self.token.isType(TokenType.IDENTIFIER):
            raise UnexpectedToken(self.tokens.getCurrentLine(), "IDENTIFIER", self.token)

    def assertKeyword(self, kw: str) -> None:
        return self.assertKeywords([kw])

    def assertKeywords(self, kw: List[str]) -> None:
        if not self.token.isType(TokenType.KEYWORD) or self.token.data not in kw:
            raise UnexpectedToken(self.tokens.getCurrentLine(), ', '.join(kw), self.token) 

    def parse_START(self) -> None:
        self.parse_STATEMENT_GROUP(TokenType.EOF)

    def parse_STATEMENT_GROUP(self, endToken: TokenType, data: Union[str, List[str]] = None, isClass: bool = False, isExtendable: bool = False) -> None:
        foundNew = False
        while not (self.token.isType(endToken) and ((self.token.data in data if type(data) == list else self.token.data == data) or data is None)):
            if not self.token.isType(TokenType.STATEMENT_STARTER):
                raise UnexpectedToken(self.tokens.getCurrentLine(), "STAWT_STATEMENT", self.token)
            
            if self.token.data == "pwease":
                self.GT()
                if self.token.isType(TokenType.KEYWORD) and self.token.data == 'new':
                    if foundNew:
                        raise SwyntaxError(self.tokens.getCurrentLine(), "Cwassu can onwy have one new statement")
                    else:
                        foundNew = True
                self.parse_PWEASE(isClass, isExtendable)
            elif self.token.data == "iffu" and not isClass:
                self.parse_IFFU()
            else:
                raise UnexpectedToken(self.tokens.getCurrentLine(), "pwease" if isClass else "pwease or iffu", self.token)

    def parse_IDENTIFIER_EXPR(self) -> None:
        self.tree.push(Node(NodeType.IDENTIFIER_EXPR))
        
        self.assertIdent()
        self.tree.shift(Node(NodeType.IDENTIFIER, self.token.data))
        self.GT()

        while self.token.isType(TokenType.POSSESIVE):
            self.GT()
            self.assertIdent()
            self.tree.shift(Node(NodeType.IDENTIFIER, self.token.data))
            self.GT()
        self.tree.pop()

    def parse_ARGLIST(self) -> None:
        if self.token.isType(TokenType.STATEMENT_STARTER):
            self.tree.shift(Node(NodeType.ARGLIST))
            return

        self.tree.push(Node(NodeType.ARGLIST))
        self.assertIdent()
        self.tree.shift(Node(NodeType.IDENTIFIER, self.token.data))
        self.GT()
        if self.token.isType(TokenType.COMMA):
            self.GT()
            while self.token.isType(TokenType.COMMA):
                self.GT()
                if self.token.isType(TokenType.IDENTIFIER):
                    self.tree.shift(Node(NodeType.IDENTIFIER, self.token.data))
                    self.GT()
                elif self.token.isType(TokenType.KEYWORD) and self.token.data == "and":
                    break
                else:
                    raise UnexpectedToken(self.tokens.getCurrentLine(), "and or IDENTIFIER", self.token)
            if self.token.isType(TokenType.KEYWORD) and self.token.data == "and":
                self.GT()
                self.assertIdent()
                self.tree.shift(Node(NodeType.IDENTIFIER, self.token.data))
                self.GT()
            else:
                raise UnexpectedToken(self.tokens.getCurrentLine(), "and", self.token)
        elif self.token.isType(TokenType.KEYWORD) and self.token.data == "and":
            self.GT()
            self.assertIdent()
            self.tree.shift(Node(NodeType.IDENTIFIER, self.token.data))
            self.GT()
        
        self.tree.pop()

    def parse_EXPRESSION(self) -> None:
        self.tree.push(Node(NodeType.EXPWESSION))
        if self.token.isType(TokenType.IDENTIFIER):
            self.parse_IDENTIFIER_EXPR()
            # Check if this is a function call
            if self.token.isType(TokenType.KEYWORD) and self.token.data in [ 'uv', 'wif', 'OwO' ]:
                self.tree.push(Node(NodeType.FCALL))
                self.parse_EXPRESSION_LIST()
                self.tree.pop()
        elif self.token.isType(TokenType.NUMBWER):
            self.tree.shift(Node(NodeType.CONST_NUMBWER, float(self.token.data)))
            self.GT()
        elif self.token.isType(TokenType.STWING):
            self.tree.shift(Node(NodeType.CONST_STWING, self.token.data))
            self.GT()
        elif self.token.isType(TokenType.BWOOLEAN):
            self.tree.shift(Node(NodeType.CONST_BWOOLEAN, self.token.data == "twue"))
            self.GT()
        elif self.token.isType(TokenType.NWULL):
            self.tree.shift(Node(NodeType.CONST_NWULL))
            self.GT()
        elif self.token.isType(TokenType.KEYWORD) and self.token.data in [ "fwunction" ]:
            self.GT()
            self.parse_FWUNCTION()
        elif self.token.isType(TokenType.KEYWORD) and self.token.data in [ "cwassu" ]:
            self.GT()
            self.parse_CWASSU()
        else:
            raise UnexpectedToken(self.tokens.getCurrentLine(), "CONST_EXPR", self.token)
        self.tree.pop()

    def parse_PWEASE(self, isClass: bool = False, isExtendable: bool = False) -> None:
        if not self.token.isType(TokenType.PWEASE_DIWECTIVE):
            raise UnexpectedToken(self.tokens.getCurrentLine(), "pwease diwective", self.token)

        if self.token.data == "set":
            self.tree.push(Node(NodeType.SET))
            self.GT()
            self.parse_IDENTIFIER_EXPR()
            if not self.token.isType(TokenType.KEYWORD) or self.token.data != "twoo":
                raise UnexpectedToken(self.tokens.getCurrentLine(), "twoo",self.token)
            self.GT()
            self.parse_EXPRESSION()
            self.tree.pop()
        elif self.token.data == "cawl":
            self.tree.push(Node(NodeType.CAWL))
            self.GT()
            self.parse_IDENTIFIER_EXPR()
            self.assertKeywords([ "wif", "uv", "OwO" ])
            self.parse_EXPRESSION_LIST()
            self.tree.pop()
        elif self.token.data == "give":
            self.tree.push(Node(NodeType.GIVE))
            self.GT()
            self.parse_EXPRESSION()
            self.tree.pop()
        elif self.token.data == "repeat":
            self.tree.push(Node(NodeType.REPEAT))
            self.GT()
            self.parse_STATEMENT_GROUP(TokenType.KEYWORD, "onegaishimasu")
            self.GT()
            self.tree.pop()
        elif self.token.data == "bweak":
            # Count the bweaks
            bLevel = 1
            self.GT()
            while self.token.isType(TokenType.PWEASE_DIWECTIVE) and self.token.data == 'bweak':
                bLevel += 1
                self.GT()
            self.tree.shift(Node(NodeType.BWEAK, bLevel))
        elif self.token.data == "mwethod" and isClass:
            self.tree.push(Node(NodeType.MWETHOD))
            self.GT()
            self.assertIdent()
            self.tree.shift(Node(NodeType.IDENTIFIER, self.token.data))
            self.GT()
            if self.token.isType(TokenType.KEYWORD) and self.token.data in [ 'wif', 'uv' ]:
                self.GT()
            self.parse_ARGLIST()
            self.tree.push(Node(NodeType.FDEF))
            self.parse_STATEMENT_GROUP(TokenType.KEYWORD, "onegaishimasu")
            self.tree.pop()
            self.GT()
            self.tree.pop()
        elif self.token.data == "new" and isClass:
            self.tree.push(Node(NodeType.NEW))
            self.GT()
            self.parse_ARGLIST()
            self.tree.push(Node(NodeType.FDEF))
            self.parse_STATEMENT_GROUP(TokenType.KEYWORD, "onegaishimasu", isExtendable=True)
            self.tree.pop()
            self.GT()
            self.tree.pop()
        elif self.token.data == "extend" and isExtendable:
            self.tree.push(Node(NodeType.EXTENDS))
            self.GT()
            self.parse_IDENTIFIER_EXPR()
            self.parse_EXPRESSION_LIST()
            self.tree.pop()
        elif self.token.data == "woad":
            self.tree.push(Node(NodeType.WOAD))
            self.GT()
            self.parse_EXPRESSION()
            self.assertKeyword("twoo")
            self.GT()
            self.parse_IDENTIFIER_EXPR()
            self.tree.pop()
        else:
            raise SwyntaxError(self.tokens.getCurrentLine(), f"Unexpwected pwease diwective {self.token.data}")

    def parse_FWUNCTION(self) -> None:
        self.parse_ARGLIST()
        self.tree.push(Node(NodeType.FDEF))
        self.parse_STATEMENT_GROUP(TokenType.KEYWORD, "onegaishimasu")
        self.GT()
        self.tree.pop()
    
    def parse_CWASSU(self) -> None:
        self.tree.push(Node(NodeType.CLASSDEF))
        self.parse_STATEMENT_GROUP(TokenType.KEYWORD, "onegaishimasu", isClass = True)
        self.GT()
        self.tree.pop()

    def parse_EXPRESSION_LIST(self) -> None:
        if self.token.isType(TokenType.KEYWORD) and self.token.data == "OwO":
            self.tree.shift(Node(NodeType.EXPWESSIONLIST))
            self.GT()
            return

        self.assertKeywords([ 'wif', 'uv' ])
        self.GT()
        self.tree.push(Node(NodeType.EXPWESSIONLIST))
        self.parse_EXPRESSION()

        if self.token.isType(TokenType.COMMA):
            while self.token.isType(TokenType.COMMA):
                self.GT()
                if self.token.isType(TokenType.KEYWORD) and self.token.data == "and":
                    break
                else:
                    self.parse_EXPRESSION()
            self.assertKeyword("and")
            self.GT()
            self.parse_EXPRESSION()
            
        elif self.token.isType(TokenType.KEYWORD) and self.token.data == "and":
            self.GT()
            self.parse_EXPRESSION()

        elif self.token.isType(TokenType.KEYWORD) and self.token.data == "UwU":
            self.GT()

        else:
            raise UnexpectedToken(self.tokens.getCurrentLine(), "COMMA, and, UwU", self.token) 

        self.tree.pop()

    def parse_IFFU(self) -> None:
        # Token is an IFFU
        self.tree.push(Node(NodeType.IFFU))
        self.GT()
        self.tree.push(Node(NodeType.COND))
        self.parse_EXPRESSION()
        self.tree.push(Node(NodeType.FDEF))
        self.parse_STATEMENT_GROUP(TokenType.KEYWORD, [ "onegaishimasu", "ewif", "ewse" ])
        self.tree.pop()
        self.tree.pop()
        while self.token.isType(TokenType.KEYWORD) and self.token.data == "ewif":
            self.GT()
            self.tree.push(Node(NodeType.COND))
            self.parse_EXPRESSION()
            self.tree.push(Node(NodeType.FDEF))
            self.parse_STATEMENT_GROUP(TokenType.KEYWORD, [ "onegaishimasu", "ewif", "ewse" ])
            self.tree.pop()
            self.tree.pop()
        if self.token.isType(TokenType.KEYWORD) and self.token.data == "ewse":
            self.GT()
            self.tree.push(Node(NodeType.FDEF))
            self.parse_STATEMENT_GROUP(TokenType.KEYWORD, "onegaishimasu")
            self.tree.pop()
        self.assertKeyword("onegaishimasu")
        self.GT()
        self.tree.pop()

        
        

