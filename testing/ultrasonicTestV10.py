import time, os, random, serial
import RPi.GPIO as GPIO
import pygame

# ───────── USER SETTINGS ───────────────────────────────────────────
DETECT_CM        = 5          # Distance to count as ball in hole
CONSEC_HITS_N    = 2          # Hits under threshold to trigger
COOLDOWN_SEC     = 5          # Debounce to avoid retriggers
CELEBRATION_SEC  = 10         # How long the celebration lasts
AUDIO_DIR        = '/home/TestPi/golf_sounds'  # Folder with .wav files
PICO_SERIAL_PORT = '/dev/ttyACM0'          # USB serial port to Pico
PICO_BAUDRATE    = 115200
# -------------------------------------------------------------------

# ───────── SETUP AUDIO ─────────────────────────────────────────────
audio_enabled = True
try:
    pygame.mixer.init()
    print("✅ Audio initialized.")
except Exception as e:
    print(f"⚠️ Audio init failed: {e}")
    audio_enabled = False

def play_random_sound():
    if not audio_enabled:
        print("🔇 Skipping sound playback.")
        return
    try:
        clips = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]
        if not clips:
            print(f"⚠️ No .wav files found in {AUDIO_DIR}")
            return
        chosen = random.choice(clips)
        print(f"🔊 Playing: {chosen}")
        pygame.mixer.music.load(os.path.join(AUDIO_DIR, chosen))
        pygame.mixer.music.play()
    except Exception as e:
        print(f"⚠️ Audio playback error: {e}")

# ───────── SETUP SENSOR ────────────────────────────────────────────
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

# ───────── SETUP SERIAL ────────────────────────────────────────────
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
