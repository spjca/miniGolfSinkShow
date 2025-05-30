import time
import RPi.GPIO as GPIO
import board, neopixel

# ───────────────────────── USER-TUNABLE SETTINGS ─────────────────────────────
DETECT_CM       = 5          # ball registered when distance < this
COOLDOWN_SEC    = 5           # ignore re-hits for this long
CELEB_SEC       = 10          # length of celebration animation
NUM_LEDS        = 30           # strip length
LED_BRIGHTNESS  = 0.6         # 0.0-1.0
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────── LED STRIP SETUP ────────────────────────────────
pixels = neopixel.NeoPixel(board.D18, NUM_LEDS,
                           brightness=LED_BRIGHTNESS, auto_write=False)

# ─────────────────────────── SENSOR PINS (BCM) ──────────────────────────────
TRIG = 23          # physical pin 16
ECHO = 19          # physical pin 35

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# ────────────────────────── HELPER FUNCTIONS ────────────────────────────────
def get_distance_cm(timeout=0.05):
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    GPIO.output(TRIG, True)
    time.sleep(1e-5)
    GPIO.output(TRIG, False)

    t0 = time.time()
    while GPIO.input(ECHO) == 0:
        if time.time() - t0 > timeout:
            return None
    pulse_start = time.time()

    while GPIO.input(ECHO) == 1:
        if time.time() - pulse_start > timeout:
            return None
    pulse_end = time.time()

    return (pulse_end - pulse_start) * 17150  # cm

def ambient_glow(frame):
    for i in range(NUM_LEDS):
        pixels[i] = ((frame+i*20) & 255,
                     (frame*2+i*30) & 255,
                     (frame*3+i*10) & 255)
    pixels.show()

def wheel(pos):
    """Generate rainbow color (0-255)."""
    if pos < 85:
        return (255-pos*3, pos*3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos*3, pos*3)
    pos -= 170
    return (pos*3, 0, 255 - pos*3)

def celebrate():
    """Run flashy rainbow + strobe for CELEB_SEC seconds."""
    print(f"🎉 Celebration for {CELEB_SEC} s!")
    start_time = time.time()
    j = 0
    while time.time() - start_time < CELEB_SEC:
        # rainbow swirl
        for i in range(NUM_LEDS):
            pixels[i] = wheel((i*256//NUM_LEDS + j) & 255)
        pixels.show()
        j = (j + 8) & 255
        time.sleep(0.04)

        # quick white flash every ~½ s
        if int((time.time() - start_time)*4) % 4 == 0:
            pixels.fill((255,255,255))
            pixels.show()
            time.sleep(0.05)
    # turn strip off at end
    pixels.fill((0,0,0))
    pixels.show()
    print("🎉 Celebration ended.")

# ───────────────────────────── MAIN LOOP ────────────────────────────────────
print(f"✅ Running. Detect < {DETECT_CM} cm; celebration {CELEB_SEC} s")
last_hit = 0
frame    = 0

try:
    while True:
        d = get_distance_cm()
        now = time.time()

        if d is None:
            print("[timeout]", end="\r")
        else:
            print(f"{d:5.1f} cm   ", end="\r")

            if d < DETECT_CM and now - last_hit > COOLDOWN_SEC:
                celebrate()
                last_hit = now

        ambient_glow(frame)
        frame = (frame + 1) & 255
        time.sleep(0.05)

except KeyboardInterrupt:
    GPIO.cleanup()
    pixels.fill((0,0,0))
    pixels.show()
    print("\n🔚 Exited cleanly")
