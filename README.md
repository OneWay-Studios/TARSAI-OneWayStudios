<!-- ===================================================== -->

<!-- ===================== TARS AI ======================= -->

<!-- ===================================================== -->

<p align="center">

# TARS

### Tactical Adaptive Robotic System

**USMC Block II Upgrade — v1.0.0**

</p>

<p align="center">
<code>HONESTY: 90%</code> • <code>HUMOR: 75%</code> • <code>Tactical Efficiency: 100%</code>
</p>

---

## ▌OVERVIEW

TARS is a Raspberry Pi–based AI assistant inspired by *Interstellar*.

Features:

* Voice interaction (speech recognition + TTS)
* Deadpan tactical personality
* Environmental awareness (camera + light detection)
* Wake-word activation ("TARS")

---

## ▌CORE STACK

```
LLM Engine   → Groq (Llama 3.1-8B)
TTS Engine   → Festival (voice_kal_diphone)
Speech Input → SpeechRecognition (Google API)
Vision       → OpenCV (light-level sensing)
Language     → Python 3.11
Platform     → Raspberry Pi (Linux only)
```

---

## ▌IMPORTANT

⚠️ **Raspberry Pi + Linux ONLY**

This project depends on:

* ALSA audio
* Festival TTS
* OpenCV camera drivers

Not supported:

* Windows
* macOS
* Non-Linux Pi systems

---

## ▌SETUP

### 1. Clone

```bash
git clone https://github.com/OneWay-Studios/TARSAI-OneWayStudios.git
cd TARSAI-OneWayStudios
```

---

### 2. Install System Packages

```bash
sudo apt update
sudo apt install -y \
    python3-pyaudio \
    portaudio19-dev \
    festival \
    festvox-kallpc16k \
    alsa-utils \
    libatlas-base-dev \
    libopencv-dev
```

---

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. API Key

Create `.env`:

```env
GROQ_API_KEY=your_key_here
```

---

### 5. Run

```bash
python tars.py
```

Say **"TARS"** to wake.

---

## ▌VOICE SYSTEM

Festival TTS:

```
voice_kal_diphone
```

* Lightweight
* Offline
* Robotic tone (intentionally matches TARS)

---

## ▌HARDWARE

Recommended:

* Raspberry Pi 4 / 5
* USB Microphone
* Speaker / AUX output
* Camera (optional, for light detection)

---

## ▌MISSION

A modular AI system for:

* Robotics
* Embedded AI
* Tactical simulation
* Personality-driven assistants

---

<p align="center">
COOPER, SEE YOU AT THE RENDEZVOUS.
</p>

<p align="center">
© 2026 OneWay Studios
</p>
