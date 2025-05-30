#!/usr/bin/env python3
import time, random, os, threading
import RPi.GPIO as GPIO
from rpi_ws281x import PixelStrip, Color

# ───────── USER SETTINGS ───────────────────────────────────────────
DETECT_CM, CONSEC_HITS_N = 5, 2
COOLDOWN_SEC, CELEB_SEC  = 5, 10
NUM_LEDS, BRIGHTNESS     = 100, 0.6           # strip length & brightness
# -------------------------------------------------------------------

# ───────── LED STRIP  (SPI on GPIO-10 / pin 19) ────────────────────
LED_PIN, LED_CHAN = 10, 0                     # SPI MOSI, logical channel 0
strip = PixelStrip(
    NUM_LEDS,
    LED_PIN,                  # SPI selected by using pin 10
    freq_hz   = 800_000,      # ignored by SPI but still required
    dma       = 10,
    invert    = False,
    brightness= int(BRIGHTNESS * 255),
    channel   = LED_CHAN
)
strip.begin()

def strip_set(i, r, g, b):  strip.setPixelColor(i, Color(g, r, b))
def strip_fill(r, g, b):
    c = Color(g, r, b)
    for i in range(NUM_LEDS):
        strip.setPixelColor(i, c)
def strip_show():           strip.show()

# ───────── SENSOR (HC-SR04) ────────────────────────────────────────
TRIG, ECHO = 23, 19
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance_cm(timeout=0.05):
    GPIO.output(TRIG, False); time.sleep(0.05)
    GPIO.output(TRIG, True);  time.sleep(1e-5); GPIO.output(TRIG, False)
    t0 = time.time()
    while GPIO.input(ECHO) == 0:
        if time.time() - t0 > timeout: return None
    start = time.time()
    while GPIO.input(ECHO) == 1:
        if time.time() - start > timeout: return None
    return (time.time() - start) * 17150

# ───────── LED EFFECTS ─────────────────────────────────────────────
def ambient_fairway():
    for i in range(NUM_LEDS):
        strip_set(i, random.randint(60, 180), 0, 0)  # green shades
    strip_show()

def pulse_putt(col=(255, 255, 0), delay=0.05):
    r, g, b = col
    sequence = list(range(NUM_LEDS)) + list(reversed(range(NUM_LEDS)))
    for pos in sequence:
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
    print(f"🎯 Celebration! Distance={d:.1f} cm")
    pulse_putt(); paparazzi(max(0, CELEB_SEC - 2))

# ───────── MAIN LOOP ───────────────────────────────────────────────
print(f"✅ Ready – need {CONSEC_HITS_N} hits < {DETECT_CM} cm …")
last = 0; streak = 0
try:
    while True:
        dist = get_distance_cm(); now = time.time()
        print(f"Dist: {dist if dist else 'None':>5}", end="\r")
        good = dist and 1 < dist < 400
        streak = streak + 1 if good and dist < DETECT_CM else 0
        if streak >= CONSEC_HITS_N and now - last > COOLDOWN_SEC:
            celebrate(dist); last = now; streak = 0
        ambient_fairway(); time.sleep(0.05)
except KeyboardInterrupt:
    GPIO.cleanup(); strip_fill(0, 0, 0); strip_show(); print("\n🔚 Exit")
