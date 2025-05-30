import time
import RPi.GPIO as GPIO
import board, neopixel

# ---------------- LED strip ----------------
NUM_LEDS = 20
pixels = neopixel.NeoPixel(board.D18, NUM_LEDS,
                            brightness=0.5, auto_write=False)

# -------------- HC-SR04 pins ---------------
TRIG = 23          # physical 16  →  BCM 23
ECHO = 19          # physical 35  →  BCM 19

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# ---------- safe distance function ---------
def get_distance():
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    t0 = time.time()
    while GPIO.input(ECHO) == 0:
        if time.time() - t0 > 0.05:     # 50 ms safety-timeout
            return None                 # echo never went HIGH
    pulse_start = time.time()

    t0 = time.time()
    while GPIO.input(ECHO) == 1:
        if time.time() - t0 > 0.05:     # echo stuck HIGH
            return None
    pulse_end = time.time()

    return (pulse_end - pulse_start) * 17150  # cm

# -------------- simple effects -------------
def ambient(frame):
    for i in range(NUM_LEDS):
        pixels[i] = ((frame+i*20) & 255,
                     (frame*2+i*30) & 255,
                     (frame*3+i*10) & 255)
    pixels.show()

def celebrate():
    for _ in range(2):
        pixels.fill((255, 0, 255))
        pixels.show()
        time.sleep(0.2)
        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(0.2)

# ---------------- main loop ----------------
print("✅ Sensor monitor started")
cooldown = 5          # seconds
last_hit = 0
frame = 0

try:
    while True:
        d = get_distance()
        now = time.time()

        if d is None:
            print("[timeout] no echo")
        else:
            print(f"{d:5.1f} cm")

            if d < 10 and now - last_hit > cooldown:
                print("🎯 Ball detected!")
                celebrate()
                last_hit = now

        ambient(frame)
        frame = (frame + 1) & 255
        time.sleep(0.05)

except KeyboardInterrupt:
    GPIO.cleanup()
    pixels.fill((0, 0, 0))
    pixels.show()
    print("\n🔚 Exited cleanly")
