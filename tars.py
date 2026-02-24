import speech_recognition as sr
import time
import numpy as np
import sounddevice as sd
from kokoro_onnx import Kokoro
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
import sys
import queue
import random


import cv2
import threading
import os

load_dotenv()


# ======================
# GLOBAL STOP FLAG
# ======================
GUI_ENABLED = True
stop_flag = False
self_destruct_active = False  # global flag
is_speaking = False  # Global flag to track whether TARS is speaking
tts_queue = queue.Queue()
tts_thread_running = False

# ======================
# INITIALIZE VOICE
# ======================
import os
import contextlib

current_eye_y = 60  # Default starting size when not speaking
target_eye_y = 60   # Target size for the eyes
transition_speed = 0.1  # Speed of smooth transition


@contextlib.contextmanager
def suppress_stderr():
    """Redirects stderr to devnull to kill persistent C++ warnings."""
    with open(os.devnull, 'w') as fnull:
        with contextlib.redirect_stderr(fnull):
            yield

try:
    import onnxruntime as ort
    
    # 1. Force the engine to ignore everything except the CPU
    sess_options = ort.SessionOptions()
    sess_options.intra_op_num_threads = 2
    sess_options.add_session_config_entry("session.intra_op.allow_spinning", "0")

    os.system('clear')
    
    # 2. Use the suppressor only during the initialization phase
    with suppress_stderr():
        kokoro = Kokoro("kokoro-v1.0.int8.onnx", "voices-v1.0.bin")
        
        # Manually lock the session to CPU
        kokoro.session = ort.InferenceSession(
            "kokoro-v1.0.int8.onnx",
            sess_options=sess_options,
            providers=["CPUExecutionProvider"]
        )
    print("Warming up voice engine...")
    _ = kokoro.create("Initialize.", voice="am_onyx", speed=1.1, lang="en-us")
    
    print("sVoice engine locked to CPU. Discovery warnings suppressed.")
