from gpiozero import Button
from subprocess import Popen
from signal import pause
import time
import os
import sys

# --- Configuration ---
# Use the GPIO pin your button is connected to
BUTTON_PIN = 17 

# --- Global variables to keep track of the running scripts ---
cam_process = None
audio_process = None
button_press_count = 0
streams_initialized = False

# --- Define the button ---
button = Button(BUTTON_PIN)

def handle_button_press():
    """Smart button handler - different actions for different presses"""
    global cam_process, audio_process, button_press_count, streams_initialized

    button_press_count += 1
    print(f"\n🔘 Button press #{button_press_count}")

    if not streams_initialized:
        # FIRST PRESS: Start streams
        print("🚀 FIRST PRESS: Starting camera and audio streams...")
        print("=" * 50)
        
        try:
            # Launch the scripts as new, independent processes
            cam_process = Popen(['python3', 'usb_cam_stream.py'])
            audio_process = Popen(['python3', 'audio_only.py'])
            
            # Wait a moment for streams to initialize
            time.sleep(3)
            
            streams_initialized = True
            print("✅ Streams started successfully!")
            print("📹 Video stream: http://143.215.189.141:5000/video_feed")
            print("🎤 Audio stream: http://143.215.189.141:5001/audio_feed")
            print("🔘 Press button again to start Wingman AI analysis")
            
        except Exception as e:
            print(f"❌ Failed to start streams: {e}")
            streams_initialized = False
    
    else:
        # SUBSEQUENT PRESSES: Start Wingman AI
        print("🤖 STARTING WINGMAN AI ANALYSIS...")
        print("=" * 50)
        
        try:
            # Tell laptop to start wingman via HTTP
            import requests
            laptop_ip = "10.90.245.140"  # Your laptop IP
            url = f"http://{laptop_ip}:5555/start_wingman"
            
            print("🧠 Telling laptop to start wingman...")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print("✅ Wingman started on laptop!")
                print("🎯 Listen for wingman advice!")
            else:
                print(f"❌ Laptop responded with error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Can't reach laptop: {e}")
            print("💡 Make sure laptop server is running")
    
    # Prevent accidental double-presses
    time.sleep(2)

def cleanup_and_exit():
    """Clean shutdown of all processes"""
    global cam_process, audio_process
    
    print("\n🧹 Cleaning up processes...")
    
    if cam_process:
        cam_process.terminate()
        cam_process = None
    
    if audio_process:
        audio_process.terminate()
        audio_process = None
        
    print("✅ Cleanup complete")

# --- Link the function to the button press ---
print("🎮 SMART BUTTON CONTROLLER")
print("=" * 40)
print(f"📍 Button on GPIO {BUTTON_PIN}")
print("🔘 First press: Start streams")
print("🔘 Subsequent presses: Start Wingman AI")
print("=" * 40)
print("⏳ Ready for button press...")

button.when_pressed = handle_button_press

# Handle cleanup on exit
import signal
import atexit

atexit.register(cleanup_and_exit)
signal.signal(signal.SIGINT, lambda s, f: (cleanup_and_exit(), exit(0)))

# Keep the script running to listen for button presses
pause()