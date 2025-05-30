import machine, neopixel, utime, urandom, sys

# ───────── CONFIG ──────────────────────────────────────────────
NUM_LEDS = 100
PIN_NUM = 0               # GPIO 0 (pin 1 on Pico)
BRIGHTNESS = 0.6
np = neopixel.NeoPixel(machine.Pin(PIN_NUM), NUM_LEDS)

# ───────── HELPERS ─────────────────────────────────────────────
def apply_brightness(color):
    return tuple(int(c * BRIGHTNESS) for c in color)

def fill(color):
    color = apply_brightness(color)
    for i in range(NUM_LEDS):
        np[i] = color
    np.write()

def off():
    fill((0, 0, 0))

# ───────── EFFECTS ─────────────────────────────────────────────
def shimmer_green():
    for i in range(NUM_LEDS):
        g = urandom.getrandbits(8) % 120 + 60  # 60–180
        np[i] = apply_brightness((0, g, 0))
    np.write()

def pulse_yellow(delay=0.01):
    col = apply_brightness((255, 255, 0))
    for i in list(range(NUM_LEDS)) + list(reversed(range(NUM_LEDS))):
        fill((0, 0, 0))
        np[i] = col
        np.write()
        utime.sleep(delay)

def paparazzi(run_time=8, density=0.25, flash_ms=60):
    end = utime.ticks_add(utime.ticks_ms(), int(run_time * 1000))
    n = max(1, int(NUM_LEDS * density))
    while utime.ticks_diff(end, utime.ticks_ms()) > 0:
        fill((0, 0, 0))
        for _ in range(n):
            idx = urandom.getrandbits(16) % NUM_LEDS
            np[idx] = apply_brightness((255, 255, 255))
        np.write()
        utime.sleep_ms(flash_ms)
    fill((0, 0, 0))
    np.write()

def celebrate():
    pulse_yellow()
    paparazzi()

# ───────── MAIN LOOP ──────────────────────────────────────────
print("✅ Pico LED controller ready.")
current_mode = "idle"

while True:
    if current_mode == "idle":
        shimmer_green()
        utime.sleep_ms(100)

    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline().strip()
        if not line:
            continue

        print(f"📥 Received: {line}")
        if line == "celebrate":
            current_mode = "celebrate"
            celebrate()
            current_mode = "idle"
        elif line == "idle":
            current_mode = "idle"
        elif line == "off":
            current_mode = "off"
            off()
        else:
            print("⚠️ Unknown command:", line)
