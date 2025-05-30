import time, os, random, serial, subprocess
import RPi.GPIO as GPIO

# ───────── USER SETTINGS ───────────────────────────────────────────
DETECT_CM        = 5            # Distance to count as ball in hole
CONSEC_HITS_N    = 2            # Hits under threshold to trigger
COOLDOWN_SEC     = 5            # Debounce to avoid retriggers
CELEBRATION_SEC  = 10           # How long the celebration lasts
AUDIO_DIR        = '/home/TestPi/golf_sounds'  # Folder with .wav files
LOG_FILE         = '/home/TestPi/golf.log'
PICO_SERIAL_PORT = '/dev/ttyACM0'              # USB serial port to Pico
PICO_BAUDRATE    = 115200
# -------------------------------------------------------------------

# ───────── LOGGING ─────────────────────────────────────────────────
def log_event(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} - {msg}\n")

# ───────── AUDIO ───────────────────────────────────────────────────
def play_random_sound():
    try:
        clips = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]
        if not clips:
            log_event("⚠️ No .wav files found in audio directory.")
            return
        chosen = random.choice(clips)
        full_path = os.path.join(AUDIO_DIR, chosen)
        log_event(f"🔊 Playing sound: {full_path}")
        subprocess.run(
            f"aplay '{full_path}'",
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ
        )
    except Exception as e:
        log_event(f"❌ Error playing sound: {e}")

# ───────── SENSOR SETUP ────────────────────────────────────────────
TRIG, ECHO = 23, 19
GPIO.setwarnings(False)
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
    log_event(f"✅ Connected to Pico at {PICO_SERIAL_PORT}")
except Exception as e:
    log_event(f"❌ Could not connect to Pico: {e}")
    pico = None

def send_to_pico(message):
    if pico and pico.is_open:
        try:
            pico.write(f"{message.strip()}\n".encode())
            log_event(f"📤 Sent to Pico: {message.strip()}")
        except Exception as e:
            log_event(f"⚠️ Error writing to Pico: {e}")
    else:
        log_event("⚠️ Pico serial not open")

# ───────── MAIN LOOP ───────────────────────────────────────────────
log_event(f"🎯 System initialized. Waiting for {CONSEC_HITS_N} hits < {DETECT_CM} cm.")
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
            msg = f"🎉 Ball detected at {dist:.1f} cm! Triggering celebration."
            print(f"\n{msg}")
            log_event(msg)
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
    log_event("🔚 System shut down via keyboard interrupt.")
    print("\n🔚 Exiting cleanly.")
