
from pawser.IStream import Filestream
from pawser.Tokenizer import Tokenizer
from pawser.Pawser import Pawser
from executor.Runner import Runner

import os

def main(root: str):
    fs = Filestream(root)
    tokens = Tokenizer(fs)

    p = Pawser(tokens)
    p.parse_START()
    # print(p.tree)

    r = Runner(p.tree, basedir=os.path.dirname(root))
    r.run()

