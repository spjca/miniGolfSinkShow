#!/usr/bin/env python3
import time, random, RPi.GPIO as GPIO
from rpi_ws281x import PixelStrip, Color, ws

# ───────── USER SETTINGS ───────────────────────────────────────────
DETECT_CM, CONSEC_HITS_N = 5, 2          # hole-detect thresholds
COOLDOWN_SEC, CELEB_SEC  = 5, 10         # debounce & celebration length
NUM_LEDS, BRIGHTNESS     = 100, 0.6      # strip length & master brightness
# -------------------------------------------------------------------

# ───────── LED STRIP  (SPI on GPIO-10 / pin 19) ────────────────────
LED_PIN, LED_CHAN = 10, 0                # SPI channel 0
strip = PixelStrip(
    NUM_LEDS, LED_PIN,
    freq_hz   = 800_000,                 # ignored in SPI mode
    dma       = 10,
    invert    = False,
    brightness= int(BRIGHTNESS * 255),
    channel   = LED_CHAN,
    strip_type= ws.WS2811_STRIP_GRB      # **correct colour order**
)
strip.begin()

def strip_set(i, r, g, b): strip.setPixelColor(i, Color(r, g, b))
def strip_fill(r, g, b):
    c = Color(r, g, b)
    for i in range(NUM_LEDS):
        strip.setPixelColor(i, c)
def strip_show(): strip.show()

# ───────── SENSOR (HC-SR04) ────────────────────────────────────────
TRIG, ECHO = 23, 19
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance_cm(timeout=0.05):
    GPIO.output(TRIG, 0); time.sleep(0.05)
    GPIO.output(TRIG, 1); time.sleep(1e-5); GPIO.output(TRIG, 0)
    t0 = time.time()
    while GPIO.input(ECHO) == 0:
        if time.time() - t0 > timeout: return None
    start = time.time()
    while GPIO.input(ECHO) == 1:
        if time.time() - start > timeout: return None
    return (time.time() - start) * 17150  # speed-of-sound calc

# ───────── LED EFFECTS ─────────────────────────────────────────────
def ambient_fairway():                   # random green “grass” shimmer
    for i in range(NUM_LEDS):
        strip_set(i, 0, random.randint(60, 180), 0)
    strip_show()

def pulse_putt(col=(255, 255, 0)):
    r, g, b = col
    delay = 2.0 / (2 * NUM_LEDS)        # 2 s forward + back
    seq = list(range(NUM_LEDS)) + list(reversed(range(NUM_LEDS)))
    for pos in seq:
        strip_fill(0, 0, 0)
        strip_set(pos, r, g, b)
        strip_show()
        time.sleep(delay)

def paparazzi(run, density=0.25, flash_ms=60):
    end = time.time() + run
    n = max(1, int(NUM_LEDS * density))
    while time.time() < end:
        strip_fill(0, 0, 0)
        for _ in range(n):
            strip_set(random.randrange(NUM_LEDS), 255, 255, 255)
        strip_show()
        time.sleep(flash_ms / 1000)
    strip_fill(0, 0, 0); strip_show()

def celebrate(d):
    print(f"🎯 Celebration!  Distance = {d:.1f} cm")
    pulse_putt()                         # ≈2 s
    paparazzi(CELEB_SEC - 2)             # ≈8 s

# ───────── MAIN LOOP ───────────────────────────────────────────────
print(f"✅ Ready – need {CONSEC_HITS_N} hits < {DETECT_CM} cm …")
ambient_fairway()                        # show grass immediately
last, streak = 0, 0
try:
    while True:
        dist = get_distance_cm()
        good = dist and 1 < dist < 400
        streak = streak + 1 if good and dist < DETECT_CM else 0
        now = time.time()
        if streak >= CONSEC_HITS_N and now - last > COOLDOWN_SEC:
            celebrate(dist)
            ambient_fairway()           # restore grass afterwards
            last, streak = now, 0
        time.sleep(0.05)
except KeyboardInterrupt:
    GPIO.cleanup()
    strip_fill(0, 0, 0); strip_show()
    print("\n🔚 Exit")
