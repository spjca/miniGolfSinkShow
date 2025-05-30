import time, random
import RPi.GPIO as GPIO
import board, neopixel

# ───────── USER-TUNABLE SETTINGS ────────────────────────────────────────────
DETECT_CM        = 5          # ball is “in” when distance < this
CONSEC_HITS_N    = 2           # how many consecutive hits to confirm
COOLDOWN_SEC     = 5           # ignore re-hits for this long
CELEB_SEC        = 10          # celebration duration
NUM_LEDS         = 30           # strip length
LED_BRIGHTNESS   = 0.6
# ────────────────────────────────────────────────────────────────────────────

pixels = neopixel.NeoPixel(board.D18, NUM_LEDS,
                           brightness=LED_BRIGHTNESS, auto_write=False)

TRIG, ECHO = 23, 19           # BCM pins 23 (Trig) & 19 (Echo)
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# ───────── HC-SR04 READING (with timeout) ───────────────────────────────────
def get_distance_cm(timeout=0.05):
    GPIO.output(TRIG, False)
    time.sleep(0.05)
    GPIO.output(TRIG, True);  time.sleep(1e-5);  GPIO.output(TRIG, False)

    t0 = time.time()
    while GPIO.input(ECHO) == 0:
        if time.time() - t0 > timeout:           # no rising edge
            return None
    pulse_start = time.time()

    while GPIO.input(ECHO) == 1:
        if time.time() - pulse_start > timeout:  # stuck high
            return None
    pulse_end = time.time()

    return (pulse_end - pulse_start) * 17150     # cm

# ───────── LIGHT EFFECTS ────────────────────────────────────────────────────
def ambient_fairway(frame):
    for i in range(NUM_LEDS):
        g = 120 + (frame + i*12) % 135           # shades of green
        pixels[i] = (0, g, 0)
    pixels.show()

def pulse_putt(col=(255,255,0), delay=0.05):
    for pos in range(NUM_LEDS):                  # forward
        pixels.fill((0,0,0)); pixels[pos]=col; pixels.show(); time.sleep(delay)
    for pos in reversed(range(NUM_LEDS)):        # back
        pixels.fill((0,0,0)); pixels[pos]=col; pixels.show(); time.sleep(delay)

def paparazzi(run_time, density=0.25, flash_ms=60):
    end = time.time()+run_time
    flash_leds = max(1, int(NUM_LEDS*density))
    while time.time() < end:
        pixels.fill((0,0,0))
        for _ in range(flash_leds):
            pixels[random.randrange(NUM_LEDS)] = (255,255,255)
        pixels.show(); time.sleep(flash_ms/1000)
    pixels.fill((0,0,0)); pixels.show()

def celebrate():
    print(f"🎉 Celebration {CELEB_SEC}s")
    start = time.time()
    pulse_putt()
    paparazzi(max(0, CELEB_SEC-(time.time()-start)))
    print("🎉 Celebration done.")

# ───────── MAIN LOOP ────────────────────────────────────────────────────────
print(f"✅ Ready. Need {CONSEC_HITS_N} consecutive hits < {DETECT_CM} cm")
frame = 0
last_celebration = 0
hit_streak = 0                 # consecutive valid hits counter

try:
    while True:
        dist = get_distance_cm()
        now  = time.time()

        # live debug readout
        txt = f"{'None' if dist is None else f'{dist:5.1f}'} cm  "
        print(txt, end="\r")

        valid = dist is not None and 1 < dist < 400  # ignore 0 cm & outliers
        if valid and dist < DETECT_CM:
            hit_streak += 1
        else:
            hit_streak = 0                           # reset streak

        if (hit_streak >= CONSEC_HITS_N and
            now - last_celebration > COOLDOWN_SEC):
            celebrate()
            last_celebration = now
            hit_streak = 0

        ambient_fairway(frame)
        frame = (frame + 1) & 255
        time.sleep(0.05)

except KeyboardInterrupt:
    GPIO.cleanup()
    pixels.fill((0,0,0)); pixels.show()
    print("\n🔚 Clean exit")
