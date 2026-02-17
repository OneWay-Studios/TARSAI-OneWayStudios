# TARS | Tactical Adaptive Robotic System
### USMC Block II Upgrade — v1.0.0

TARS is a high-fidelity AI assistant inspired by *Interstellar*, designed for tactical brevity and deadpan humor. It utilizes the **Groq Llama 3.1-8B** model for intelligence and the **Kokoro-ONNX** engine for high-speed, local voice synthesis.

## 🛠 Required Downloads
To deploy TARS, ensure your system has the following dependencies:
* **Python 3.10+**
* **Git**
* **FFmpeg** (Required for audio processing and speech recognition)

## 🚀 Installation Protocol

### 1. Clone the system
Navigate to your desired directory and run:
```bash
git clone [https://github.com/OneWay-Studios/TARSAI-OneWayStudios.git](https://github.com/OneWay-Studios/TARSAI-OneWayStudios.git)
cd TARSAI-OneWayStudios

### 2. Install Dependencies
Use the `requirements.txt` file to install all necessary Python libraries in one command:
```bash
pip install -r requirements.txt


### 3. Configure API Credentials
TARS requires a connection to the Groq API for its cognitive functions.
1.  Go to [https://groq.com/](https://groq.com/) and navigate to the **Groq Console** to generate your API key.
2.  Create a new file in the root folder of this project named **.env**
3.  Open the `.env` file and paste your key in the following format:
    ```text
    GROQ_API_KEY=your_actual_groq_api_key_here
    ```

### 4. Hardware/Model Setup
For the voice engine to function, you must place the following files in the root directory (these are not included in the repository due to file size):
* `kokoro-v1.0.int8.onnx`
* `voices-v1.0.bin`

## 🕹 Usage
Once setup is complete, initialize TARS by running:
```bash
python tars.py

© 2026 OneWay Studios.