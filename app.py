from flask import Flask, render_template, Response, redirect
from ultralytics import YOLO
import cv2
import urllib.request
import numpy as np
import requests

from plant_health import scan_plant

app = Flask(__name__)

# YOLO
model = YOLO("models/yolov8n.pt")

# ESP32-CAM
ESP32_URL = "http://10.190.91.238/capture"

# ESP32 Sensor API
ESP32_DATA_URL = "http://10.190.91.209/data"

# ESP32 Control
ESP32_CONTROL_URL = "http://10.190.91.209"

last_detection = "None"
health_status = "Waiting for Scan..."


def generate_frames():
    global last_detection

    while True:

        try:

            img_resp = urllib.request.urlopen(
                ESP32_URL,
                timeout=2
            )

            img_np = np.array(
                bytearray(img_resp.read()),
                dtype=np.uint8
            )

            frame = cv2.imdecode(
                img_np,
                cv2.IMREAD_COLOR
            )

            if frame is None:
                continue

            frame = cv2.resize(
                frame,
                (640, 480)
            )

            results = model(
                frame,
                imgsz=320,
                verbose=False
            )

            annotated = results[0].plot()

            last_detection = "None"

            for box in results[0].boxes:

                cls = int(box.cls[0])
                conf = float(box.conf[0])

                if conf > 0.4:
                    last_detection = model.names[cls]

            ret, buffer = cv2.imencode(
                ".jpg",
                annotated
            )

            frame_bytes = buffer.tobytes()

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + frame_bytes +
                b'\r\n'
            )

        except Exception as e:
            print("Camera Error:", e)


@app.route('/')
def home():

    try:

        sensor = requests.get(
            ESP32_DATA_URL,
            timeout=2
        ).json()

    except:

        sensor = {
            "temperature": "--",
            "humidity": "--",
            "soil": "--",
            "distance": "--",
            "pump": "--",
            "mode": "--",
            "lat": "--",
            "lon": "--"
        }

    return render_template(
        "index.html",
        health=health_status,
        detection=last_detection,
        sensor=sensor
    )


@app.route('/scan')
def scan():

    global health_status

    try:
        health_status = scan_plant()

    except Exception as e:
        health_status = str(e)

    return redirect('/')


# MODE CONTROL

@app.route('/auto')
def auto_mode():

    requests.get(
        f"{ESP32_CONTROL_URL}/auto"
    )

    return redirect('/')


@app.route('/manual')
def manual_mode():

    requests.get(
        f"{ESP32_CONTROL_URL}/manual"
    )

    return redirect('/')


# ROVER CONTROL

@app.route('/forward')
def forward_cmd():

    requests.get(
        f"{ESP32_CONTROL_URL}/forward"
    )

    return redirect('/')


@app.route('/left')
def left_cmd():

    requests.get(
        f"{ESP32_CONTROL_URL}/left"
    )

    return redirect('/')


@app.route('/right')
def right_cmd():

    requests.get(
        f"{ESP32_CONTROL_URL}/right"
    )

    return redirect('/')


@app.route('/stop')
def stop_cmd():

    requests.get(
        f"{ESP32_CONTROL_URL}/stop"
    )

    return redirect('/')
@app.route('/sensor_data')
def sensor_data():

    try:
        sensor = requests.get(
            ESP32_DATA_URL,
            timeout=1
        ).json()

        return sensor

    except:
        return {
            "temperature":"--",
            "humidity":"--",
            "soil":"--",
            "distance":"--",
            "pump":"--",
            "mode":"--"
        }


@app.route('/video_feed')
def video_feed():

    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        threaded=True
    )