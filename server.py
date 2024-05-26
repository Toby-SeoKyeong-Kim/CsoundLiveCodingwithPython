import socket
import threading
import ctcsound
import time
import classes
import numpy as np
import pyaudio
import musicalData


clients = {}
instruments = {}
instrInfo = {}
instrSource = {}
cs = ctcsound.Csound()
instrNum = 2
lock = threading.Lock()
bpm = 120
quant = 1600
beatPos = 0
barPos = 0
tick = 0
elapsedTime = 0
maxBeat = 4
maxBar = 16
tickRes = 400
interval = (60 / bpm) / tickRes
# Create event objects
stop_event = threading.Event()
pause_event = threading.Event()
eventArray = []
keyCenter = 0
chordCenter = 0
chordType = 0
quantEvents = []
loopArray = []
loopIndex = 1002
loopControlMap = {}

busMap = {}
busTrackMap = {}
busTrackControlMap = {}
busTrackPlaybackMap = {}
busTrackUsingBuses = {}
busTrackInfo = {}

chnMap = {}

busTrackIndex = 500
giArrayIndex=0
sr = 44100.0
# Parameters
RATE = 44100  # Sample rate (Hz)
cnt = 0

chordProgression = []

chordModeMapSwap = {
    0: "M7",
    1: "m7",
    2: "m7",
    3: "M7",
    4: "7",
    5: "m7",
    6: "m7b5",
    7: "7alt"
}

chordModeMap ={
    "ion": 0,
    "dor": 1,
    "phr": 2,
    "lyd": 3,
    "mix": 4,
    "aeo": 5,
    "loc": 6,
    "alt": 7,
    }

chordRootMap ={
    "1": 0,
    "8": 0,
    "b2": 1,
    "s1": 1,
    "2": 2,
    "s2": 3,
    "b3": 3,
    "3": 4,
    "4": 5,
    "11": 5,
    "s4": 6,
    "s11": 6,
    "b5": 6,
    "b13": 6,
    "5": 7,
    "13":7,
    "s5": 8,
    "s13": 8,
    "b6":8,
    "6": 9,
    "s6": 10,
    "b7": 10,
    "7": 11,
    "b1": 11
    }

keyMap = {
    "c":0,
    "cs":1,
    "db":1,
    "d":2,
    "ds":3,
    "eb":3,
    "e":4,
    "es":5,
    "fb":4,
    "f":5,
    "fs":6,
    "gb":6,
    "g":7,
    "gs":8,
    "ab":8,
    "a":9,
    "as":10,
    "bb":10,
    "b":11,
    "bs":0,
    "cb":11
}
keyStr = "c"
chordSemanticDictionary = {
    "c": musicalData.chordRootSemantic_c,
    "cs":musicalData.chordRootSemantic_cs,
    "db":musicalData.chordRootSemantic_db,
    "d":musicalData.chordRootSemantic_d,
    "ds":musicalData.chordRootSemantic_ds,
    "eb":musicalData.chordRootSemantic_eb,
    "e": musicalData.chordRootSemantic_e,
    "es": musicalData.chordRootSemantic_f,  # Enharmonic equivalent of F
    "fb": musicalData.chordRootSemantic_e,   # Enharmonic equivalent of E
    "f": musicalData.chordRootSemantic_f,
    "fs": musicalData.chordRootSemantic_fs,
    "gb": musicalData.chordRootSemantic_gb,
    "g": musicalData.chordRootSemantic_g,
    "gs": musicalData.chordRootSemantic_gs,
    "ab": musicalData.chordRootSemantic_ab,
    "a": musicalData.chordRootSemantic_a,
    "as": musicalData.chordRootSemantic_as,  # Enharmonic equivalent of Bb
    "bb": musicalData.chordRootSemantic_bb,
    "b": musicalData.chordRootSemantic_b,
    "bs": musicalData.chordRootSemantic_c,   # Enharmonic equivalent of C
    "cb": musicalData.chordRootSemantic_cb
}

