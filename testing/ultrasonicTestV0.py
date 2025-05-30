import time
import RPi.GPIO as GPIO
import board
import neopixel

# === LED Setup ===
NUM_LEDS = 8
pixels = neopixel.NeoPixel(board.D18, NUM_LEDS, brightness=0.5, auto_write=False)

# === Ultrasonic Sensor Wiring ===
TRIG = 4    # BCM GPIO 4 → Physical Pin 16
ECHO = 24   # BCM GPIO 24 → Physical Pin 35

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# === Safe Sensor Function with Timeout ===
def get_distance():
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    timeout_start = time.time()
    while GPIO.input(ECHO) == 0:
        if time.time() - timeout_start > 0.05:
            print("⚠️ Timeout: ECHO didn't go HIGH")
            return None
    pulse_start = time.time()

    timeout_start = time.time()
    while GPIO.input(ECHO) == 1:
        if time.time() - timeout_start > 0.05:
            print("⚠️ Timeout: ECHO didn't go LOW")
            return None
    pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # cm
    return distance

# === Animations ===
def ambient_glow(frame):
    for i in range(NUM_LEDS):
        r = (frame + i * 20) % 255
        g = (frame * 2 + i * 30) % 255
        b = (frame * 3 + i * 10) % 255
        pixels[i] = (r, g, b)
    pixels.show()

def pulse_flash():
    print("✨ Running pulse flash...")
    for _ in range(2):
        pixels.fill((255, 0, 255))  # Pink flash
        pixels.show()
        time.sleep(0.2)
        pixels.fill((0, 0, 0))      # Off
        pixels.show()
        time.sleep(0.2)

# === Main Loop ===
print("🚀 System started. Monitoring ultrasonic sensor...")
last_trigger_time = time.time()
cooldown_seconds = 5
frame = 0

try:
    while True:
        dist = get_distance()
        now = time.time()

        if dist is None:
            print(f"[{time.strftime('%H:%M:%S')}] Sensor timeout.")
        elif dist < 10 and (now - last_trigger_time) > cooldown_seconds:
            print(f"[{time.strftime('%H:%M:%S')}] Distance: {dist:.1f} cm → 🎯 Ball detected!")
            pulse_flash()
            last_trigger_time = now
        elif (now - last_trigger_time) <= cooldown_seconds:
            print(f"[{time.strftime('%H:%M:%S')}] Distance: {dist:.1f} cm (cooldown)")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Distance: {dist:.1f} cm")

        ambient_glow(frame)
        frame = (frame + 1) % 256
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n🛑 Interrupted by user. Cleaning up...")
    GPIO.cleanup()
    pixels.fill((0, 0, 0))
    pixels.show()
