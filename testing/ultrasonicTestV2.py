import time
import RPi.GPIO as GPIO
import board
import neopixel

# ─── USER-ADJUSTABLE THRESHOLDS ────────────────────────────────────────────────
DETECT_CM       = 5          # ball is “in the hole” when distance < this
COOLDOWN_SEC    = 5           # ignore additional hits for this long
NUM_LEDS        = 25           # length of your strip
LED_BRIGHTNESS  = 0.5         # 0.0-1.0
# ───────────────────────────────────────────────────────────────────────────────

# LED strip on BCM-18  (physical pin 12)
pixels = neopixel.NeoPixel(board.D18, NUM_LEDS,
                           brightness=LED_BRIGHTNESS, auto_write=False)

# HC-SR04 wiring
TRIG = 23          # BCM 23 → physical pin 16
ECHO = 19          # BCM 19 → physical pin 35

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance_cm(timeout=0.05):
    """Return distance in centimetres, or None on timeout/error."""
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    GPIO.output(TRIG, True)
    time.sleep(1e-5)      # 10 µs
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

    return (pulse_end - pulse_start) * 17150  # speed of sound/2 → cm

def ambient_glow(frame):
    for i in range(NUM_LEDS):
        pixels[i] = ((frame+i*20) & 255,
                     (frame*2+i*30) & 255,
                     (frame*3+i*10) & 255)
    pixels.show()

def celebrate():
    print("✨ Pulse flash!")
    for _ in range(25):
        pixels.fill((255, 0, 255))
        pixels.show()
        time.sleep(0.2)
        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(0.2)

print(f"✅ Started. Detecting when distance < {DETECT_CM} cm")
last_hit = 0
frame = 0

try:
    while True:
        dist = get_distance_cm()
        now  = time.time()

        if dist is None:
            print("[timeout] no echo")
        else:
            print(f"{dist:5.1f} cm", end='')

            if dist < DETECT_CM and now - last_hit > COOLDOWN_SEC:
                print("  →  🎯 hit!")
                celebrate()
                last_hit = now
            elif now - last_hit <= COOLDOWN_SEC:
                print("  (cooldown)")
            else:
                print()

        ambient_glow(frame)
        frame = (frame + 1) & 255
        time.sleep(0.05)

except KeyboardInterrupt:
    GPIO.cleanup()
    pixels.fill((0, 0, 0))
    pixels.show()
    print("\n🔚 Exited cleanly")