commands_description = {
    'orcIn': 'InstrName Source',
    'scoreIn': 'InstrName Duration P4 P5 ...',
    'instrSearch': 'no parameter needed',
    'setLoop': 'MaxBeat MaxBar\n',
    'loopIn': 'InstrName LoopInterval LoopPosOffset Duration p4 p5 ...\n\tLoopInterval: in relation to quarter note (1 = quarter note)\n\tLoopPosOffset: in relation to quarter note (1 = quarter note)\n\tDuration: in relation to quarter note (1 = quarter note)',
    'cLoopIn': 'InstrName LoopInterval LoopPosOffset LoopType Durations p4s p5s ...\n\tLoopInterval: in relation to quarter note (1 = quarter note)\n\tLoopPosOffset: in relation to quarter note (1 = quarter note)\n\tLoopType: 0 accending, 1 decending, 2 random\n\tDuration: in relation to quarter note (1 = quarter note)\n\tYou can have as many durations as you want.\n\tEach element is separated by "," i.e. .5,.4,.6\n\tSame goes for p4s p5s ...',
    'cLoopInB': 'InstrName LoopInterval LoopPosOffset LoopType Chord/Key min,max,cur Degrees Durations p5s p6s ...\n\tLoopInterval: in relation to quarter note (1 = quarter note)\n\tLoopPosOffset: in relation to quarter note (1 = quarter note)\n\tLoopType: 0 accending, 1 decending, 2 random\n\tChord/Key: whether to bind this loop to the chord or the key (0 = chord, 1 = key)\n\tmin,max,cur: 3 parameters separated by ",".\n\tif 60,80,60 this loop will have p4 value from 60 to 80 starting from 60\n\tDegrees: from the range you specified, what degree from the chord (or key) you would allow\n\tif 1,3,5 meaning that you will allow 1st 3rd and 5th notes from your chord (or key)\n\tDuration: in relation to quarter note (1 = quarter note)\n\tYou can have as many durations as you want.\n\tEach element is separated by "," i.e. .5,.4,.6\n\tSame goes for p5s p6s ...',
    'removeLoop': 'LoopIndex\n\tthis can be obtained by searchLoop',
    'searchLoop': 'no parameter needed',
    'setChord': 'IntervalFromRoot ChordMode\n\t 1 Ion \n\t b3 phr \n\t s5 lyd \n\t possible modes are Ion Dor Phr Lyd Mix Aeo Loc Alt',
    'setKey': 'Key(C,D,Eb,Fs...)',
    'addBus': 'BusName(starts with "ga")',
    'busInstr': 'BusInstrName BusNamesbeingUsed Source\n\t BusNamesbeingUsed is optional but highly recommended to specify to avoid conflict with other instruments',
    'busTrackPlay': 'BusInstrName',
    'busTrackStop': 'BusInstrName',
    'busSearch': 'no parameter needed',
    'addChn': 'ChnName initialValue',
    'setChn': 'ChnName newValue',
    'searchChn': 'no parameter needed',
    'setBpm': 'newBpm',
    'help': 'commandName (if none provided, list of all commands)'
}


def eventArrayInit():

    for i in range(maxBar):
        chordProgression.append([0,0,"1"])

def orcIn(msg, c):
    global instrNum
    global instruments
    global instrInfo
    source = ' '.join(msg[1:])
    with lock:
        orc = f"""
        instr {instrNum}
        \t{source}
        endin
        """
        instrInfo[msg[0]] = orc
        instruments[msg[0]] = instrNum
        instrSource[msg[0]] = source
        instrNum += 1
    cs.compileOrc(orc)
    response(f"new Instrument named '{msg[0]}' assigned!",c)
    broadcast(f"new Instrument named '{msg[0]}' assigned!",c)
    print("ornIn!!  " + orc)

def scoreIn(msg, c):
    instr = instruments[msg[0]]
    dur = " ".join(msg[1:])
    score = f"i {instr} 0 {dur}"
    quantEvents.append(lambda score=score: cs.inputMessage(score))
    print("scoreIn!!  " + score)



def loopIn(msg, c):
    global loopIndex
    loopLength = float(msg[1])
    loopPos = float(msg[2]) * (60/bpm)
    source = instrSource[msg[0]]
    dur = ", ".join(msg[3:])
    loopControl = f"gil{loopIndex}"
    with lock:
        score = f"schedule({loopIndex}, {loopPos}, {dur})"
        numP = len(msg[3:])
        pStr = f"schedule({loopIndex}, {loopLength} * (60/ibpm)"
        for i in range(numP):
            pStr += ", "
            pStr += f"p{i+3}"
        pStr += ")"
        orc = f"""
            instr {loopIndex}
            ibpm chnget "bpm"
            {source}
            if {loopControl} == 1 then
            {pStr}
            endif
            endin
            """
        loopControlMap[loopIndex] = classes.LoopControl(loopIndex,pStr,loopControl)
        result = cs.compileOrc(f"{loopControl} init 1")
        if result != 0:
            print("something went wrong!!!!!!")
        result = cs.compileOrc(orc)
        if result != 0:
            print(f"Error compiling orc: {orc}")
        quantEvents.append(lambda score=score: send_events(score))
        response(f"new loop assigned at index '{loopIndex}'!",c)
        broadcast(f"new loop assigned at index '{loopIndex}'!",c)
        loopIndex+=1
    print("loopIn!!  " + orc)
    print("loopIn!!  " + score)

