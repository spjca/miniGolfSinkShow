import time, os, random, serial, subprocess
import RPi.GPIO as GPIO

# ───────── USER SETTINGS ───────────────────────────────────────────
DETECT_CM        = 5          # Distance to count as ball in hole
CONSEC_HITS_N    = 2          # Hits under threshold to trigger
COOLDOWN_SEC     = 5          # Debounce to avoid retriggers
CELEBRATION_SEC  = 10         # How long the celebration lasts
AUDIO_DIR        = '/home/TestPi/golf_sounds'  # Folder with .wav files
PICO_SERIAL_PORT = '/dev/ttyACM0'              # USB serial port to Pico
PICO_BAUDRATE    = 115200
# -------------------------------------------------------------------

# ───────── AUDIO ───────────────────────────────────────────────────
def play_random_sound():
    try:
        clips = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]
        if not clips:
            print(f"⚠️ No .wav files found in {AUDIO_DIR}")
            return
        chosen = random.choice(clips)
        full_path = os.path.join(AUDIO_DIR, chosen)
        print(f"🔊 Playing via shell: {full_path}")

        command = f"aplay '{full_path}'"
        result = subprocess.run(
            command,
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ  # inherit full environment including XDG_RUNTIME_DIR
        )

        if result.returncode != 0:
            print(f"⚠️ aplay error:\n{result.stderr}")
        else:
            print("✅ aplay playback succeeded.")

    except Exception as e:
        print(f"⚠️ Exception during sound playback: {e}")



# ───────── SENSOR SETUP ────────────────────────────────────────────
TRIG, ECHO = 23, 19
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance_cm(timeout=0.05):
    GPIO.output(TRIG, False)
    time.sleep(0.05)
    GPIO.output(TRIG, True); time.sleep(1e-5); GPIO.output(TRIG, False)

    t0 = time.time()
    while GPIO.input(ECHO) == 0:
        if time.time() - t0 > timeout: return None
    start = time.time()
    while GPIO.input(ECHO) == 1:
        if time.time() - start > timeout: return None
    return (time.time() - start) * 17150

# ───────── PICO SERIAL SETUP ───────────────────────────────────────
try:
    pico = serial.Serial(PICO_SERIAL_PORT, PICO_BAUDRATE, timeout=1)
    print(f"✅ Connected to Pico at {PICO_SERIAL_PORT}")
except Exception as e:
    print(f"❌ Could not connect to Pico: {e}")
    pico = None

def send_to_pico(message):
    if pico and pico.is_open:
        try:
            pico.write(f"{message.strip()}\n".encode())
            print(f"📤 Sent to Pico: {message.strip()}")
        except Exception as e:
            print(f"⚠️ Error writing to Pico: {e}")
    else:
        print("⚠️ Pico serial not open")

# ───────── MAIN LOOP ───────────────────────────────────────────────
print(f"🎯 System ready. Need {CONSEC_HITS_N} hits < {DETECT_CM} cm.")
send_to_pico("idle")
last_celebration = 0
hit_streak = 0

try:
    while True:
        dist = get_distance_cm()
        valid = dist is not None and 1 < dist < 400
        txt = "None" if dist is None else f"{dist:5.1f} cm"
        print(txt, end="\r")

        now = time.time()
        if valid and dist < DETECT_CM:
            hit_streak += 1
        else:
            hit_streak = 0

        if hit_streak >= CONSEC_HITS_N and now - last_celebration > COOLDOWN_SEC:
            print(f"\n🎉 Ball detected at {dist:.1f} cm! Celebrating.")
            send_to_pico("celebrate")
            play_random_sound()
            time.sleep(CELEBRATION_SEC)
            send_to_pico("idle")
            last_celebration = time.time()
            hit_streak = 0

        time.sleep(0.05)

except KeyboardInterrupt:
    GPIO.cleanup()
    if pico and pico.is_open:
        send_to_pico("off")
        pico.close()
    print("\n🔚 Exiting cleanly.")
