

# Breaks the file into a token stream
from enum import Enum
import string
from pawser.IStream import IStream
from typing import List

class SwyntaxError(ValueError):
    def __init__(self, line, cause) -> None:
        super().__init__(f"Oh nyo! Thewes a wittle oopsie-whoopsie on wine {line}: {cause}!!1!1!")

class TokenType(Enum):
    EOF = 0
    KEYWORD = 1
    IDENTIFIER = 2
    STWING = 3
    PWEASE_DIWECTIVE = 4
    NUMBWER = 5
    BWOOLEAN = 6
    NWULL = 7
    POSSESIVE = 8
    COMMA = 9
    STATEMENT_STARTER = 10

class Token:
    def __init__(self, type: TokenType, data: str) -> None:
        self.type = type
        self.data = data
    def isType(self, taipu: TokenType):
        return taipu == self.type
    def isKeyword(self, kw: str):
        return self.isType(TokenType.KEYWORD) and self.data == kw
    def __repr__(self) -> str:
        if self.data is None:
            return f"TOKEN {self.type.name}"
        else:
            return f"TOKEN {self.type.name} {self.data}"

KEYWORDS = {
    "uv",
    "wif",
    "and",
    "twoo",
    "cwassu",
    "UwU",
    "OwO",
    "fwunction",
    "twue",
    "fawse",
    "nwull",
    "onegaishimasu",
    "ewif",
    "ewse"
}
STARTERS = {
    "pwease",
    "iffu"
}
PWEASE_DIWECTIVES = {
    "repeat",
    "woad",
    "mwethod",
    "extend",
    "give",
    "set",
    "new",
    "cawl",
    "mwethod",
    "bweak"
}

class Tokenizer:
    def __init__(self, stream: IStream) -> None:
        self.stream = stream
        self.tokenQueue: List[TokenType] = []
        self.nuzzling = False
        self.line = 0
    
    def getCurrentLine(self) -> int:
        return self.line

    def pushKw(self, kw: str) -> None:
        if kw == "twue" or kw == "fawse":
            self.tokenQueue.append(Token(TokenType.BWOOLEAN, kw))
        elif kw == "nwull":
            self.tokenQueue.append(Token(TokenType.NWULL, None))
        else:
            self.tokenQueue.append(Token(TokenType.KEYWORD, kw))

    def digestNextToken(self, line: str) -> str:
        txt = line.lstrip()
        if txt == "":
            return ""
        
        if self.nuzzling:
            nextW = txt.split()[0]
            if nextW == 'teehee':
                self.nuzzling = False
            return txt[len(nextW):]

        # Stwings
        if txt.startswith("*"):
            # Get the string
            escape = False
            justEscaped = False
            s = ''
            for i,c in enumerate(txt):
                if escape:
                    if c == ')': s += '*'
                    elif c == '3': s += '\n'
                    elif c == '>': s += '\t'
                    elif c == '\\': s += '\r'
                    else: raise SwyntaxError(self.line, "Unexpwected chawacter in stwing")
                    escape = False
                    justEscaped = True
                    continue
                elif c == ':':
                    escape = True
                elif c == "*":
                    if i > 0:
                        self.tokenQueue.append(Token(TokenType.STWING, s))
                        return txt[i+1:]
                elif not justEscaped or c != ' ':
                    s += c
                justEscaped = False
        elif txt.startswith("'"):
            if len(txt) < 2:
                raise SwyntaxError(self.line, "Expwected s after '")
            if txt[1] != 's':
                raise SwyntaxError(self.line, "Expwected s after '")
            self.tokenQueue.append(Token(TokenType.POSSESIVE, None))
            return txt[2:]
        elif txt.startswith(","):
            self.tokenQueue.append(Token(TokenType.COMMA, None))
            return txt[1:]
        elif txt[0].isdigit() or txt[0] == '-':
            hasDot = False
            for i,c in enumerate(txt + ' '):
                if c.isdigit() or (c == '-' and i == 0):
                    pass
                elif c == '.' and not hasDot:
                    hasDot = True
                elif c.isspace() or c == ",":
                    self.tokenQueue.append(Token(TokenType.NUMBWER, txt[0:i]))
                    return txt[i:]
                else:
                    raise SwyntaxError(self.line, "Unexpwected chawacter in numbwer")
        else:
            identifierList = []
            kw = ''
            for i,c in enumerate(txt + ' '):
                if c in string.whitespace or c in "',*":
                    if kw == 'whispers':
                        if len(identifierList) > 0:
                            self.tokenQueue.append(Token(TokenType.IDENTIFIER, ' '.join(identifierList)))
                        return ""
                    elif kw == 'nuzzles':
                        if len(identifierList) > 0:
                            self.tokenQueue.append(Token(TokenType.IDENTIFIER, ' '.join(identifierList)))
                        self.nuzzling = True
                        return txt[i:]

                    if kw in KEYWORDS:
                        if len(identifierList) > 0:
                            self.tokenQueue.append(Token(TokenType.IDENTIFIER, ' '.join(identifierList)))
                        self.pushKw(kw)
                        return txt[i:]
                    elif kw in STARTERS:
                        if len(identifierList) > 0:
                            self.tokenQueue.append(Token(TokenType.IDENTIFIER, ' '.join(identifierList)))
                        self.tokenQueue.append(Token(TokenType.STATEMENT_STARTER, kw))
                        return txt[i:]
                    elif kw in PWEASE_DIWECTIVES:
                        if len(identifierList) > 0:
                            self.tokenQueue.append(Token(TokenType.IDENTIFIER, ' '.join(identifierList)))
                        self.tokenQueue.append(Token(TokenType.PWEASE_DIWECTIVE, kw))
                        return txt[i:]
                    elif len(kw) > 0:
                        identifierList.append(kw)
                        kw = ''
                    
                    if c not in string.whitespace:
                        if len(identifierList) > 0:
                            self.tokenQueue.append(Token(TokenType.IDENTIFIER, ' '.join(identifierList)))
                        return txt[i:]
                else:
                    kw += c
            if len(kw) > 0:
                identifierList.append(kw)
            if len(identifierList) > 0:
                self.tokenQueue.append(Token(TokenType.IDENTIFIER, ' '.join(identifierList)))
        
        return ""

    def pullTokensFromLine(self) -> None:
        if not self.stream.hasNextLine():
            self.tokenQueue.append(Token(TokenType.EOF, None))
            return
        line = self.stream.nextLine()
        while not line.isspace() and line != "":
            line = self.digestNextToken(line)

    def getToken(self) -> Token:
        while len(self.tokenQueue) == 0:
            self.line += 1
            self.pullTokensFromLine()
        if self.tokenQueue[0].isType(TokenType.EOF):
            return Token(TokenType.EOF, None)
        return self.tokenQueue.pop(0)