def cLoopIn(msg, c):
    global loopIndex
    global giArrayIndex
    loopLength = float(msg[1])
    loopPos = float(msg[2]) * (60/bpm)
    lType = msg[3]
    args = []
    initPVals = [lType]
    if len(msg) > 4:
        for i in range(len(msg)-4):
            argJoin = msg[i+4]
            args.append(argJoin)
            initPVals.append("0")

    instr = instruments[msg[0]]
    pf = ", ".join(initPVals)
    
    pIndex = 5
    getPFields = "iMode = p4\n"
    iValDefine = ""
    iValAdvance = ""
    gi_Arrs = []
    iIndex =[]
    iVals = []
    numP = len(msg[4:])
    lpStrAppend = ""
    triggerStr = f"schedule({instr}, 0, iVal{pIndex}*(60/ibpm)"
    
    
    with lock:
        loopControl = f"gil{loopIndex}"
        for i in range(numP):
            gi_Arrs.append(f"gi_Arr_{giArrayIndex}")
            giArrayIndex+=1
            print("join Array!!   " + msg[i+4])
            cs.compileOrc(f"{gi_Arrs[i]}[] fillarray {msg[i+4]}")

            iIndex.append(f"iField{pIndex}")
            iVals.append(f"iVal{pIndex}")
            getPFields += (f"{iIndex[i]} = p{pIndex}\n")
            pIndex+=1

            iValDefine += f"{iVals[i]} = iMode == 0 ? {gi_Arrs[i]}[{iIndex[i]}] : {gi_Arrs[i]}[rnd(lenarray({gi_Arrs[i]}))]\n"
            if i != 0:
                triggerStr += ", "
                triggerStr += f"{iVals[i]}"
            
            iValAdvance += f"{iIndex[i]} = {iIndex[i]}+1 < lenarray({gi_Arrs[i]}) ? {iIndex[i]} + 1 : 0 \n"

            lpStrAppend += ", "
            lpStrAppend += f"{iIndex[i]}"
        triggerStr += ")"
        lpStrAppend+= ")"
    
        score = f"schedule({loopIndex}, {loopPos}, 0, {pf})"
        lpStr = f"schedule({loopIndex}, {loopLength} * (60/ibpm), 0, {lType}"
        lpStr += lpStrAppend
        orc = f"""
            instr {loopIndex}
            ibpm chnget "bpm"
            \t{getPFields}

            \t{iValDefine}

            \t{triggerStr}
            if {loopControl} == 1 then
            \t{iValAdvance}

            \t{lpStr}
            endif
            endin
            """
        loopControlMap[loopIndex] = classes.LoopControl(loopIndex,lpStr,loopControl)
        cs.compileOrc(f"{loopControl} init 1")
        result = cs.compileOrc(orc)
        if result != 0:
            print(f"Error compiling orc: {orc}")
        quantEvents.append(lambda score=score: send_events(score))
        response(f"new loop assigned at index '{loopIndex}'!",c)
        broadcast(f"new loop assigned at index '{loopIndex}'!",c)
        loopIndex+=1
    print("loopIn!!  " + orc)
    print("loopIn!!  " + score)

