# OpenPMU-KTH
Code repository for the revised OpenPMU-project from KTH. 

**2026 Revision:** Modified by Haron Akram Ahmed Mohammed (Bachelor's Thesis) to include a dual-engine estimation architecture. The system now runs the baseline time-domain Least Squares Method (LSM) simultaneously with a highly optimized, cross-language (C++) frequency-domain Enhanced Interpolated DFT (e-IpDFT).

## 1. Setup Guide
1) Flash microSD card with Raspberry Pi OS Lite (tested with Bullseye).
   Use Raspberry Pi Imager to configure the following:
    - Change hostname to `OpenPMU-KTH-XYZ` where XYZ is your unique 3-digit ID number.
    - Enable SSH, with the option *Use password authentication*
    - Change password to your unique password
    - Change locale to `Europe/Stockholm`

2) Mount USB drive (for logging SV/phasor/performance data):
    - `lsblk -fp`  (Note down UUID of USB drive, usually of format AB12-34CD)
    - `sudo nano /etc/fstab`
    - Add this line at the end:
      `UUID=AB12-34CD /mnt/usb0 vfat defaults,auto,users,rw,nofail,umask=000 0 0`
    - The USB drive will mount at `/mnt/usb0` on reboot.
    *Note: The logger scripts are hardcoded to automatically delete data older than 30 days to protect this USB drive from overflowing.*

3) Clone the content of this git repository to `/home/pi/OpenPMU-KTH/`

4) Run the setup script to install dependencies and the C++ compiler:
    ```shell
    cd /home/pi/OpenPMU-KTH
    chmod +x setup.sh
    ./setup.sh
    ```

5) **Important C++ Compilation:** Navigate into the `PhasorEst02` directory and compile the `libEnhancedIpDFT.so` shared library using `g++`. The Python ctypes wrapper will fail to run if this library is missing.

## 2. Configurations & Network Streams
This PMU runs two algorithms simultaneously. If you want to change configurations, edit the `config.json` file inside each respective module folder.

* **LSM Stream:** Uses `Telecom01` (Port 4711, IDCODE 101).
* **e-IpDFT Stream:** Uses `Telecom02` (Port 4712, IDCODE 102).

**Modifying Startup:**
- Edit the file `/home/pi/OpenPMU-KTH/launchOpenPMU-KTHcron`.
- Comment out any module you don't want to start with a `#`.
- Copy the edited file: `sudo cp launchOpenPMU-KTHcron /etc/cron.d/`

## 3. Monitoring
There are now 9 active modules running in the background. To see which screens are running, use:
```shell
screen -ls
```
That should give an output similar to:
```shell
There are screens on:
        100.SVtoWave     (Detached)
        101.PhasorEst01  (Detached)
        102.PhasorEst02  (Detached)
        103.MulticastSV  (Detached)
        104.CSVlogger01  (Detached)
        105.CSVlogger02  (Detached)
        106.Telecom01    (Detached)
        107.Telecom02    (Detached)
        108.CPULogger    (Detached)
9 Sockets in /run/screen/S-pi.
```
To look at (attach to) one of the running screens, use the screens ID code when running the command:
```shell
screen -x 494
```
This example would show the telecom screen.

To deattach from the screen you are looking at, press CTRL+A and then press D.