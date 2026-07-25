# 🚜 AGRO-VATORS

<p align="center">
  <b>AI-powered Smart Farming Rover for Plant Disease Detection, Autonomous Navigation, and Real-time IoT Monitoring</b>
</p>

<p align="center">
  <img src="docs/images/Main_concept/rover_concept.jpeg" width="850" alt="AGRO-VATORS">
</p>
<p align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black?logo=flask)
![ESP32](https://img.shields.io/badge/ESP32-IoT-red)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Computer%20Vision-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

</p>

# 🚜 AGRO-VATORS

**AI-Powered Smart Farming Rover using Computer Vision and IoT**

AGRO-VATORS is an intelligent farming rover designed to assist farmers by monitoring environmental conditions, detecting plant diseases, and supporting autonomous navigation. It combines IoT sensors, computer vision, and a web dashboard for real-time monitoring and control.

---

## ✨ Features

- 🌱 Plant disease detection using YOLOv8 and Roboflow
- 📹 Live ESP32-CAM video streaming
- 🌡️ Real-time temperature and humidity monitoring
- 💧 Soil moisture monitoring
- 🚰 Water pump control using relay
- 📍 GPS location tracking
- 🤖 Autonomous line-following mode
- 🎮 Manual rover control through a web dashboard
- 📊 Live dashboard with sensor data

---

## 🛠️ Hardware Used

- ESP32
- ESP32-CAM
- L298N Motor Driver
- DC Motors
- IR Line Sensors
- Ultrasonic Sensor
- DHT11 Sensor
- Soil Moisture Sensor
- GPS Module
- OLED Display
- Relay Module
- Water Pump
- Servo Motors

---

## 💻 Software Stack

- Arduino IDE (ESP32)
- Python
- Flask
- HTML
- CSS
- JavaScript
- YOLOv8
- Roboflow

---

## 📂 Project Structure

```text
AGRO-VATORS/
├── docs/
├── esp32/
├── models/
├── static/
├── templates/
├── test/
├── app.py
├── plant_health.py
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

---

## 🚀 Installation

1. Clone the repository

```bash
git clone https://github.com/<your-username>/AGRO-VATORS.git
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Create a `.env` file

```
ROBOFLOW_API_KEY=YOUR_API_KEY
ROBOFLOW_MODEL_ID=YOUR_MODEL_ID
```

4. Run the application

```bash
python app.py
```

---

## 📸 Project Images

### Rover

<img src="docs/images/rover/rover_front.jpeg" width="500">

---

### Dashboard

<img src="docs/images/dashboard/web.jpeg" width="700">

---

### OLED Display

<img src="docs\images\rover\oled_display.jpeg" width="350">

---

## 🎥 Demo

Project demonstration videos are available in the `docs/videos` folder.

---

## 📄 License

This project is licensed under the MIT License.

---