def cLoopInB(msg, c):# cLoopInB loopLength loopPos loopType chord/Key [min,max,startPos] [degrees] [durs] [par1] [par2]... 
    global loopIndex
    global giArrayIndex
    loopLength = float(msg[1])
    loopPos = float(msg[2]) * (60/bpm)
    lType = msg[3]
    args = []
    initPVals = []
    if len(msg) > 7:
        for i in range(len(msg)-7):
            argJoin = msg[i+7]
            args.append(argJoin)
            initPVals.append("0")

    instr = instruments[msg[0]]
    pf = ", ".join(initPVals)
    pIndex = 9
    getPFields = ""
    iValDefine = ""
    iValAdvance = ""
    gi_Arrs = []
    iIndex =[]
    iVals = []
    degrees = msg[6].split(",")
    for i in range(len(degrees)):
        degrees[i] = int(degrees[i]) - 1
        while degrees[i] < 0:
            degrees[i] +=12
        while degrees[i] >= 12:
            degrees[i] -=12
    degreesStr = ", ".join(str(d) for d in degrees)
    pitchCon = msg[5].split(',')
    pitchConStr = ", ".join(pitchCon)
    numP = len(msg[7:])
    lpStrAppend = ""
    triggerStr = f"schedule({instr}, 0, iVal{pIndex}*(60/ibpm), ipit"
    
    with lock:
        loopControl = f"gil{loopIndex}"
        for i in range(numP):
            gi_Arrs.append(f"gi_Arr_{giArrayIndex}")
            giArrayIndex+=1
            print("join Array!!   " + msg[i+4])
            cs.compileOrc(f"{gi_Arrs[i]}[] fillarray {msg[i+7]}")

            iIndex.append(f"iField{pIndex}")
            iVals.append(f"iVal{pIndex}")
            getPFields += (f"{iIndex[i]} = p{pIndex}\n")
            pIndex+=1

            iValDefine += f"{iVals[i]} = {gi_Arrs[i]}[{iIndex[i]}]\n"
            if i != 0:
                triggerStr += ", "
                triggerStr += f"{iVals[i]}"

            iValAdvance += f"{iIndex[i]} = {iIndex[i]}+1 < lenarray({gi_Arrs[i]}) ? {iIndex[i]} + 1 : 0 \n"

            lpStrAppend += ", "
            lpStrAppend += f"{iIndex[i]}"
        triggerStr += ")"
        lpStrAppend+= ")"
    
        score = f"schedule({loopIndex}, {loopPos}, 0, {lType}, {msg[4]}, {pitchConStr}, {pf})"
        lpStr = f"schedule({loopIndex}, {loopLength} * (60/ibpm), 0, iMode, ichordKey, iminPit, imaxPit, ipitIndex"
        lpStr += lpStrAppend
        orc = f"""
            instr {loopIndex}
            ibpm chnget "bpm"
            iMode = p4
            ichordKey = p5
            iminPit = p6
            imaxPit = p7
            ipitIndex = p8

            \t{getPFields}

            isafe = 0
            iIter =0
            i_Arr[] fillarray {degreesStr}
            idegree = (ipitIndex % 12)
            ioctave = ipitIndex / 12
            while isafe < 20 do
                iIter = 0
                while iIter < lenarray(i_Arr) do
                    ival getScale giChordMode, i_Arr[iIter]
                    icompare = ichordKey == 0 ? ival + giChord +giKey : i_Arr[iIter] +giKey
                    while icompare < 0 do
                        icompare += 12
                    od
                    while icompare >= 12 do
                        icompare -= 12
                    od
                    if idegree == icompare then
                        goto here
                    endif
                    iIter += 1
                od
                ipitIndex += iMode == 1 ? -1 : 1
                while ipitIndex < iminPit do
                    ipitIndex += imaxPit - iminPit
                od
                idegree = ipitIndex % 12
                isafe += 1
            od
            here:
            if ipitIndex > imaxPit then
                idegree = ipitIndex % 12
                iminDegree = iminPit % 12
                iadd = idegree - iminDegree < 0 ? idegree - iminDegree +12 : idegree - iminDegree
                ipitIndex = iminPit + iadd
            endif
            ipit = ipitIndex

            \t{iValDefine}

            \t{triggerStr}
            if {loopControl} == 1 then
            \t{iValAdvance}
                if iMode == 1 then
                    ipitIndex = ipitIndex-1 > iminPit ? ipitIndex - 1 : imaxPit
                elseif iMode == 2 then
                    ipitIndex += int(rnd(imaxPit - iminPit))
                else
                    ipitIndex = ipitIndex+1 < imaxPit ? ipitIndex + 1 : iminPit
                endif
            \t{lpStr}
            endif
            endin
            """
        loopControlMap[loopIndex] = classes.LoopControl(loopIndex,lpStr,loopControl)
        cs.compileOrc(f"{loopControl} init 1")
        result = cs.compileOrc(orc)
        if result != 0:
            print(f"Error compiling orc: {orc}")
        quantEvents.append(lambda score=score: send_events(score))
        response(f"new loop assigned at index '{loopIndex}'!",c)
        broadcast(f"new loop assigned at index '{loopIndex}'!",c)
        loopIndex+=1
    print("loopIn!!  " + orc)
    print("loopIn!!  " + score)

