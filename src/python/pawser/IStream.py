

class IStream:
    def nextLine(self) -> str:
        raise NotImplementedError()
    def hasNextLine(self) -> bool:
        raise NotImplementedError()
    def close(self):
        raise NotImplementedError()

class Filestream(IStream):
    def __init__(self, fname: str) -> None:
        self.file = open(fname, 'r', encoding='utf8')
        self.more = True
    
    def nextLine(self) -> str:
        line = self.file.readline()
        if line == "":
            self.close()
        return line
    
    def hasNextLine(self) -> bool:
        return self.more

    def close(self) -> None:
        self.more = False
        self.file.close()

