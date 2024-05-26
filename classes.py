class EventFunc:
    def __init__(self):
        self.handlers = {}
        self.instantHandlers = {}
        self.infos = {}
        self.current_id = 0

    def add(self, handler, msg):
        handler_id = self.current_id
        self.handlers[handler_id] = handler
        self.infos[handler_id] = msg
        self.current_id += 1
        return handler_id

    def remove(self, handler_id):
        if handler_id in self.handlers:
            del self.handlers[handler_id]
            del self.infos[handler_id]

    def empty(self):
        for handler_id in self.handlers:
            del self.handlers[handler_id]
            del self.infos[handler_id]

    def trigger(self, *args, **kwargs):
        for handler in self.handlers.values():
            handler(*args, **kwargs)
    
    def search(self):
        fullStr = ""
        for key, value in self.infos.items():
            fullStr += f"ID: {key} | {value} \n"
        return fullStr
    
class CsoundArp:
    def __init__(self, csInstance, instrName, arpType, durs, pitches, vels, *args):
        self.cs = csInstance
        self.arpType = arpType
        self.pitches = pitches
        self.durs = durs
        self.vels = vels
        self.args = args
        self.arpIndex = [0,0,0]
        self.instr = instrName
        print(self.durs)
        print(self.pitches)
        print(self.vels)
        print(self.args)
        print(len(self.args))
        for arg in self.args:
            if len(arg) != 0:
                self.arpIndex.append(0)
    
    def trigger(self):
        d = self.durs[self.arpIndex[0]]
        p = self.pitches[self.arpIndex[1]]
        v = self.vels[self.arpIndex[2]]
        argsStr = ""
        for i, arg in enumerate(self.args):
            if len(arg) == 0:
                break
            argsStr += arg[self.arpIndex[i]] + " "
            self.arpIndex[i] = self.arpIndex[i]+1 if self.arpIndex[i]+1 < len(arg) else 0
            
        self.arpIndex[0] = self.arpIndex[0]+1 if self.arpIndex[0]+1 < len(self.durs) else 0
        self.arpIndex[1] = self.arpIndex[1]+1 if self.arpIndex[1]+1 < len(self.pitches) else 0
        self.arpIndex[2] = self.arpIndex[2]+1 if self.arpIndex[2]+1 < len(self.vels) else 0
        
        score = f"i {self.instr} 0 {d} {p} {v} {argsStr}"
        print(score)
        self.cs.sendScore(score)

class LoopControl:
    def __init__(self, index, pStr, lc):
        self.index = index
        self.pStr = pStr
        self.lc = lc
    
    def search(self):
        return f"{self.index} : {self.pStr}"

class LoopControlC(LoopControl):
    def __init__(self, index, pStr, lc):
        self.index = index
        self.pStr = pStr
        self.lc = lc
    
    def search(self):
        return f"{self.index} : {self.pStr}"