def addChn(msg,c):
    global chnMap

    chnName = msg[0]
    val = msg[1]
    with lock:
        if chnName in chnMap:
            response(f"Chn Name {chnName} already exists",c)
        else:
            cs.setControlChannel(chnName, float(val))
            chnMap[chnName] = float(val)
            response(f"Chn Name {chnName} added with initial value of {val}",c)
            broadcast(f"Chn Name {chnName} added with initial value of {val}",c)

def setChn(msg,c):
    global chnMap
    chnName = msg[0]
    val = msg[1]
    with lock:
        if chnName in chnMap:
            cs.setControlChannel(chnName, float(val))
            chnMap[chnName] = float(val)
            response(f"Chn Name {chnName} set to {val}",c)
            broadcast(f"Chn Name {chnName} set to {val}",c)
        else:
            response(f"Chn Name {chnName} does not exist",c)

def searchChn(msg,c):
    global chnMap
    addStr = ""
    for k,v in chnMap.items():
        addStr += f"ChnName: {k}   Value: {v}\n"
    response(addStr, c)
def addBus(msg,c):
    global busMap
    busName = msg[0]
    with lock:
        if busName.startswith("ga"):
            if busName in busMap:
                response(f"Bus name '{busName}' already exists",c)
            else:
                busMap[busName] = True
                cs.compileOrc(f"{busName} init 0")
                print(f"Bus name '{busName}' created")
                response(f"Bus name '{busName}' created",c)
                broadcast(f"Bus name '{busName}' created",c)
        else:
            response("Bus name has to start with 'ga'", c)

def busInstr(msg,c):
    busTrackName = msg[0]
    global busTrackIndex
    global busTrackMap
    global busTrackControlMap
    global busTrackPlaybackMap
    global busTrackUsingBuses
    global busTrackInfo

    busesBeingUsed = msg[1].split(",")
    
    source = ' '.join(msg[2:])
    broadcastMsgAppen = ""
    
    
        
    with lock:

        for bus in busesBeingUsed:
            if bus not in busMap:
                response(f"Bus {bus} does not exist!", c)
                return
            else:
                if not busMap[bus]:
                    response(f"bus name '{bus}' is already being used in another bus track")
                    return
                
        for bus in busesBeingUsed:
            busMap[bus] = False
            cs.compileOrc(f"{bus} = 0")
            broadcastMsgAppen += f"{bus}\n"
        busTrackControl = f"gk{busTrackIndex}"
        cs.compileOrc(f"{busTrackControl} init 1")
        orc = f"""
        instr {busTrackIndex}
        \t{source}
        if {busTrackControl} != 1 then
            turnoff
        endif
        endin
        """
        busTrackMap[busTrackName] = busTrackIndex
        busTrackControlMap[busTrackName] = busTrackControl
        busTrackPlaybackMap[busTrackName] = True
        busTrackUsingBuses[busTrackName] = busesBeingUsed
        busTrackInfo[busTrackName] = orc

        cs.compileOrc(orc)
        cs.compileOrc(f"schedule({busTrackIndex}, 0, 900000)")
        broadcast(f"Bus track name '{busTrackName}' assigned, with following buses\n{broadcastMsgAppen}",c)
        response(f"Bus track name '{busTrackName}' assigned, with following buses\n{broadcastMsgAppen}",c)
        busTrackIndex += 1
    print("ornIn!!  " + orc)

def busTrackPlay(msg,c):
    global busTrackUsingBuses
    global busTrackMap
    global busTrackPlaybackMap
    global busTrackControlMap

    with lock:
        busTrackName = msg[0]
        busesBeingUsed = busTrackUsingBuses[busTrackName]
        for bus in busesBeingUsed:
            if bus not in busMap:
                response(f"Bus {bus} does not exist!", c)
                return
            else:
                if not busMap[bus]:
                        response(f"bus name '{bus}' is already being used in another bus track",c)
                        return

        if busTrackName in busTrackPlaybackMap:
            if busTrackPlaybackMap[busTrackName]:
                response(f"Bus track name '{busTrackName}' is already being played",c)
                return
            else:
                busTrackPlaybackMap[busTrackName] = True
                cs.compileOrc(f"{busTrackControlMap[busTrackName]} = 1")
        else:
            response(f"No bus track name '{busTrackName}' assigned yet",c)
            return

        for bus in busesBeingUsed:
            busMap[bus] = False
            cs.compileOrc(f"{bus} = 0")
        
        btIndex = busTrackMap[busTrackName]
        cs.compileOrc(f"schedule({btIndex}, 0, 900000)")