except Exception as e:
    print(f"Kokoro Init Error: {e}")

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
- Humor frequency: approximately 1 in 7 interactions.
"""

# ======================
# SPEECH RECOGNITION
# ======================
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.5
mic = sr.Microphone()

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

import sys

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
             TACTICAL ADAPTIVE ROBOTIC SYSTEM (TARS)
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

def update_eye_size():
    global current_eye_y, target_eye_y
    # Smoothly transition between current size and target size
    current_eye_y += (target_eye_y - current_eye_y) * transition_speed

def create_face_image():
    # Set the background to black (all zeros)
    face = np.zeros((400, 500, 3), dtype=np.uint8)  # Black background
    
    # Make the eyes bigger and wider
    eye_axis_x = 30  # Horizontal radius (makes eyes wide)
    
    # Update the vertical axis for smooth animation (based on speaking)
    eye_axis_y = current_eye_y  # Smooth transition for vertical axis
    
    # Position of the eyes
    eye_position_left = (120, 150)
    eye_position_right = (380, 150)
    
    # Draw the eyes as ellipses (wider at the top)
    cv2.ellipse(face, eye_position_left, (eye_axis_x, int(eye_axis_y)), 0, 0, 360, (255, 255, 255), -1)  # Left eye (white)
    cv2.ellipse(face, eye_position_right, (eye_axis_x, int(eye_axis_y)), 0, 0, 360, (255, 255, 255), -1)  # Right eye (white)
    
    return face


# Function to display the eyes continuously
def display_eyes():
    global current_eye_y, stop_flag, self_destruct_active
    window_name = "TARS Eyes"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while not stop_flag:
        if not self_destruct_active:
            update_eye_size()
            face = create_face_image()
            cv2.imshow(window_name, face)
        # Always call waitKey to process window events
        key = cv2.waitKey(1)
        if key == ord('f'):
            prop = cv2.getWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN)
            if prop == 0:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        # Tiny sleep to reduce CPU usage
        time.sleep(0.01)

# ---------------------
# Draw eyes on a given frame (for self-destruct / overlays)
# ---------------------
def draw_eyes(frame, shrink=False, twitch_offset=0):
    global current_eye_y
    eye_axis_x = 30
    eye_axis_y = 20 if shrink else int(current_eye_y)
    eye_axis_y += twitch_offset  # random twitch

    eye_position_left = (frame.shape[1] // 4, frame.shape[0] // 3 + twitch_offset)
    eye_position_right = (3 * frame.shape[1] // 4, frame.shape[0] // 3 + twitch_offset)

    cv2.ellipse(frame, eye_position_left, (eye_axis_x, eye_axis_y), 0, 0, 360, (255,255,255), -1)
    cv2.ellipse(frame, eye_position_right, (eye_axis_x, eye_axis_y), 0, 0, 360, (255,255,255), -1)


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

    # --- SPEAK INITIATION (non-blocking thread) ---
    threading.Thread(
        target=lambda: speak("Self destruct sequence initiated. This is not a joke.", speed=1.2),
        daemon=True
    ).start()

    # --- SETUP WINDOW ---
    window_name = "TARS Eyes"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    countdown = 10
    last_countdown_update = time.time()

    # --- NON-BLOCKING BEEP ---
    def play_alarm_beep(duration=0.2, freq=880):
        """Queue a beep to play asynchronously on top of TTS."""
        fs = 24000
        t = np.linspace(0, duration, int(fs * duration), False)
        tone = np.sin(freq * t * 2 * np.pi)
        fade = int(fs * 0.02)
        tone[:fade] *= np.linspace(0, 1, fade)
        tone[-fade:] *= np.linspace(1, 0, fade)
        samples = (tone * 0.5).astype(np.float32)

        # Put beep in the global sound queue
        sound_queue.put(samples)

    # --- COUNTDOWN LOOP ---
    while countdown > 0 and not stop_flag:
        frame = np.zeros((400, 500, 3), dtype=np.uint8)

        # Smooth glitch signal
        noise = np.random.randint(0, 256, frame.shape, dtype=np.uint8)
        glitch_intensity = np.random.uniform(0.2, 0.5)
        frame = cv2.addWeighted(frame, 1 - glitch_intensity, noise, glitch_intensity, 0)
        frame[:, :, 2] = 255  # Strong red channel

        # Static countdown text (no blinking)
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f"SELF DESTRUCT IN: {countdown:02d}"
        scale = 1.0
        thickness = 2
        while cv2.getTextSize(text, font, scale, thickness)[0][0] > frame.shape[1] - 20:
            scale -= 0.05
        text_size = cv2.getTextSize(text, font, scale, thickness)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = (frame.shape[0] + text_size[1]) // 2
        cv2.putText(frame, text, (text_x, text_y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Countdown logic: decrease once per second
        if time.time() - last_countdown_update >= 1:
            if countdown <= 4:
                play_alarm_beep(0.3, 1200)  # faster/louder near the end
            else:
                play_alarm_beep(0.2, 880)
            countdown -= 1
            last_countdown_update = time.time()

        time.sleep(0.01)

    # --- FINAL CANCEL SPEECH ---
    speak("Self destruct cancelled. Humor setting was clearly too high.")
    self_destruct_active = False

# ======================
# TEXT TO SPEECH
# ======================
def tts_worker():
    """Continuously plays queued TTS chunks."""
    global tts_thread_running
    tts_thread_running = True
    while tts_thread_running:
        try:
            samples = tts_queue.get(timeout=1)
            # Play the samples asynchronously (non-blocking)
            sd.play(samples, 24000)
            tts_queue.task_done()
        except queue.Empty:
            continue

# Start the TTS worker thread once
threading.Thread(target=tts_worker, daemon=True).start()


# ---------------------
# Speak function
# ---------------------
def speak(text, speed=1.3):
    """Moderately fast TTS using queue system."""
    global is_speaking  # Access the global speaking flag
    global target_eye_y  # Access the target_eye_y for smooth animation
    
    if not text:
        return

    clean_text = text.replace("*", "").replace("#", "").strip()
    print(f"TARS: {clean_text}")

    # Mark that TARS is speaking
    is_speaking = True
    target_eye_y = 20  # Shrink eyes immediately when speaking starts

    # Split text only if very long
    chunks = (
        [clean_text]
        if len(clean_text.split()) <= 100
        else [
            s.strip()
            for s in clean_text.replace("!", ".").replace("?", ".").split(".")
            if len(s.strip()) > 2
        ]
    )

    for chunk in chunks:
        try:
            # Generate TTS samples asynchronously (immediately, not waiting for eye shrinking)
            samples, _ = kokoro.create(chunk, voice="am_onyx", speed=speed, lang="en-us")
            tts_queue.put(samples)  # Queue for playback immediately
        except Exception as e:
            print(f"TTS Error: {e}")

    # After triggering TTS, we can asynchronously handle eye animation
    threading.Thread(target=update_eye_size, daemon=True).start()  # Update eyes smoothly in the background

    global last_sound_time
    last_sound_time = time.time()

    # Return eyes to normal size after speaking finishes (do not block TTS)
    target_eye_y = 60  # Eyes return to normal size

    # Mark that TARS has finished speaking
    is_speaking = False


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
    global last_sound_time, stop_flag, active_conversation
    while not stop_flag:
        if not active_conversation and (time.time() - last_sound_time > SILENCE_THRESHOLD):
            speak("All quiet here.")
            last_sound_time = time.time()
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
# GUI: Display Eyes in a separate thread
# ======================
if GUI_ENABLED:
    threading.Thread(target=display_eyes, daemon=True).start()  # Start the eyes display thread

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

        # Allow OpenCV window to update (key press event handling)
        if GUI_ENABLED:
            cv2.waitKey(1)  # Let OpenCV process events and update the GUI window

except KeyboardInterrupt:
    print("\nTARS: Powering down...")
    stop_flag = True
    camera.release()

if GUI_ENABLED:
    cv2.destroyAllWindows()  # Close the OpenCV windows properly