# ⛳ Office Mini Golf Celebration System

A Raspberry Pi-powered mini golf hole that reacts when you sink a putt — with flashing lights, funny taunts, and triumphant applause. 

Designed for workplace tournaments, kids-at-heart, and anyone who thinks a golf hole should heckle you back.

---

## 🎉 Features

- Detects golf ball using an ultrasonic sensor.
- Triggers a celebration with:
  - Animated LED light show (pulse and paparazzi style)
  - Randomized audio: golf claps, taunts, and silly quotes
- Idle mode: shimmering green LEDs mimic a golf fairway.
- Automatic startup on boot (optional).

---

## 🛠️ Hardware Required

| Component | Description |
|----------|-------------|
| **Raspberry Pi 3B (or newer)** | Running Raspberry Pi OS |
| **WS2812B LED Strip** | 30 LEDs recommended |
| **Ultrasonic Sensor (HC-SR04)** | Detects when the ball drops in |
| **Speaker** | USB or 3.5mm speaker for audio |
| **MegaBloks or LEGO** | (Optional) Decorate the course or disguise the sensor |
| **NES-style Pi Case** | (Optional) Pure style points 🎮 |

---

## 📁 Project Folder Structure

/home/TestPi/ ├── mini-golf-celebration/ │ └── ultrasonicTestV4.py └── golf_sounds/ ├── clap1.wav ├── taunt1.wav └── etc...


All `.wav` audio files (taunts, claps, etc.) go in the `golf_sounds/` folder.  
They are selected randomly when a celebration is triggered.

> ⚠️ Make sure audio files are **PCM-encoded `.wav`** files. Use `ffmpeg` to convert if needed:
> 
> `ffmpeg -i input.wav -acodec pcm_s16le -ar 44100 output.wav`

---

## 🔧 Installation Instructions

### 1. Install dependencies

```bash
sudo apt update
sudo apt install -y python3-pygame python3-rpi.gpio ffmpeg
pip3 install adafruit-circuitpython-neopixel
```

2. Clone this repo


```bash
cd /home/TestPi
git clone https://github.com/yourusername/mini-golf-celebration.git
cd mini-golf-celebration
```

3. Run it

```bash
python3 ultrasonicTestV6.py
```

🤝 Credits
Created with imagination, competitive spirit, and a little too much time after work.
Special thanks to MegaBloks, NES nostalgia, and every missed putt that deserved to be roasted.