def busTrackStop(msg,c):
    global busTrackUsingBuses
    global busTrackPlaybackMap
    global busTrackControlMap

    with lock:
        busTrackName = msg[0]
        busesBeingUsed = busTrackUsingBuses[busTrackName]
        for bus in busesBeingUsed:
            busMap[bus] = True
        if busTrackName in busTrackPlaybackMap:
            if not busTrackPlaybackMap[busTrackName]:
                response(f"Bus track name '{busTrackName}' is already being stopped")
                return
            else:
                busTrackPlaybackMap[busTrackName] = False
                cs.compileOrc(f"{busTrackControlMap[busTrackName]} = 0")
        else:
            response(f"No bus track name '{busTrackName}' assigned yet")
            return

def busSearch(msg,c):
    global busMap
    for key, value in busMap.items():
        print(f"BusName: {key}, Availability: {value}")

def searchLoop(msg, c):
    responseStr = ""
    for value in loopControlMap.values():
        responseStr += f"{value.search()}\n"
    response(responseStr, c)

def removeLoop(msg, c):
    strInt = int(msg[0])
    if strInt in loopControlMap:
        lc = loopControlMap[strInt].lc
        cs.compileOrc(f"{lc} = 2")
        del loopControlMap[strInt]
        broadcast(f"LoopNum {strInt} got deleted!\n",c)
        response(f"LoopNum {strInt} got deleted!\n",c)
    else:
        response(f"No Loop number {strInt} playing", c)

def send_events(score):
    result = cs.compileOrc(score)
    if result != 0:
        print(f"Error sending score message: {score}")


def instrSearch(msg, c):
    if len(msg) ==0:
        resStr = ""
        for k,v in instrInfo.items():
            resStr += f"{k}\n"
        response(f"{resStr}",c)
        return
    value = instrInfo.get(msg[0])
    if value is not None:
        response(value, c)
    else:
        print(f"Instr '{msg[0]}' does not exist.")  

def setLoop(msg, c):
    global maxBeat 
    global maxBar 
    global beatPos 
    global barPos 
    global tick 
    global chordProgression

    beat = msg[0]
    bar = msg[1]
    

    maxBeat = int(beat)
    maxBar = int(bar)
    for i in range(maxBeat):
        if i >= len(chordProgression):
            chordProgression.append([0,0,"1"])
    broadcast(f"Loop Changed\nNew Beat: {maxBeat}\nNew Measures: {maxBar}",c)
    response(f"Loop Changed\nNew Beat: {maxBeat}\nNew Measures: {maxBar}",c)

def changeChord(pos):
    global chordProgression
    global chordSemanticDictionary
    global keyStr

    semantic = chordProgression[pos][2]
    mode = chordProgression[pos][1]
    code = f"""
                giChord = {chordProgression[pos][0]}
                giChordMode = {chordProgression[pos][1]}
            """
    print(f"Measure: {pos+1}   {chordSemanticDictionary[keyStr][semantic]}{chordModeMapSwap[mode]}")
    cs.compileOrc(code)

def setChord(msg,c):
    global chordProgression
    pos = msg[0]
    if msg[1].lower() in chordRootMap:
        if msg[2].lower() in chordModeMap:
            chord = chordRootMap[msg[1].lower()]
            mode = chordModeMap[msg[2].lower()]
            code = f"""
                pos = {pos}
                giChord = {msg[1]}
                giChordMode = {msg[2]}
            """
            chordProgression[int(pos)-1] = [chord,mode, msg[1].lower()]
            response(f"New chord entry \n {code}", c)
            broadcast(f"New chord entry \n {code}", c)
        else:
            response("setChord should get values like 'b2 Ion' , 's4 Lyd'", c)
    else:
        response("setChord should get values like 'b2 Ion' , 's4 Lyd'", c)

    

