

from enum import Enum
import math
import os
from typing import Any, Dict, List, Optional, Set

from pawser.Pawser import Tree, Node, NodeType, Pawser, Tokenizer
from pawser.IStream import Filestream

class DataType(Enum):
    NWULL = 0
    BWOOLEAN = 1
    NUMBWER = 2
    STWING = 3
    FWUNCTION = 4

    CWASS = 7
    CWASS_INST = 8
    SCOPE = 9
    MWETHOD = 10

    BUILTIN_FWUNCTION = 14

    MESSAGE_BWEAK = 20 # Used for break statements

class FunctionDef:
    def __init__(self, args: List[str], s: List["StackFrame"], n: Node) -> None:
        self.stack = s
        self.node = n
        self.args = args
class ClassDef:
    def __init__(self, s: List["StackFrame"], n: Node, data: Dict[str, "Data"]) -> None:
        self.stack = s
        self.statics = Data(DataType.SCOPE, data)
        self.newConstructor = None
        
        assert n.type == NodeType.CLASSDEF

        self.methods = {}
        for c in n.children:
            if c.type == NodeType.MWETHOD:
                ident = c.children[0]
                methodArgs = c.children[1]
                fdef = c.children[2]
                self.methods[ident.data] = Data(DataType.MWETHOD, FunctionDef([a.data for a in methodArgs.children], s[:], fdef))
            elif c.type == NodeType.NEW:
                # Save object for later construction
                self.newConstructor = c

class ClassInstance:
    def __init__(self, prototype: ClassDef, exec: "Runner", args: List["Data"], extL: Set[str] = None) -> None:
        if extL is None:
            extL = set()
        extL.add(str(prototype))

        self.members = {}
        self.methodStack = []

        if prototype.newConstructor is not None:
            sf = StackFrame()
            for i, var in enumerate(prototype.newConstructor.children[0].children):
                sf.set(var.data, args[i] if i < len(args) else Data(DataType.NWULL))
            sf.set("watashi", Data(DataType.SCOPE, self.members))
            stack = prototype.stack + [sf]
            for node in prototype.newConstructor.children[1].children:
                if node.type == NodeType.EXTENDS:
                    dat, _ = exec.getIdentDataFromExpr(node.children[0], stack=stack)
                    if dat is None or dat.taipu != DataType.CWASS:
                        raise RuntimeException(f"Object to extend must be CWASSDEF")
                    exprs = [ exec.getDataFromExpr(n, stack=stack) for n in node.children[1].children ]
                    c: ClassDef = dat.value
                    if str(c) in extL:
                        raise RuntimeException("Circuwar Inweritance")
                    cinst = ClassInstance(c, exec, exprs, extL)
                    for ms in cinst.methodStack:
                        self.methodStack.append(ms)
                    for s in cinst.members:
                        self.members[s] = cinst.members[s]
                else:
                    exec.executeNode(node, stack=stack)
            self.methodStack.append(prototype.methods)
            self.methodStack.reverse()
    def has(self, ident: str) -> bool:
        if ident in self.members:
            return True
        for methods in self.methodStack:
            if ident in methods:
                return True
        return False
    def get(self, ident: str) -> "Data":
        if ident in self.members:
            return self.members[ident]
        for methods in self.methodStack:
            if ident in methods:
                return methods[ident]
        return Data(DataType.NWULL)
    def __repr__(self) -> str:
        return "Class Instance: \nScope: " + ', '.join([ m for m in self.members ]) + "\n" + \
            '\n'.join(["Method Stack:"] + [', '.join([ m for m in M ]) for M in self.methodStack])

def toArglistStr(args: List[str]):
    if len(args) == 0:
        return 'OwO'
    elif len(args) == 1:
        return args[0] + ' UwU'
    elif len(args) >= 3:
        return ', '.join(args[:-1]) + ', and' + args[-1]
    else:
        return ' and '.join(args)

