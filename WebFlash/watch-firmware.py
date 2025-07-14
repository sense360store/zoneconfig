#!/usr/bin/env python3
"""
Firmware Directory Watcher
==========================

Automatically runs automation when firmware files are added or removed.
Perfect for development workflow.

Usage:
  python3 watch-firmware.py        # Watch for changes and auto-update
  python3 watch-firmware.py --once # Run once and exit
"""

import os
import time
import argparse
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FirmwareWatcher(FileSystemEventHandler):
    def __init__(self, auto_run=True):
        self.auto_run = auto_run
        self.last_run = 0
        self.debounce_time = 2  # seconds
        
    def on_any_event(self, event):
        if event.is_directory:
            return
            
        # Only watch .bin files
        if not event.src_path.endswith('.bin'):
            return
            
        # Debounce multiple events
        current_time = time.time()
        if current_time - self.last_run < self.debounce_time:
            return
            
        self.last_run = current_time
        
        print(f"Firmware change detected: {event.event_type} - {event.src_path}")
        
        if self.auto_run:
            self.run_automation()
    
    def run_automation(self):
        """Run the deployment automation."""
        try:
            print("Running automation...")
            result = subprocess.run(['python3', 'deploy-automation.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Automation completed successfully")
            else:
                print(f"✗ Automation failed: {result.stderr}")
                
        except Exception as e:
            print(f"✗ Error running automation: {e}")

def main():
    parser = argparse.ArgumentParser(description='Watch firmware directory for changes')
    parser.add_argument('--once', action='store_true', help='Run automation once and exit')
    
    args = parser.parse_args()
    
    # Change to WebFlash directory
    os.chdir(Path(__file__).parent)
    
    if args.once:
        # Run automation once
        watcher = FirmwareWatcher(auto_run=False)
        watcher.run_automation()
        return
    
    # Watch for changes
    firmware_dir = Path('firmware')
    if not firmware_dir.exists():
        print(f"Creating firmware directory: {firmware_dir}")
        firmware_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Watching firmware directory: {firmware_dir.absolute()}")
    print("Add or remove .bin files to trigger automation...")
    print("Press Ctrl+C to stop")
    
    event_handler = FirmwareWatcher()
    observer = Observer()
    observer.schedule(event_handler, str(firmware_dir), recursive=True)
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nWatcher stopped")
    
    observer.join()

if __name__ == '__main__':
    main()