def setKey(msg,c):
    global keyStr

    if msg[0].lower() in keyMap:
        code = f"""
        giKey = {keyMap[msg[0].lower()]}
        """
        cs.compileOrc(code)
        keyStr = msg[0].lower()
        broadcast(f"Key changed into {keyStr}",c)
        response(f"Key changed into {keyStr}",c)
    else:
        response("setKey should get values like 'C' , 'Cs' , 'Db'", c)

def help(msg,c):
    if len(msg) == 0:
        listStr = """
        'orcIn' - InstrName Source
        'scoreIn' - InstrName Duration P4 P5 ...
        'instrSearch'
        'setLoop' - MaxBeat MaxBar
        'loopIn' - InstrName LoopInterval LoopPosOffset Duration p4 p5 ...
        'cLoopIn' - InstrName LoopInterval LoopPosOffset LoopType Durations p4s p5s ...
        'cLoopInB' - InstrName LoopInterval LoopPosOffset LoopType Chord/Key min,max,cur Degrees Durations p5s ...
        'removeLoop' - LoopIndex
        'searchLoop'
        'setChord' - IntervalFromRoot ChordMode
        'setKey' - Key(C,D,Eb,Fs...)
        'addBus' - BusName(starts with 'ga')
        'busInstr' - BusInstrName BusNamesbeingUsed Source
        'busTrackPlay' - BusInstrName
        'busTrackStop' - BusInstrName
        'busSearch'
        'addChn' - ChnName initialValue
        'setChn' - ChnName newValue
        'searchChn'
        'setBpm' - newBpm
        For more informations, 'help [CommandName]'
        """
        response(listStr,c)
    else:
        if msg[0] in commands_description:
            response(f"{msg[0]}:\n\t{commands_description[msg[0]]}",c)
        else:
            response(f"Command {msg[0]} does not exist",c)

def setBpm(msg,c):
    global bpm
    newBpm = int(msg[0])
    bpm = newBpm
    cs.setControlChannel('bpm',bpm)
    broadcast(f"BPM changed into {bpm}",c)
    response(f"BPM changed into {bpm}",c)

events = {
    'orcIn': orcIn,
    'scoreIn': scoreIn,
    'instrSearch': instrSearch,
    'setLoop': setLoop,
    'loopIn': loopIn,
    'cLoopIn': cLoopIn,
    'cLoopInB': cLoopInB,
    'removeLoop':removeLoop,
    'searchLoop':searchLoop,
    'setChord':setChord,
    'setKey':setKey,
    'addBus':addBus,
    'busInstr':busInstr,
    'busTrackPlay':busTrackPlay,
    'busTrackStop':busTrackStop,
    'busSearch':busSearch,
    'addChn': addChn,
    'setChn': setChn,
    'searchChn': searchChn,
    'setBpm': setBpm,
    'help':help
}

def handle_message(msg, c):
    msgArray = msg.split(' ')
    contents = msgArray[1:]
    if msgArray[0] in events:
        events[msgArray[0]](contents, c)
    else:
        response("Function does not exists", c)
    

def broadcast(message, sender_id):
    """Send the message to all clients."""
    for client_id, conn in clients.items():
        if client_id != sender_id:
            try:
                conn.sendall(message.encode())
            except Exception as e:
                print(f"Error sending message to client {client_id}: {e}")

def response(message, sender_id):
    """Send the message back to a client."""
    try:
        clients[sender_id].sendall(message.encode())
    except Exception as e:
        print(f"Error sending message to client {sender_id}: {e}")