class Data:
    def __init__(self, type: DataType, value: Any = None) -> None:
        self.taipu = type
        self.value = value
    @staticmethod
    def buildClassDef(node: Node, exec: "Runner") -> None:
        assert node.type == NodeType.CLASSDEF
        sf = StackFrame()
        for c in node.children:
            if c.type != NodeType.MWETHOD and c.type != NodeType.NEW:
                exec.executeNode(c, stack=exec.stack + [sf])
        return Data(DataType.CWASS, ClassDef(exec.stack[:], node, sf.data))
    @staticmethod
    def instantiate(cwass: "Data", exec: "Runner", args: List["Data"]) -> None:
        if cwass.taipu != DataType.CWASS:
            raise RuntimeException(f"Cannot instantiate {cwass.taipu.name}")
        return Data(DataType.CWASS_INST, ClassInstance(cwass.value, exec, args))
    def update(self, type: DataType, value: Any = None) -> None:
        self.taipu = type
        self.value = value
    def getPossessive(self, node: Node, ident: str, create: bool = False) -> "Data":
        if self.taipu == DataType.NWULL:
            return Data(DataType.NWULL)
        if self.taipu == DataType.CWASS:
            c: ClassDef = self.value
            return c.statics.getPossessive(node, ident, create=create)
        if self.taipu == DataType.CWASS_INST:
            c: ClassInstance = self.value
            if not c.has(ident):
                if not create:
                    return Data(DataType.NWULL)
                c.members[ident] = Data(DataType.NWULL)
            return c.get(ident)
        if self.taipu == DataType.SCOPE:
            if ident not in self.value:
                if not create:
                    return Data(DataType.NWULL)
                self.value[ident] = Data(DataType.NWULL)
            return self.value[ident]
        raise RuntimeException(node, f"Cannot get possessive of {self.taipu}")
    def __str__(self) -> str:
        if self.taipu == DataType.NWULL:
            return "nwull"
        if self.taipu == DataType.NUMBWER:
            if self.value == float(int(self.value)):
                return str(math.floor(self.value))
            return str(self.value)
        if self.taipu == DataType.STWING:
            return self.value
        if self.taipu == DataType.BWOOLEAN:
            return "twue" if self.value else "fawse"
        if self.taipu == DataType.FWUNCTION:
            return "fwunction " + toArglistStr(F.args)
        if self.taipu == DataType.MWETHOD:
            F: FunctionDef = self.value
            return "mwethod " + toArglistStr(F.args)
        if self.taipu == DataType.CWASS:
            c: ClassDef = self.value
            s = [ f"{key}: {c.statics.value[key]}" for key in c.statics.value ]
                #+ [ f"{n.children[0].data} {toArglistStr([ a.data for a in n.children[1].children ])}" for n in c.node.children if n.type == NodeType.MWETHOD ]
            return 'cwassu { ' + ', '.join(s) + ' }'
        if self.taipu == DataType.CWASS_INST:
            def procVal(d: Data):
                if d.taipu == DataType.CWASS_INST:
                    return "cwassu"
                return str(d)
            c: ClassInstance = self.value
            return '{ ' + ', '.join([ f"{k}: {procVal(c.members[k])}" for k in c.members ]) + ' }'
        return "BUILTIN"
    def __repr__(self) -> str:
        return self.__str__()

class BuiltinFwunction:
    def call(self, node: Node, args: List[Data]) -> Data:
        raise NotImplementedError()
class BuiltinNaryFwunction(BuiltinFwunction):
    def __init__(self, minArg: int = 0, maxArg: int = -1) -> None:
        self.minArg = minArg
        self.maxArg = maxArg
    def call(self, node: Node, args: List[Data]) -> Data:
        if len(args) < self.minArg:
            raise RuntimeException(node, f"Expwected {self.minArg} args, got {len(args)}")
        if self.maxArg >= 0 and len(args) > self.maxArg:
            raise RuntimeException(node, f"Expwected {self.maxArg} args, got {len(args)}")
        return self.evaluate(node, args)
    def evaluate(self, node: Node, args: List[Data]) -> Data:
        raise NotImplementedError()
