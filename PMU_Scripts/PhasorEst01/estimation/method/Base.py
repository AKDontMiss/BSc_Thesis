from __future__ import print_function
import numpy as np
import threading
from ..interface.PMU import Receiver
from ..interface.UDP import Sender
import time as timezone

class EstimationMethodBase:
    def __init__(self, ):
        pass
    def getPhasor(self, samples):
        pass

class EstimatorBase:
    def __init__(self, receiveIP, receivePort, sendIP, sendPort):
        self.estimationFrequency = 50  
        self.receiveIP = receiveIP
        self.receivePort = receivePort
        self.sendIP = sendIP
        self.sendPort = sendPort

        self.estimationThread = threading.Thread(target=self.run)
        self.estimationThread.daemon = True
        self.runThreadEvent = threading.Event()

    def oneChannelDone(self, date, time, chNo, mag, frequency, angle, rocof):
        """ Formats and prints the calculated data for the terminal display """
        d = f"{str(date).strip():<12}"
        t = f"{str(time).strip():<15}"
        c = f"{str(chNo).strip():<8}"
        m = f"{mag:<12.4f}"
        f = f"{frequency:<10.2f}"
        a = f"{angle:<10.2f}"
        r = f"{rocof:<8.2f}"
        print(f" {d} | {t} | {c} | {m} | {f} | {a} | {r}")
        if chNo == 2:
            print("")

    def stop(self, ):
        self.runThreadEvent.clear()
        self.estimationThread.join()

    def start(self, ):
        self.runThreadEvent.set()
        if not self.estimationThread.is_alive():
            self.estimationThread = threading.Thread(target=self.run)
            self.estimationThread.start()

    def run(self, ):
        timeout = 1
        
        # We use a Multicast IP (239.16.1.102), so the OS natively duplicates 
        # the UDP packets for both algorithms. forward=False is correct here.
        pmuReceiver = Receiver(self.receiveIP, self.receivePort, False)
       
        # Setup Dual Dispatch: Send to Telecom and to local CSV Logger
        sender_telecom = Sender("127.0.0.1", self.sendPort)
        sender_csv = Sender("127.0.0.1", self.sendPort + 100)

        chEstimation = None
        payloadDataBuffer = None
        dataCnt = 0

        # Pre-allocate XML metadata to save CPU in the fast loop
        lsm_meta = [
            {"Name": "eIpDFT_Va", "Type": "V", "Phase": "a", "Range": "275"},
            {"Name": "eIpDFT_Vb", "Type": "V", "Phase": "b", "Range": "275"},
            {"Name": "eIpDFT_Vc", "Type": "V", "Phase": "c", "Range": "275"}
        ]
        
        while self.runThreadEvent.isSet():
            try:
                # Grab raw BeagleBone data
                phasor = pmuReceiver.receive(timeout)
                if phasor is None:
                    continue

                # PURE 3-CHANNEL ENFORCEMENT 
                # To prevent network bloating and keep the stream strictly compliant,
                # we delete any floating or unused channels above Phase C.
                for dead_ch in range(3, 10):
                    dead_key = 'Channel_%d' % dead_ch
                    if dead_key in phasor:
                        del phasor[dead_key]
               
                # Lock the pipeline strictly to 3 channels (Va, Vb, Vc)
                phasor["Channels"] = 3
                chNo = 3

                Fs = phasor["Fs"]
                n = phasor['n']
                date = phasor["Date"]
                time = phasor["Time"]
                frame = phasor["Frame"]
                interval = phasor['n'] * 1000.0 / phasor['Fs']
                recNo = int(1000.0 / self.estimationFrequency / interval)

                # Initialize the math engine if this is the first frame
                if chEstimation is None:
                    chEstimation = []
                    for i in range(chNo):
                        chEstimation.append(self.estimationMethod(Fs, n * recNo))
                    payloadDataBuffer = np.zeros([chNo, n * recNo])

                    # EMA FILTER MEMORY
                    freq_prev_smoothed = [50.0, 50.0, 50.0]  # Memory for 3 channels
                    is_first_frame = True                    # Startup trigger

                    continue

                if frame == 0:
                    dataCnt = 1

                # Extract payloads for the active channels
                for i in range(0, chNo):
                    k = 'Channel_%d' % i
                    try:
                        payloadDataBuffer[i, dataCnt * n:(dataCnt * n + n)] = (phasor[k]['Payload'])
                        del phasor[k]['Payload']
                    except KeyError:
                        pass # Silently ignore missing payloads to prevent crashing

                dataCnt += 1
                                                                   
                # Wait until we have enough samples to perform estimation
                if dataCnt >= recNo:
                    dataCnt = 0
                    for i in range(0, chNo):
                        try:
                            # PACKET DROP DETECTOR (LSM SAFETY NET) 
                            if np.max(np.abs(np.diff(payloadDataBuffer[i,]))) > 0.3:
                                raise IndexError("UDP Drop Discontinuity Detected!")
                                
                            # Run the math engine and calibrate scale
                            mag, frequency, angle, rocof = chEstimation[i].getPhasor(payloadDataBuffer[i,])
                            mag = mag * 115.5

                            # POST-PROCESSING LOW-PASS FILTER (EMA)
                            if is_first_frame:
                                freq_prev_smoothed[i] = frequency
                                
                            # Apply the exact same alpha=0.05 filter used in e-IpDFT
                            alpha = 0.05
                            freq_prev_smoothed[i] = (alpha * frequency) + ((1.0 - alpha) * freq_prev_smoothed[i])
                            
                            # Override the raw frequency with the smoothed frequency
                            frequency = freq_prev_smoothed[i]

                        except IndexError as e:
                            # Fallback to defaults if buffer errors out
                            frequency, angle, mag, rocof = 50.0, 0.0, 0.0, 0.0
                            is_first_frame = True  # Reset filter memory on recovery
                           
                        k = 'Channel_%d' % i
                        phasor[k]["Freq"] = frequency
                        phasor[k]["Angle"] = angle
                        phasor[k]["Mag"] = mag
                        phasor[k]["ROCOF"] = rocof

                        # Ultra-fast dictionary injection
                        phasor[k].update(lsm_meta[i])
                        
                        # XML METADATA INJECTION (LSM)
                        # Because we stripped the XML to a clean 3-channel layout, we must 
                        # dynamically inject the names so the XML builder doesn't throw a KeyError.
                        phase_letters = ["a", "b", "c"]
                        phasor[k]["Name"] = "LSM" 
                        phasor[k]["Type"] = "V"
                        phasor[k]["Phase"] = phase_letters[i]
                        phasor[k]["Range"] = "275"
                       
                        # Output results to terminal
                        self.oneChannelDone(date, time, i, mag, frequency, angle, rocof)

                    # Turn off the startup trigger after all 3 channels have initialized
                    is_first_frame = False
                    
                    # Dispatch the finalized data packet to the networking scripts
                    sender_telecom.send(phasor)
                    sender_csv.send(phasor)
           
            except KeyboardInterrupt:
                self.stop()

        pmuReceiver.close()