def handle_client(conn, addr, client_id):
    try:
        print(f"Connected by {addr} with client ID {client_id}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            message = data.decode()
            #print(f"Received from client {client_id}: {message}")
            handle_message(message, client_id)
            #broadcast(f"Message from client {client_id}: {message}", client_id)
    except Exception as e:
        print(f"Error handling client {client_id}: {e}")
    finally:
        conn.close()
        del clients[client_id]
        print(f"Client {client_id} disconnected")

def run_Loop( delta_time):
    global interval
    global beatPos
    global barPos
    global tick
    global elapsedTime
    elapsedTime += delta_time
    while elapsedTime >= interval:
        elapsedTime -= interval
        tick += 1
        if (barPos * (tickRes * maxBeat) + beatPos * tickRes + tick) % quant == 0:
            for q in quantEvents:
                q()
            quantEvents.clear()
        while tick >= tickRes:
            tick -= tickRes
            beatPos += 1
            while beatPos >= maxBeat:
                beatPos -= maxBeat
                barPos += 1
                while barPos >= maxBar:
                    barPos -= maxBar
                changeChord(barPos)       
    

# Callback function
def callback(in_data, frame_count, time_info, status):
    global cs
    global cnt
    deltaTime = float(frame_count) / sr
    run_Loop(deltaTime)
    end = cs.ksmps()

    spout = cs.spout()
    

    data = np.zeros(frame_count * 2, dtype=np.float32)

    for i in range(frame_count):
        if cnt ==0:
            result = cs.performKsmps()
            if result != 0:
                return (None, pyaudio.paComplete)
        data[i * 2] = np.float32(spout[cnt])  # Left channel
        data[i * 2 + 1] = np.float32(spout[cnt + 1])  # Right channel
        cnt = (cnt+2)% (end*2)

    dataB = data.tobytes()
    return (dataB, pyaudio.paContinue)




def main():
    host = '127.0.0.1'
    port = 65432
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    print("Server is listening")
    

    csd_text = '''
        <CsoundSynthesizer>
        <CsOptions>
            --messagelevel=0 --m-range=1 --m-warnings=1
        </CsOptions>
        <CsInstruments>
            sr = 44100
            ksamps = 32
            0dbfs = 1
            nchnls = 2

            instr 3
                aout poscil p5, cpsmidinn(p4)
                aout linen aout, 0.001, p3, p3/3
                out aout,aout
            endin

        </CsInstruments>
        <CsScore>
        
        </CsScore>
        </CsoundSynthesizer>'''
    result = cs.setOption("-d")
    result = cs.setOption("-n")
    result = cs.compileCsdText(csd_text)
    result = cs.start()
    result = cs.compileOrc(f"gil1001 init 2")
    
    orc = """
    instr 1001
                aout poscil p5, cpsmidinn(p4)
                aout linen aout, 0.001, p3, p3/3
                out aout,aout
                if gil1001 == 1 then
                schedule(1004, 1.0 * (60/120), p3, p4, p5)
                endif
                endin
    """
    result = cs.compileOrc(orc) #this part is necessary to avoid Segmentation fault

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open stream
    stream = p.open(format=pyaudio.paFloat32,
                    channels=2,
                    rate=RATE,
                    output=True,
                    stream_callback=callback)

    # Start the stream
    stream.start_stream()


    eventArrayInit()

    cs.setControlChannel('bpm',bpm)
    orc = """
        gi_Ion_Arr[] fillarray 0, 2, 4, 5, 7, 9, 11
        gi_Dor_Arr[] fillarray 0, 2, 3, 5, 7, 9, 10
        gi_Phr_Arr[] fillarray 0, 1, 3, 5, 7, 8, 10
        gi_Lyd_Arr[] fillarray 0, 2, 4, 6, 7, 9, 11
        gi_Mix_Arr[] fillarray 0, 2, 4, 5, 7, 9, 10
        gi_Aeo_Arr[] fillarray 0, 2, 3, 5, 7, 8, 10
        gi_Loc_Arr[] fillarray 0, 1, 3, 5, 6, 8, 10

        gi_Alt_Arr[] fillarray 0, 1, 4, 5, 7, 8, 10

        giKey = 0
        giChord = 0
        giChordMode = 0

        opcode getScale, i,ii
            iMode,iIndex xin
            iOut = 0
            if iMode == 0 then
                iOut = gi_Ion_Arr[iIndex]
            elseif iMode == 1 then
                iOut = gi_Dor_Arr[iIndex]
            elseif iMode == 2 then
                iOut = gi_Phr_Arr[iIndex]
            elseif iMode == 3 then
                iOut = gi_Lyd_Arr[iIndex]
            elseif iMode == 4 then
                iOut = gi_Mix_Arr[iIndex]
            elseif iMode == 5 then
                iOut = gi_Aeo_Arr[iIndex]
            elseif iMode == 6 then
                iOut = gi_Loc_Arr[iIndex]
            elseif iMode == 7 then
                iOut = gi_Alt_Arr[iIndex]
            else
                iOut = gi_Ion_Arr[iIndex]
            endif
            
            xout iOut
            
        endop
    """
    cs.compileOrc(orc)
    client_id = 0
    while True:
        conn, addr = server.accept()
        clients[client_id] = conn  # Store the connection
        thread = threading.Thread(target=handle_client, args=(conn, addr, client_id))
        thread.start()
        client_id += 1

if __name__ == '__main__':
    main()