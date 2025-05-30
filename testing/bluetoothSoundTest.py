import subprocess
import time
import pygame
import os

BT_MAC = "FC:58:FA:D7:0B:82"
SINK_NAME = "bluez_sink.FC_58_FA_D7_0B_82.a2dp_sink"
LOG = "/home/TestPi/bluetooth_audio.log"
CLAP_SOUND = "/home/TestPi/golf_sounds/clap.wav"

def log(msg):
    with open(LOG, "a") as f:
        f.write(f"{time.ctime()} - {msg}\n")
    print(msg)

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Step 1: Restart pulseaudio (safe even if already running)
run_cmd("pulseaudio -k")
time.sleep(1)
run_cmd("pulseaudio --start")
time.sleep(2)

# Step 2: Check connection status
info = run_cmd(f"bluetoothctl info {BT_MAC}").stdout
if "Connected: yes" in info:
    log("🔗 Already connected to Bluetooth speaker.")
else:
    bt_script = f"connect {BT_MAC}\ntrust {BT_MAC}\nexit\n"
    run_cmd(f"echo -e \"{bt_script}\" | bluetoothctl")
    log("🔌 Bluetooth connection attempted.")
    time.sleep(3)

# Step 3: Wait for sink to become available (even if already connected)
log("🔍 Looking for audio sink...")
sink_found = False
for i in range(10):
    sinks = run_cmd("pactl list short sinks").stdout
    if SINK_NAME in sinks:
        log(f"🔊 Sink found on attempt {i+1}: {SINK_NAME}")
        run_cmd(f"pactl set-default-sink {SINK_NAME}")
        sink_found = True
        break
    time.sleep(1)

if not sink_found:
    log("❌ Sink not found after retries. Aborting.")
    exit(1)


# Step 4: Play sound
try:
    pygame.mixer.init()
    pygame.mixer.music.load(CLAP_SOUND)
    pygame.mixer.music.play()
    log("✅ Played sound successfully.")
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
except Exception as e:
    log(f"❌ Sound playback failed: {e}")
