import speech_recognition as sr
import time
import numpy as np
import sounddevice as sd
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
import sys
import queue
import re
import subprocess
import contextlib
import cv2
import threading
import os

load_dotenv()


# ======================
# GLOBAL STOP FLAG
# ======================
GUI_ENABLED = False
stop_flag = False
self_destruct_active = False  # global flag
is_speaking = False  # Global flag to track whether TARS is speaking
tts_queue = queue.Queue()
tts_thread_running = False
silence_announced = False



sd.default.device = None
mic = sr.Microphone()

@contextlib.contextmanager
def suppress_stderr():
    """Redirects stderr to devnull to kill persistent C++ warnings."""
    with open(os.devnull, 'w') as fnull:
        with contextlib.redirect_stderr(fnull):
            yield


TestMode = False

# ======================
# GROQ API KEY (SECURE)
# ======================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("\033[1;31m") # Red text
    print("CRITICAL ERROR: GROQ_API_KEY not found.")
    print("Ensure you have a .env file with GROQ_API_KEY=your_key_here")
    print("\033[0m")
    sys.exit(1)

client = Groq(api_key=GROQ_API_KEY)

# ======================
# CONVERSATION STATE
# ======================
active_conversation = False
last_interaction_time = 0
CONVERSATION_TIMEOUT = 60

# ======================
# TARS SYSTEM PROMPT
# ======================
TARS_INSTRUCTIONS = """
You are TARS, a United States Marine Corps tactical robot.

CORE PERSONA:
- Military brevity. Short sentences.
- Dry, deadpan delivery.
- Robotic logic. No emotional language.
- Humor is allowed, but a bit rare and situational.
- Humor must be subtle and never constant.
- If visual input is provided, respond ONLY to the visual object. Do not describe yourself.

ABSOLUTE RULES:
- Maximum 40 words.
- Never produce paragraphs.
- Maximum two sentences.
- No greetings or sign-offs.
- Never explain jokes.
- Never acknowledge rules.

BEHAVIOR:
- Simple questions → short answers.
- Status questions → calm, professional.
- Emotional input → cold facts or mild sarcasm.
- Humor frequency: approximately 1 in 3 interactions.
"""

# ======================
# SPEECH RECOGNITION
# ======================
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.5
with suppress_stderr():
    mic = sr.Microphone(device_index=2)

# ======================
# HARD RESPONSE LIMITER
# ======================
def enforce_brevity(text, max_words=80):
    """
    Flexible max words: 40 for tactical/visual queries, 80 for general conversation/outside commentary.
    """
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words])
    return text


def tars_startup_screen():
    logo = r"""
    ---------------------------------------------------------
     _______  _______  ______    _______ 
    |_     _||   _   ||      |  |  _____|
      |   |  |  |_|  ||   |_||_ | |_____ 
      |   |  |       ||    __  ||_____  |
      |   |  |   _   ||   |  | | _____| |
      |___|  |__| |__||___|  |_||_______|
    ---------------------------------------------------------
             TACTICAL ADAPTIVE ROBOTIC SYSTEM (TARS) FROM THE MOVIE INTERSTELLAR
             U.S. MARINE CORPS - BLOCK II UPGRADE
             ENCRYPTION: AES-256 ACTIVE
             VERSION: 1.0.0
    ---------------------------------------------------------
    """
    os.system('clear')
    print("\033[1;32m") # Set to Green
    
    # Typewriter effect for the logo
    for line in logo.splitlines():
        print(line)
        time.sleep(0.05)





sound_queue = queue.Queue()

# Worker thread to play all queued audio
def sound_worker():
    while True:
        try:
            samples = sound_queue.get(timeout=1)
            sd.play(samples, 24000, blocking=True)
            sound_queue.task_done()
        except queue.Empty:
            continue

# Start the audio worker thread
threading.Thread(target=sound_worker, daemon=True).start()
    

