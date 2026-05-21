"""
OpenPMU - CPU Performance Logger
Copyright (C) 2021  www.OpenPMU.org
Made for Bachelor's Thesis Implementation by Haron Akram Ahmed Mohammed 2026
Email: haamo@kth.se
"""

import os
import time
import shutil
import subprocess
import json
from datetime import datetime, timedelta

class PerformanceMonitor:
    def __init__(self, config_path="config.json"):
        # Load configuration
        with open(config_path) as f:
            self.config = json.load(f)
            
        self.log_root = self.config["logPathRoot"]
        self.interval = self.config["logInterval"]
        self.targets = self.config["targets"]
        
        # Track the current day to handle midnight rollovers
        self.current_date_str = None
        self.current_file_path = None
        
        print("Initializing Dual-Engine CPU Performance Monitor...")

    def ensure_directory(self, file_path):
        """Creates the necessary directories if they do not exist."""
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def deleteOldRecords(self, folderPath, daysToKeep, currentTime):
        """ Deletes CSV files older than daysToKeep (Specific to CPUlogger file structure) """
        thresholdDate = currentTime - timedelta(days=daysToKeep)
        
        if os.path.exists(folderPath):
            for filename in os.listdir(folderPath):
                file_path = os.path.join(folderPath, filename)
                # Check if it is a file and ends with .csv
                if os.path.isfile(file_path) and filename.endswith(".csv"):
                    try:
                        # Reconstruct the datetime from the filename (e.g. 2026-05-19.csv)
                        fileDateStr = filename.replace(".csv", "")
                        fileDate = datetime.strptime(fileDateStr, "%Y-%m-%d")
                        if fileDate.date() < thresholdDate.date():
                            print(f"\nDeleting old performance log: {file_path}")
                            os.remove(file_path)
                    except ValueError:
                        pass # Ignore files that aren't properly named dates

    def update_log_file(self, now):
        """Checks if a new day has started, and creates a new CSV file if necessary."""
        date_str = now.strftime("%Y-%m-%d")
        
        # If it is a new day (or the script just started)
        if date_str != self.current_date_str:
            self.current_date_str = date_str
            file_name = f"{date_str}.csv"
            self.current_file_path = os.path.join(self.log_root, file_name)
            
            self.ensure_directory(self.current_file_path)
            
            if self.config.get("allowDeletion", False):
                print(f"\nChecking for records older than {self.config['daysToKeep']} days...")
                self.deleteOldRecords(self.log_root, self.config["daysToKeep"], now)
            
            # Write headers if the file is brand new
            if not os.path.exists(self.current_file_path):
                with open(self.current_file_path, 'w') as f:
                    # Dynamically create headers based on targets in config.json
                    headers = "Date,Time," + ",".join([f"{name}(%)" for name in self.targets.keys()])
                    f.write(headers + "\n")
            
            print(f"\n[+] Now logging to: {self.current_file_path}")
            print(f"Monitoring overhead every {self.interval} seconds. Press Ctrl+C to stop.\n")
            
            # Print the static terminal table header
            target_names = list(self.targets.keys())
            header_str = f"{'Time':<10} | " + " | ".join([f"{name:<10}" for name in target_names])
            print(header_str)
            print("-" * len(header_str))

    def get_cpu_usage(self, identifier):
        """
        Hunts specifically for the raw python3 engine, ignoring the sudo wrapper.
        identifier: The folder name (e.g., 'PhasorEst01')
        """
        try:
            # Find the PIDs of ALL active python3 processes
            cmd_pids = "pgrep python3"
            pids = subprocess.check_output(cmd_pids, shell=True, text=True).strip().split('\n')
        except subprocess.CalledProcessError:
            return 0.0 # Return 0 if absolutely no python3 processes exist
            
        total_cpu = 0.0
        for pid in pids:
            if not pid: continue
            
            try:
                # Inspect the background memory to see exactly which folder this python3 script is in
                cmd_pwdx = f"sudo pwdx {pid}"
                # Redirect stderr to DEVNULL so it doesn't spam the terminal if a process dies
                pwdx_out = subprocess.check_output(cmd_pwdx, shell=True, text=True, stderr=subprocess.DEVNULL)
                
                if identifier in pwdx_out:
                    # If the folder matches, grab the raw CPU % and add it up!
                    cmd_cpu = f"ps -p {pid} -o %cpu="
                    cpu_out = subprocess.check_output(cmd_cpu, shell=True, text=True).strip()
                    if cpu_out:
                        total_cpu += float(cpu_out)
            except subprocess.CalledProcessError:
                # If a background process dies right before we check it, 
                # just skip it and keep checking the rest!
                continue
                
        # Normalize for Raspberry Pi 3B/4 (Quad-Core = 400% max)
        return total_cpu / 4.0

    def run(self):
        """Main logging loop."""
        
        while True:
            try:
                now = datetime.now()
                self.update_log_file(now)
                
                time_str = now.strftime("%H:%M:%S")
                date_str = now.strftime("%Y-%m-%d")
                
                # Fetch CPU usage for all targeted algorithms
                cpu_results = []
                for name, identifier in self.targets.items():
                    usage = self.get_cpu_usage(identifier)
                    cpu_results.append(f"{usage:.1f}")
                
                # Build and write the CSV line
                log_line = f"{date_str},{time_str}," + ",".join(cpu_results) + "\n"
                
                with open(self.current_file_path, 'a') as f:
                    f.write(log_line)
                
                # Live Terminal Output
                # \r sends the cursor to the beginning of the line.
                # end="" prevents Python from jumping to the next line.
                # flush=True forces the terminal to draw the text immediately.
                row_str = f"{time_str:<10} | " + " | ".join([f"{res + '%':<10}" for res in cpu_results])
                print(f"\r{row_str}", end="", flush=True)
                    
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                # Add a few newlines so we don't overwrite the final data point when exiting
                print("\n\nLogging safely stopped by user.")
                break
            except Exception as e:
                # Clear the line and print the error
                print(f"\rNon-fatal logging error: {e}")
                time.sleep(self.interval)

if __name__ == '__main__':
    monitor = PerformanceMonitor()
    monitor.run()