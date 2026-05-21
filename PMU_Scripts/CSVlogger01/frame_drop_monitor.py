"""
Made for Bachelor's Thesis Implementation by Haron Akram Ahmed Mohammed 2026
Email: haamo@kth.se
"""

import UDPphasor as UDP
import signal
import sys
import threading

print("--- OpenPMU Frame Drop Monitor ---")

# Load configuration dynamically
with open(os.path.join(os.path.dirname(__file__), "config.json")) as j:
    config = json.load(j)
    IP = config["recvIP"]
    PHASOR_PORT = config["recvPort"]
    SV_PORT = 48501 # The standard raw ADC port

print(f"Listening for Phasors on {IP}:{PHASOR_PORT}")
print(f"Listening for Raw SV on {IP}:{SV_PORT}\n")

udp_phasor = UDP.Receiver(IP, PHASOR_PORT)
udp_SV = UDP.Receiver(IP, SV_PORT)

def phasor_check(last_frame):
    dataInfo = udp_phasor.receive()
    # If there's no frame of data, skip rest of loop and wait for next frame.
    if dataInfo is None:
        return last_frame
    
    new_frame = int(dataInfo["Frame"]) // 2
    expected_frame = (last_frame + 1) % 50
    if new_frame != expected_frame and last_frame != 0:
        print(f"[WARNING] Phasor Frame Dropped! Jumped from {last_frame} to {new_frame} at {dataInfo['Time']}")
    return new_frame


def sv_check(last_frame):
    dataInfo = udp_SV.receive()
    # If there's no frame of data, skip rest of loop and wait for next frame.
    if dataInfo is None:
        return last_frame

    new_frame = int(dataInfo["Frame"])
    expected_frame = (last_frame + 1) % 100
    
    if new_frame != expected_frame and last_frame != 0:
        print(f"[WARNING] Raw SV Frame Dropped! Jumped from {last_frame} to {new_frame} at {dataInfo['Time']}")
    return new_frame

def loop(func):
    last_frame = 0
    while True:
        last_frame = func(last_frame)

t = threading.Thread(target=loop, args=(phasor_check,))
t.start()

t2 = threading.Thread(target=loop, args=(sv_check,))
t2.start()

input()