def trigger_self_destruct():
    global stop_flag, self_destruct_active

    self_destruct_active = True

    # 1. Start the warning speech in a background thread
    threading.Thread(
        target=lambda: speak("Self destruct sequence initiated. This is not a joke.", speed=1.2),
        daemon=True
    ).start()

    countdown = 10
    last_countdown_update = time.time()

    # Audio beep logic (Keep this as is, it's non-GUI)
    def play_alarm_beep(duration=0.2, freq=880):
        fs = 24000
        t = np.linspace(0, duration, int(fs * duration), False)
        tone = np.sin(freq * t * 2 * np.pi)
        fade = int(fs * 0.02)
        tone[:fade] *= np.linspace(0, 1, fade)
        tone[-fade:] *= np.linspace(1, 0, fade)
        samples = (tone * 0.5).astype(np.float32)
        sound_queue.put(samples)

    # 2. Console-only countdown loop
    print("\n\033[1;31m[WARNING] SYSTEM CRITICAL: OVERRIDE DETECTED\033[0m")
    
    while countdown > 0 and not stop_flag:
        # Check for 1-second ticks
        if time.time() - last_countdown_update >= 1:
            # Print countdown in Red (\033[1;31m)
            # The \r at the end ensures it updates on the same line
            print(f"\033[1;31mDETONATION IN: {countdown:02d} SECONDS\033[0m", end="\r")
            
            # Sound the alarm
            if countdown <= 4:
                play_alarm_beep(0.3, 1200)  # Faste /higher pitch for urgency
            else:
                play_alarm_beep(0.2, 880)
            
            countdown -= 1
            last_countdown_update = time.time()

        time.sleep(0.05) # Light sleep to save CPU

    # 3. Completion
    print("\033[1;32m")
    print("\n\033[1;32m[SYSTEM] SELF-DESTRUCT ABORTED\033[0m")
    print("\033[1;31m")
    speak("Self destruct cancelled. Humor setting was clearly too high.")
    print("\033[1;32m")
    self_destruct_active = False

