# TARS | Tactical Adaptive Robotic System
### USMC Block II Upgrade — VERSION: v1.0.0
### TARS is also compatible with Windows and Rasberry pi too


TARS is a high-fidelity AI assistant inspired by *Interstellar*, designed for tactical brevity and deadpan humor. It utilizes the **Groq Llama 3.1-8B** model for intelligence and the **Kokoro-ONNX** engine for high-speed, local voice synthesis.

## 🛠 Required Downloads
To deploy TARS, ensure your system has the following dependencies:
* **Python 3.10+**

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
TARS requires a connection to the Groq API for its functions.
1.  Go to (https://console.groq.com/home) and generate your API key.
2.  Create a new file in the root folder of this project named **.env**
3.  and paste the following code:  
    ```
    GROQ_API_KEY=YourGroqKey
    ```

## 🕹 Usage
Once setup is complete, initialize TARS by running:
```bash
python tars.py

© 2026 OneWay Studios.