class BuiltinBinawyFwunction(BuiltinNaryFwunction):
    def __init__(self) -> None:
        super().__init__(2, 2)
class BuiltinNumbwerFwunction(BuiltinFwunction):
    def __init__(self, minArg: int = 0, maxArg: int = -1) -> None:
        self.minArg = minArg
        self.maxArg = maxArg
    def call(self, node: Node, args: List[Data]) -> Data:
        if len(args) < self.minArg:
            raise RuntimeException(node, f"Expwected {self.minArg} args, got {len(args)}")
        if self.maxArg >= 0 and len(args) > self.maxArg:
            raise RuntimeException(node, f"Expwected {self.maxArg} args, got {len(args)}")
        if any(a.taipu != DataType.NUMBWER for a in args):
            return Data(DataType.NWULL)
        return self.evaluate(node, [ a.value for a in args ])
    def evaluate(self, node: Node, args: List[float]) -> Data:
        raise NotImplementedError()
class BuiltinBinawyNumbwerFwunction(BuiltinNumbwerFwunction):
    def __init__(self) -> None:
        super().__init__(2, 2)
class BuiltinBinawyUnawyFwunction(BuiltinNumbwerFwunction):
    def __init__(self) -> None:
        super().__init__(1, 1)
class BUILTIN_PWINT(BuiltinFwunction):
    def call(self, node: Node, args: List[Data]) -> Data:
        print(' '.join([ str(a) for a in args ]))
        return Data(DataType.NWULL)
class BUILTIN_INPUT(BuiltinFwunction):
    def call(self, args: List[Data]) -> Data:
        return Data(DataType.STWING, input(' '.join([ str(a) for a in args ])))
class BUILTIN_NUM_INPUT(BuiltinFwunction):
    def call(self, args: List[Data]) -> Data:
        n = input(' '.join([ str(a) for a in args ]))
        try:
            return Data(DataType.NUMBWER, float(n))
        except ValueError:
            return Data(DataType.NWULL)
class BUILTIN_JOIN(BuiltinNaryFwunction):
    def __init__(self) -> None:
        super().__init__(1)
    def call(self, args: List[Data]) -> Data:
        return Data(DataType.STWING, ''.join([ str(a) for a in args ]))
class BUILTIN_STWING(BuiltinBinawyUnawyFwunction):
    def call(self, args: List[Data]) -> Data:
        return Data(DataType.STWING, str(args[0]))
class BUILTIN_NWUMBER(BuiltinBinawyUnawyFwunction):
    def call(self, node: Node, args: List[Data]) -> Data:
        d = args[0]
        if d.taipu == DataType.NUMBWER:
            return Data(d.taipu, d.value)
        if d.taipu == DataType.STWING:
            try:
                return Data(d.taipu, float(d.value))
            except ValueError:
                pass
        return Data(DataType.NWULL)
