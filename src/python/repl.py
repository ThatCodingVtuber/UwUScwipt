

from typing import List
from pawser.IStream import IStream
from pawser.Tokenizer import Tokenizer, SwyntaxError, TokenType
from pawser.Pawser import Pawser, UnexpectedToken
from executor.Runner import Runner, RuntimeException
import VERSION
import sys

class Repler(IStream):
    def __init__(self, lines: List[str]) -> None:
        self.lines = lines
        self.currentLine = 0
    def hasNextLine(self) -> bool:
        return self.currentLine < len(self.lines)
    def nextLine(self) -> str:
        if self.hasNextLine():
            line = self.lines[self.currentLine]
            self.currentLine += 1
            return line
        return ""
    def reset(self):
        self.currentLine = 0

def main():
    vi = sys.version_info
    print(VERSION.NAME, VERSION.VERSION, "running on Python",
        '.'.join([str(vi.major), str(vi.minor), str(vi.micro)]))
    print("Licensed under the MIT license (read LICENSE.md)")
    print("Read README.md for documentation")
    print("Quit with Ctrl+C")

    repler = Repler([])
    SF = None

    try:
        inp = input("ଘ(੭ ˘ ᵕ˘)━☆ﾟ.*･｡ﾟᵕ꒳ᵕ~ ")
        while True:
            repler.lines.append(inp)
            repler.reset()

            try:
                t = Tokenizer(repler)
                p = Pawser(t)
                p.parse_START()

                runner = Runner(p.tree, SF)
                runner.run()
                SF = runner.globals

                repler.lines.clear()
                repler.reset()
            except UnexpectedToken as ue:
                # If the UnexpectedToken error was caused by an unexpected EOF, then we can try getting more text
                if not ue.got.isType(TokenType.EOF):
                    print(ue, "(≧д≦ヾ)")
                    repler.lines.clear()
                    repler.reset()
            except SwyntaxError as se:
                print(se, "(≧д≦ヾ)")
                repler.lines.clear()
                repler.reset()
            except RuntimeException as re:
                print("Oh nyo! Wuntime exception:", re, "(≧д≦ヾ)")
                repler.lines.clear()
                repler.reset()
            
            if len(repler.lines) == 0:
                inp = input("ଘ(੭ ˘ ᵕ˘)━☆ﾟ.*･｡ﾟᵕ꒳ᵕ~ ")
            else:
                inp = input("ଘ(੭ ˘ ᵕ˘)━☆ﾟ.*･｡ﾟᵕ꒳ᵕ~ ~> ")
    except KeyboardInterrupt:
        pass
