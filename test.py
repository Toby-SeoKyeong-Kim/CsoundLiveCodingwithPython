import sys
import ctcsound
import numpy as np
import pyaudio
import threading

cs = ctcsound.Csound()

# Parameters
RATE = 44100  # Sample rate (Hz)
INITIAL_FREQUENCY = 440.0  # Initial frequency of the sine wave (Hz)
DURATION = 0.1  # Duration of each chunk in seconds

# Shared variables
frequency = INITIAL_FREQUENCY
frequency_lock = threading.Lock()
cnt = 0

# Callback function
def callback(in_data, frame_count, time_info, status):
    global cs
    global cnt
    end = cs.ksmps()
    # Use the NumPy array returned by cs.spout()
    spout = cs.spout()
    
    # Ensure spout array has the expected size
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

csd_text = '''
  <CsoundSynthesizer>
  <CsOptions>
    
  </CsOptions>
  <CsInstruments>
    sr = 44100
    ksamps = 32
    0dbfs = 1
    nchnls = 2
  instr 1
    aout oscili p4, p5
    aout linen aout,0.1,p3,0.1
    outs aout, aout
  endin
  </CsInstruments>
  <CsScore>

  </CsScore>
  </CsoundSynthesizer>'''


result = cs.setOption("-n")
result = cs.compileCsdText(csd_text)
result = cs.start()

orc = """
instr 2
    aout vco2 p4, p5
    aout linen aout,0.1,p3,0.1
    outs aout, aout
endin
"""
result = cs.compileOrc(orc)

result = cs.compileOrc(f"gil1004 init 1")
orc = """
instr 1004
            aout poscil p5, cpsmidinn(p4)
            aout linen aout, 0.001, p3, p3/3
            out aout,aout
            if gil1004 == 1 then
            schedule(1004, 1.0 * (60/120), p3, p4, p5)
            endif
            endin
"""
result = cs.compileOrc(orc)

result = cs.compileOrc("schedule(1005, 0, .25, 60, .5)")
#result = cs.inputMessage("i 2 0 3 .5 600")

cs.compileOrc(f"gi_Arr[] fillarray 1,2,3,4")
cs.compileOrc(f"gil2 init 1")
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

# Example main thread interaction
try:
    while stream.is_active():
        # Change frequency from the main thread for demonstration
        new_freq = float(input("Enter new frequency: "))

except KeyboardInterrupt:
    pass

# Stop and close the stream
stream.stop_stream()
stream.close()

# Terminate PyAudio
p.terminate()



# while True:
#     result = cs.performKsmps()
#     if result != 0:
#         break

result = cs.cleanup()
cs.reset()
del cs
sys.exit(result)