class BUILTIN_SUM(BuiltinNumbwerFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        s = 0.0
        for a in args:
            s += a
        return Data(DataType.NUMBWER, s)
class BUILTIN_PRODUCT(BuiltinNumbwerFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        p = 1.0
        for a in args:
            p *= a
        return Data(DataType.NUMBWER, p)
class BUILTIN_DIFF(BuiltinBinawyNumbwerFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.NUMBWER, args[0] - args[1])
class BUILTIN_DIWISION(BuiltinBinawyNumbwerFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        if args[1] == 0.0:
            if args[0] > 0:
                return math.inf
            elif args[0] < 0:
                return -math.inf
            else:
                return 0.0
        return Data(DataType.NUMBWER, args[0] / args[1])
class BUILTIN_MOD(BuiltinBinawyNumbwerFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.NUMBWER, args[0] % args[1])
class BUILTIN_NEGATIVE(BuiltinBinawyUnawyFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.NUMBWER, -args[0])
class BUILTIN_ABS(BuiltinBinawyUnawyFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.NUMBWER, abs(args[0]))
class BUILTIN_FLOOR(BuiltinBinawyUnawyFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.NUMBWER, float(math.floor(args[0])))
class BUILTIN_ROUND(BuiltinBinawyUnawyFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.NUMBWER, float(math.floor(args[0] + 0.5)))
class BUILTIN_CEIL(BuiltinBinawyUnawyFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.NUMBWER, float(math.ceil(args[0])))
class BUILTIN_SQRT(BuiltinBinawyUnawyFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.NUMBWER, float(math.sqrt(args[0])))
class BUILTIN_GTR(BuiltinBinawyNumbwerFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.BWOOLEAN, args[0] > args[1])
class BUILTIN_LSS(BuiltinBinawyNumbwerFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.BWOOLEAN, args[0] < args[1])
class BUILTIN_GTREQ(BuiltinBinawyNumbwerFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.BWOOLEAN, args[0] >= args[1])
class BUILTIN_LSSEQ(BuiltinBinawyNumbwerFwunction):
    def evaluate(self, node: Node, args: List[float]) -> Data:
        return Data(DataType.BWOOLEAN, args[0] <= args[1])
class BUILTIN_EQ(BuiltinNaryFwunction):
    def __init__(self) -> None:
        super().__init__(2)
    def evaluate(self, node: Node, args: List[Data]) -> Data:
        a = args[0]
        for v in args[1:]:
            if a.taipu != v.taipu or a.value != v.value:
                return Data(DataType.BWOOLEAN, False)
        return Data(DataType.BWOOLEAN, True)
class BUILTIN_NEQ(BuiltinNaryFwunction):
    def __init__(self) -> None:
        super().__init__(2)
    def evaluate(self, node: Node, args: List[Data]) -> Data:
        a = args[0]
        for v in args[1:]:
            if a.taipu != v.taipu or a.value != v.value:
                return Data(DataType.BWOOLEAN, True)
        return Data(DataType.BWOOLEAN, False)
class BUILTIN_AND(BuiltinBinawyFwunction):
    def evaluate(self, node: Node, args: List[Data]) -> Data:
        a = not (args[0].taipu == DataType.NWULL or (args[0].taipu == DataType.BWOOLEAN and not args[0].value))
        b = not (args[1].taipu == DataType.NWULL or (args[1].taipu == DataType.BWOOLEAN and not args[1].value))
        return Data(DataType.BWOOLEAN, a and b)
class BUILTIN_OR(BuiltinBinawyFwunction):
    def evaluate(self, node: Node, args: List[Data]) -> Data:
        a = not (args[0].taipu == DataType.NWULL or (args[0].taipu == DataType.BWOOLEAN and not args[0].value))
        b = not (args[1].taipu == DataType.NWULL or (args[1].taipu == DataType.BWOOLEAN and not args[1].value))
        return Data(DataType.BWOOLEAN, a or b)
class BUILTIN_NOR(BuiltinBinawyFwunction):
    def evaluate(self, node: Node, args: List[Data]) -> Data:
        a = not (args[0].taipu == DataType.NWULL or (args[0].taipu == DataType.BWOOLEAN and not args[0].value))
        b = not (args[1].taipu == DataType.NWULL or (args[1].taipu == DataType.BWOOLEAN and not args[1].value))
        return Data(DataType.BWOOLEAN, not (a or b))
class BUILTIN_INDEX(BuiltinNaryFwunction):
    def __init__(self) -> None:
        super().__init__(2, 2)
    def evaluate(self, node: Node, args: List[Data]) -> Data:
        table = args[0]
        index = args[1]
        if table.taipu == DataType.NWULL or index.taipu == DataType.NWULL:
            return Data(DataType.NWULL)
        indexS = str(index.value)
        return table.getPossessive(node, indexS)
class BUILTIN_SETINDEX(BuiltinNaryFwunction):
    def __init__(self) -> None:
        super().__init__(3, 3)
    def evaluate(self, node: Node, args: List[Data]) -> Data:
        table = args[0]
        index = args[1]
        value = args[2]
        if table.taipu == DataType.NWULL or index.taipu == DataType.NWULL:
            return Data(DataType.NWULL)
        indexS = str(index.value)
        dat = table.getPossessive(node, indexS, True)
        dat.update(value.taipu, value.value)
        return Data(DataType.NWULL)

class StackFrame:
    def __init__(self) -> None:
        self.data: Dict[str, Data] = {}
    def has(self, ident: str):
        return ident in self.data
    def get(self, ident: str):
        return self.data[ident]
    def set(self, ident: str, data: Data):
        self.data[ident] = data
    
    def __repr__(self) -> str:
        return "StackFrame(" + ','.join([ f"{k}: {self.data[k]}" for k in self.data ]) + ")"

def reconstructNodeName(n: Node):
    if n.type == NodeType.IDENTIFIER_EXPR:
        s = n.children[0].data
        for n2 in n.children[1:]:
            s += "'s " + n2.data
        return s

class RuntimeException(Exception):
    def __init__(self, node: Node, s: str, returnStack: List[Node] = None) -> None:
        if returnStack is None:
            returnStack = []
        self.node = node
        self.err = s
        self.returnStack = returnStack
        self.lines = []
        for r in self.returnStack:
            s2 = reconstructNodeName(r)
            self.lines.append(f"    cawled at {s2} on wine {r.line}")
        super().__init__('\n'.join([f"Oh Nyo! Pwogwam ewwow on wine {node.line}! {s}   ┐('～`;)┌"] + self.lines))

class Runner:
    def __init__(self, tree: Tree, initSf: StackFrame = None, basedir: str = "") -> None:
        if basedir == "":
            self.basedir = os.getcwd()
        else:
            self.basedir = basedir

        self.code = tree

        self.stack: List[StackFrame] = [  ]
        self.globals = initSf
        
        if self.globals is None:
            # Default globals
            self.globals = StackFrame()
            self.globals.set("pwint", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_PWINT()))
            self.globals.set("nani", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_INPUT()))
            self.globals.set("moshi moshi", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_NUM_INPUT()))
            self.globals.set("conneko", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_JOIN()))
            self.globals.set("nwumber", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_NWUMBER()))
            self.globals.set("stwing", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_STWING()))

            self.globals.set("sum", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_SUM()))
            self.globals.set("pwoduct", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_PRODUCT()))
            self.globals.set("diffwence", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_DIFF()))
            self.globals.set("diwision", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_DIWISION()))
            self.globals.set("wemainder", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_MOD()))

            self.globals.set("negative", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_NEGATIVE()))
            self.globals.set("absowute", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_ABS()))
            self.globals.set("fwoor", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_FLOOR()))
            self.globals.set("wound", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_ROUND()))
            self.globals.set("ceiwing", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_CEIL()))
            self.globals.set("sqware woot", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_SQRT()))

            self.globals.set("is bwiger", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_GTR()))
            self.globals.set("is smowwer", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_LSS()))
            self.globals.set("as bwig as", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_GTREQ()))
            self.globals.set("as smol as", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_LSSEQ()))
            self.globals.set("same", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_EQ()))
            self.globals.set("not same", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_NEQ()))
            self.globals.set("both", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_AND()))
            self.globals.set("neither", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_NOR()))
            self.globals.set("either", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_OR()))

            self.globals.set("index", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_INDEX()))
            self.globals.set("update index", Data(DataType.BUILTIN_FWUNCTION, BUILTIN_SETINDEX()))
        
        self.stack.append(self.globals)

    def getData(self, node: Node, ident: str, stack: List[StackFrame] = None, create: bool = False) -> Data:
        if stack is None:
            stack = self.stack
        # Go through the function stack to find the data
        for frame in reversed(stack):
            if frame.has(ident):
                return frame.get(ident)
        if create:
            d = Data(DataType.NWULL)
            stack[-1].set(ident, d)
            return d
        raise RuntimeException(node, f"Could not find {ident}")

    def getDataFromExpr(self, node: Node, stack: List[StackFrame] = None) -> Data:
        assert node.type == NodeType.EXPWESSION

        expr = node.children[0]
        if expr.type == NodeType.CONST_NWULL:
            return Data(DataType.NWULL)
        if expr.type == NodeType.CONST_NUMBWER:
            return Data(DataType.NUMBWER, expr.data)
        if expr.type == NodeType.CONST_BWOOLEAN:
            return Data(DataType.BWOOLEAN, expr.data)
        if expr.type == NodeType.CONST_STWING:
            return Data(DataType.STWING, expr.data)
        if expr.type == NodeType.IDENTIFIER_EXPR:
            data, parent = self.getIdentDataFromExpr(expr, stack=stack)
            if len(node.children) == 2 and node.children[1].type == NodeType.FCALL:
                exprs = [ self.getDataFromExpr(n, stack=stack) for n in node.children[1].children[0].children ]
                if data.taipu == DataType.BUILTIN_FWUNCTION:
                    return data.value.call(node, exprs)
                elif data.taipu == DataType.FWUNCTION:
                    fdef: FunctionDef = data.value
                    frame = StackFrame()
                    for i, var in enumerate(fdef.args):
                        frame.set(var, exprs[i] if i < len(exprs) else Data(DataType.NWULL))
                    try:
                        return self.executeNode(fdef.node, stack=fdef.stack + [frame])
                    except RuntimeException as re:
                        raise RuntimeException(re.node, re.err, re.returnStack + [expr])
                elif data.taipu == DataType.CWASS:
                    return Data.instantiate(data, self, exprs)
                elif data.taipu == DataType.MWETHOD:
                    fdef: FunctionDef = data.value
                    frame = StackFrame()
                    for i, var in enumerate(fdef.args):
                        frame.set(var, exprs[i] if i < len(exprs) else Data(DataType.NWULL))
                    frame.set("watashi", Data(DataType.SCOPE, parent.value.members))
                    try:
                        return self.executeNode(fdef.node, stack=fdef.stack + [frame])
                    except RuntimeException as re:
                        raise RuntimeException(re.node, re.err, re.returnStack + [expr])
            else:
                return data
        if expr.type == NodeType.ARGLIST:
            return Data(DataType.FWUNCTION, FunctionDef([a.data for a in node.children[0].children], self.stack[:], node.children[1]))
        if expr.type == NodeType.CLASSDEF:
            return Data.buildClassDef(expr, self)

    def getIdentDataFromExpr(self, node: Node, create: bool = False, require: bool = False, stack: List[StackFrame] = None) -> Data:
        if node.type == NodeType.IDENTIFIER_EXPR:
            current = None
            parent = None
            isWatashi = False
            for n in node.children:
                isWatashi = n.data == "watashi"
                parent = current
                if current is None:
                    current = self.getData(n, n.data, stack=stack, create=create)
                else:
                    current = current.getPossessive(n, n.data, create=create)
                    if current is None:
                        break
            if isWatashi and create:
                raise RuntimeException(node, f"Cannot set watashi!")
            if current is None:
                paf = reconstructNodeName(node)
                raise RuntimeException(node, f"Cwould not fwind {paf}")
            elif require and current.taipu == DataType.NWULL:
                paf = reconstructNodeName(node)
                raise RuntimeException(node, f"Cwould not fwind {paf}")
            return current, parent

    def executeNode(self, node: Node, stack: List[StackFrame] = None) -> Optional[Data]:
        if node.type == NodeType.SET:
            val,_ = self.getIdentDataFromExpr(node.children[0], stack=stack, create=True)
            dat = self.getDataFromExpr(node.children[1], stack=stack)
            if dat is None:
                dat = Data(DataType.NWULL)
            val.update(dat.taipu, dat.value)
            return
        if node.type == NodeType.CAWL:
            F,parent = self.getIdentDataFromExpr(node.children[0], require=True, stack=stack)
            if F is None or F.taipu == DataType.NWULL:
                raise RuntimeException(node, f"Unknown vawiable")
            exprs = [ self.getDataFromExpr(n, stack=stack) for n in node.children[1].children ]
            if F.taipu == DataType.BUILTIN_FWUNCTION:
                F.value.call(node, exprs)
            elif F.taipu == DataType.FWUNCTION:
                fdef: FunctionDef = F.value
                frame = StackFrame()
                for i, var in enumerate(fdef.args):
                    frame.set(var, exprs[i] if i < len(exprs) else Data(DataType.NWULL))
                try:
                    self.executeNode(fdef.node, stack=fdef.stack + [frame])
                except RuntimeException as re:
                    raise RuntimeException(re.node, re.err, re.returnStack + [node.children[0]])
            elif F.taipu == DataType.MWETHOD:
                fdef: FunctionDef = F.value
                frame = StackFrame()
                for i, var in enumerate(fdef.args):
                    frame.set(var, exprs[i] if i < len(exprs) else Data(DataType.NWULL))
                frame.set('watashi', parent)
                try:
                    self.executeNode(fdef.node, stack=fdef.stack + [frame])
                except RuntimeException as re:
                    raise RuntimeException(re.node, re.err, re.returnStack + [node.children[0]])
            return
        if node.type == NodeType.FDEF:
            for n in node.children:
                dat = self.executeNode(n, stack=stack)
                if dat is not None:
                    return dat
            return
        if node.type == NodeType.IFFU:
            for n in node.children:
                if n.type == NodeType.COND:
                    cond = self.getDataFromExpr(n.children[0], stack=stack)
                    if cond is not None:
                        condEval = cond.taipu != DataType.NWULL and (cond.taipu != DataType.BWOOLEAN or cond.value)
                        if condEval:
                            n = self.executeNode(n.children[1], stack=stack)
                            return n
                elif n.type == NodeType.FDEF:
                    return self.executeNode(n, stack=stack)
            return
        if node.type == NodeType.REPEAT:
            while True:
                for n in node.children:
                    dat = self.executeNode(n, stack=stack)
                    if dat is not None:
                        if dat.taipu == DataType.MESSAGE_BWEAK:
                            if dat.value > 1:
                                return Data(DataType.MESSAGE_BWEAK, dat.value - 1)
                            else:
                                return
        if node.type == NodeType.BWEAK:
            return Data(DataType.MESSAGE_BWEAK, node.data)
        if node.type == NodeType.FILE:
            for n in node.children:
                d = self.executeNode(n)
                if d is not None:
                    return d
            return
        if node.type == NodeType.GIVE:
            return self.getDataFromExpr(node.children[0], stack=stack)
        if node.type == NodeType.WOAD:
            path = str(self.getDataFromExpr(node.children[0], stack=stack))
            if path.startswith('#'):
                bd = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                fpath = os.path.abspath(os.path.join(bd, 'stdlib', path[1:] + '.uwu'))
            else:
                fpath = os.path.abspath(os.path.join(self.basedir, path + '.uwu'))
            parser = Pawser(Tokenizer(Filestream(fpath)))
            parser.parse_START()
            exec = Runner(parser.tree, basedir=os.path.dirname(fpath))
            val,_ = self.getIdentDataFromExpr(node.children[1], stack=stack, create=True)
            dat = exec.run()
            if dat is None or dat.taipu == DataType.MESSAGE_BWEAK:
                dat = Data(DataType.SCOPE, exec.stack[0].data)
            val.update(dat.taipu, dat.value)
            return

    def run(self) -> None:
        try:
            return self.executeNode(self.code.base)
        except RuntimeException as re:
            print(re)
