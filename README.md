# 🌱 AGRO-VATORS

An AI-powered Smart Farming Rover that combines IoT, Computer Vision, and Artificial Intelligence for precision agriculture.

---

## 📖 Overview

AGRO-VATORS is a smart agricultural rover designed to monitor crop conditions in real time. It collects environmental data using multiple sensors, streams live video from an ESP32-CAM, performs object detection using YOLOv8, detects plant diseases using Roboflow AI, and supports both manual and autonomous navigation.

---

## ✨ Features

- Manual Web Control
- Autonomous Line Following (3 IR Sensors)
- Live ESP32-CAM Video Streaming
- YOLOv8 Real-Time Object Detection
- AI Plant Disease Detection
- Smart Irrigation
- Soil Moisture Monitoring
- Temperature & Humidity Monitoring
- Ultrasonic Obstacle Detection
- GPS Tracking
- OLED Live Display

---

## 🔧 Hardware Used

- ESP32
- ESP32-CAM
- L298N Motor Driver
- DC Motors
- IR Line Sensors
- Ultrasonic Sensor
- Soil Moisture Sensor
- DHT11
- GPS Module
- OLED Display
- Relay Module
- Water Pump
- Servo Pan-Tilt Camera

---

## 💻 Software Used

- Arduino IDE
- C++ (Arduino)
- Python
- Flask
- HTML
- CSS
- JavaScript
- YOLOv8
- Roboflow API

---

## 🚀 Working Principle

1. ESP32 collects sensor data.
2. Sensor data is transmitted over Wi-Fi in JSON format.
3. Flask receives and displays live data.
4. ESP32-CAM streams live video.
5. YOLOv8 performs object detection.
6. When Scan is pressed, an image is sent to Roboflow.
7. Disease prediction is displayed on the dashboard.
8. The rover supports both manual and autonomous modes.

---

## 📄 License

MIT License