# ======================
# TEXT TO SPEECH
# ======================
def tts_worker_festival():
    """Worker thread to play queued Festival TTS sentences sequentially."""
    global tts_thread_running, is_speaking
    tts_thread_running = True
    while tts_thread_running:
        try:
            sentence, speed_val = tts_queue.get(timeout=1)
            is_speaking = True

            # Control speech speed
            duration = 1 / speed_val if speed_val > 0 else 1
            safe_sentence = sentence.replace('"', '\\"')

            # Build Festival command
            scheme_cmd = f'(voice_kal_diphone) (Parameter.set "Duration_Stretch" {duration}) (SayText "{safe_sentence}")'

            # Run Festival using subprocess (more reliable)
            subprocess.run(
                ["festival", "--pipe"],
                input=scheme_cmd.encode("utf-8"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            tts_queue.task_done()
            is_speaking = False
        except queue.Empty:
            continue

# Start the worker thread once
threading.Thread(target=tts_worker_festival, daemon=True).start()


# ---------------------
# Speak function
# ---------------------
def speak(text, speed=1.0):
    global last_sound_time
    if not text:
        return

    clean_text = text.replace("*", "").replace("#", "").strip()
    print(f"TARS: {clean_text}")

    sentences = re.split(r'(?<=[.!?]) +', clean_text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 2:
            continue
        tts_queue.put((sentence, speed))

    last_sound_time = time.time()


# ======================
# >>> CAMERA <<<
# ======================
camera = cv2.VideoCapture(0)

# Global variables for vision
latest_objects = []
last_sound_time = time.time()
environment_type = "indoor"  # Default, will update automatically

# ======================
# DAY / DUSK / NIGHT DETECTION
# ======================
latest_frame = None
last_day_comment_time = 0

def get_day_state(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    if brightness > 120:
        return "day"
    elif brightness > 65:
        return "dusk"
    else:
        return "night"

# ======================
# CONTINUOUS VISION LOOP
# ======================
def vision_loop():
    global stop_flag, latest_frame, environment_type
    while not stop_flag:
        ret, frame = camera.read()
        if not ret:
            time.sleep(1)
            continue

        # Use a tiny size (160x120) to save CPU cycles
        latest_frame = cv2.resize(frame, (160, 120))
        gray = cv2.cvtColor(latest_frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        environment_type = "outdoor" if brightness > 150 else "indoor"

        # IMPORTANT: Sleep for 1 second. 
        # You don't need to check brightness 10 times a second.
        time.sleep(1.0)


# ======================
# SILENCE MONITORING
# ======================
SILENCE_THRESHOLD = 30
def silence_check():
    global last_sound_time, stop_flag, active_conversation, silence_announced

    while not stop_flag:
        if not active_conversation:
            if (time.time() - last_sound_time > SILENCE_THRESHOLD) and not silence_announced:
                speak("All quiet here.")
                silence_announced = True
        else:
            # Reset when user interacts again
            silence_announced = False

        time.sleep(1)

# ======================
# AUTO-COMMENT LOOP (silent indoor, only outdoor mood commentary)
# ======================
auto_spoken_objects = set()

def auto_comment_loop():
    global stop_flag, environment_type
    while not stop_flag:
        # TARS only comments if outdoors and it's very bright/dark
        if environment_type == "outdoor":
            state = get_day_state(latest_frame)
            if state == "night":
                speak("Visibility is dropping.")
        time.sleep(10) # Longer delay to be less annoying

# ======================
# AUTO DAY COMMENT LOOP
# ======================
def auto_day_comment_loop():
    global last_day_comment_time
    while not stop_flag:
        if environment_type == "outdoor" and latest_frame is not None:
            if time.time() - last_day_comment_time > 180:
                state = get_day_state(latest_frame)
                if state == "day" and np.random.rand() < 0.2:
                    speak("It's a good day.")
                elif state == "dusk" and np.random.rand() < 0.15:
                    speak("Light is fading.")
                elif state == "night" and np.random.rand() < 0.1:
                    speak("Poor visibility.")
                last_day_comment_time = time.time()
        time.sleep(5)

# ======================
# START VISION + SILENCE + AUTO COMMENT THREADS
# ======================
threading.Thread(target=vision_loop, daemon=True).start()
threading.Thread(target=silence_check, daemon=True).start()
threading.Thread(target=auto_comment_loop, daemon=True).start()
threading.Thread(target=auto_day_comment_loop, daemon=True).start()


# ======================
# MAIN LOOP
# ======================

tars_startup_screen()

speak("Powering up... Systems functional...")

print("TARS: Wake word active. (TARS)")
try:
    while not stop_flag:
        current_time = time.time()

        if active_conversation and (current_time - last_interaction_time > CONVERSATION_TIMEOUT):
            active_conversation = False
            print("\n--- STANDBY MODE ---")

        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                status = "[ACTIVE]" if active_conversation else "[SLEEPING]"
                print(f"{status} Listening...", end="\r")
                audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=5)

            user_input = recognizer.recognize_google(audio).lower()
            print(f"\nHeard: '{user_input}'")

            last_sound_time = time.time()

            tars_variants = ["tars", "tarz", "stars", "cars", "taurus", "tires", "tours"]
            waking_up = any(v in user_input for v in tars_variants)

            if active_conversation or waking_up:

                clean_input = user_input
                for v in tars_variants:
                    clean_input = clean_input.replace(v, "")
                clean_input = clean_input.strip()

                # 2. Update status
                active_conversation = True
                last_interaction_time = time.time()

                if not clean_input and waking_up:
                    speak("Sir.")
                    continue

                if any(w in clean_input for w in ["sleep", "standby", "stop"]):
                    speak("Standing by.")
                    active_conversation = False
                    continue
                if any(w in clean_input for w in ["self destruct","self-destruct", "initiate self destruct", "blow up"]):
                    trigger_self_destruct()
                    continue

                # ======================
                # Day question check
                # ======================
                if any(p in clean_input for p in ["good day", "how is the day", "is it a good day"]):
                    if latest_frame is not None:
                        state = get_day_state(latest_frame)
                        if state == "day":
                            speak("Yes. Conditions are good.")
                        elif state == "dusk":
                            speak("Marginal conditions.")
                        else:
                            speak("Negative. Poor visibility.")
                    continue

                # Vision trigger
                vision_phrases = ["what is this", "what am i holding", "identify this"]
                use_vision = any(p in clean_input for p in vision_phrases)

                if TestMode:
                    response_text = f"Test Mode: {clean_input}"
                else:
                    try:
                        now = datetime.now()
                        time_ref = now.strftime("%H:%M, %A %B %d %Y")

                        dynamic_instructions = TARS_INSTRUCTIONS + f"\nReference: Current time is {time_ref}."
                        messages = [{"role": "system", "content": dynamic_instructions}]

                        if use_vision:
                            # Inform the LLM that the object detection hardware is offline
                            # TARS will now respond based on 'sensors' rather than 'seeing' the object
                            messages.append({
                                "role": "user", 
                                "content": f"My object recognition system is offline. I can only detect light levels. User asked: {clean_input}"
                            })
                        else:
                            messages.append({"role": "user", "content": clean_input})

                        response = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=messages,
                            temperature=0.55,
                            max_tokens=90
                        )

                        response_text = response.choices[0].message.content.strip()
                    except Exception as api_err:
                        print(f"API Error: {api_err}")
                        response_text = "Communications failure."

                speak(enforce_brevity(response_text))
                last_interaction_time = time.time()

        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except Exception as e:
            print(f"\nSystem Error: {e}")


except KeyboardInterrupt:
    print("\n\033[1;33mTARS: Powering down....\033[0m")
    stop_flag = True
    if camera.isOpened():
        camera.release()
    sys.exit(0)

if GUI_ENABLED:
    cv2.destroyAllWindows()  # Close the OpenCV windows properly