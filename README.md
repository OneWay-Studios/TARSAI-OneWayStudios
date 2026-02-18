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

# ▌SYSTEM OVERVIEW

TARS is a modular AI assistant inspired by *Interstellar*.

Built for:
- Low-latency inference  
- Tactical voice synthesis  
- Environmental awareness  
- Deadpan humor subroutines  

Core stack:

```
LLM Engine      → Groq Llama 3.1-8B
Voice Engine    → Kokoro-ONNX by by thewh1teagle/kokoro-onnx Repo.
Language        → Recommended Version of Python is Version 3.1
Interface       → Terminal
```

---

# ▌PROJECT STRUCTURE

This repository follows the exact operational layout:

```
TARS/
│
│
├── venv/
│   ├── Include/
│   ├── Lib/
│   ├── Scripts/
│   └── share/
│
├── .env
├── .gitignore
├── kokoro-v1.0.int8.onnx
├── voices-v1.0.bin
├── requirements.txt
├── tars.py
└── README.md
```

---

# ▌INSTALLATION PROTOCOL

## 1. Clone Repo

```bash
git clone https://github.com/OneWay-Studios/TARSAI-OneWayStudios.git
cd TARSAI-OneWayStudios
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure API key

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_actual_key_here
```

---

## 4. Initialize TARS

```bash
python tars.py
```

If successful, TARS will begin voice-enabled operation.

---


# ▌VOICE ENGINE FILES

These files must remain in the root directory:

```
kokoro-v1.0.int8.onnx
voices-v1.0.bin
```

They power the Kokoro-ONNX synthesis system.

---

# ▌ENVIRONMENT

Required:

```
Python 3.11
Groq API Key
Internet Connection
```

Supported Platforms:

- Windows
- Linux
- Raspberry Pi

---



# ▌MISSION STATEMENT

TARS is designed as a modular tactical AI framework capable of scaling into:

- Embedded robotics
- Tactical simulation systems
- AI personality frameworks
- Field-ready hardware platforms

---

<p align="center">
COOPER, SEE YOU AT THE RENDEZVOUS.
</p>

<p align="center">
© 2026 OneWay Studios
</p>
