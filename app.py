from flask import Flask, render_template, Response, jsonify, request, redirect
from ultralytics import YOLO
import cv2
import urllib.request
import numpy as np
import requests
import time
import threading
import base64
from datetime import datetime

from plant_health import scan_plant
from intercrop_engine import recommend_intercrops
from database import init_database, save_sensor_reading, get_sensor_history

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)
# DATABASE DISABLED FOR CURRENT VERSION (init_database not called)

# ============================================================
# ESP32 CONFIG
# ============================================================
ESP32_CAM_IP = "10.191.83.238"
ESP32_MAIN_IP = "10.155.192.209"
ESP32_URL = f"http://{ESP32_CAM_IP}/capture"
ESP32_DATA_URL = f"http://{ESP32_MAIN_IP}/data"
ESP32_CONTROL_URL = f"http://{ESP32_MAIN_IP}"
REQUEST_TIMEOUT = 3
CAMERA_TIMEOUT = 3

# ============================================================
# DATABASE (disabled — future: historical sensor graphs)
# ============================================================
last_database_save = 0
DATABASE_SAVE_INTERVAL = 5

# ============================================================
# AUTOMATIC IRRIGATION
# ============================================================
AUTO_IRRIGATION = True
PUMP_RUN_SECONDS = 10          # pump runs for 10s
PUMP_COOLDOWN_SECONDS = 300    # then waits 5 min before running again
last_pump_run = 0
pump_running_until = 0
pump_timer = None
pump_lock = threading.Lock()

# ============================================================
# YOLO MODEL
# ============================================================
model = YOLO("models/yolov8n.pt")
last_detection = "None"

# ============================================================
# SENSOR / STATE
# ============================================================
OFFLINE_SENSOR = {
    "temperature": "--", "humidity": "--", "soil": "--",
    "distance": "--", "pump": "OFF", "mode": "--",
    "lat": "--", "lon": "--", "pan": 90, "tilt": 90
}
last_sensor_data = dict(OFFLINE_SENSOR)
esp32_online = False
health_status = "Waiting for Scan..."

weather_location = {
    "available": False, "latitude": None, "longitude": None,
    "accuracy": None, "source": "Waiting for laptop location", "updated": None
}

weather_data = {
    "available": False, "temperature": "--", "humidity": "--",
    "condition": "Waiting for laptop location", "rain_probability": "--",
    "precipitation": "--", "wind_speed": "--", "forecast_max": "--",
    "forecast_min": "--", "rain_forecast": "--", "latitude": "--",
    "longitude": "--", "location_source": "Laptop location unavailable"
}
last_weather_update = 0
WEATHER_CACHE_TIME = 300

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail"
}


# ============================================================
# ESP32 COMMUNICATION
# ============================================================
def get_sensor_data():
    """Poll ESP32 for latest sensor readings, cache them, and log to DB."""
    global last_sensor_data, esp32_online, last_database_save

    try:
        response = requests.get(ESP32_DATA_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        for key in OFFLINE_SENSOR:
            if key in data and data[key] is not None:
                last_sensor_data[key] = data[key]
        esp32_online = True

        now = time.time()
        if now - last_database_save >= DATABASE_SAVE_INTERVAL:
            save_sensor_reading(
                temperature=data.get("temperature"),
                humidity=data.get("humidity"),
                soil=data.get("soil"),
                distance=data.get("distance"),
                pump=data.get("pump"),
                mode=data.get("mode"),
                latitude=data.get("lat"),
                longitude=data.get("lon")
            )
            last_database_save = now

        return dict(last_sensor_data)

    except Exception as e:
        print("ESP32 sensor error:", e)
        esp32_online = False
        return dict(last_sensor_data)


def esp32_command(path):
    """Send a GET command to the ESP32 control endpoint."""
    try:
        url = f"{ESP32_CONTROL_URL}{path}"
        print("ESP32 COMMAND:", url)
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        print("ESP32 RESPONSE:", response.text)
        return True
    except Exception as e:
        print("ESP32 COMMAND ERROR:", e)
        return False


def weather_description(code):
    try:
        code = int(code)
    except (TypeError, ValueError):
        return "Unknown"
    return WEATHER_CODES.get(code, "Unknown")


# ============================================================
# LAPTOP LOCATION / WEATHER
# ============================================================
@app.route("/set_weather_location", methods=["POST"])
def set_weather_location():
    global weather_location, last_weather_update
    try:
        data = request.get_json()
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError("Invalid coordinates")

        weather_location = {
            "available": True,
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": data.get("accuracy"),
            "source": "Laptop browser location",
            "updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        last_weather_update = 0
        print("Laptop weather location:", latitude, longitude)

        return jsonify({"success": True, "latitude": latitude, "longitude": longitude})

    except Exception as e:
        print("Location error:", e)
        return jsonify({"success": False, "error": str(e)}), 400


def get_weather():
    """Fetch current + forecast weather from Open-Meteo, cached for WEATHER_CACHE_TIME."""
    global weather_data, last_weather_update

    if not weather_location["available"]:
        return dict(weather_data)

    now = time.time()
    if weather_data["available"] and now - last_weather_update < WEATHER_CACHE_TIME:
        return dict(weather_data)

    lat = weather_location["latitude"]
    lon = weather_location["longitude"]
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m"
        "&hourly=temperature_2m,precipitation_probability,precipitation"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        "&forecast_days=2&timezone=auto"
    )

    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        data = response.json()

        current = data["current"]
        hourly = data["hourly"]
        daily = data["daily"]

        probabilities = hourly.get("precipitation_probability", [])[:12]
        rain_probability = max(probabilities) if probabilities else 0

        weather_data = {
            "available": True,
            "temperature": current.get("temperature_2m", "--"),
            "humidity": current.get("relative_humidity_2m", "--"),
            "condition": weather_description(current.get("weather_code", 0)),
            "rain_probability": rain_probability,
            "precipitation": current.get("precipitation", "--"),
            "wind_speed": current.get("wind_speed_10m", "--"),
            "forecast_max": daily.get("temperature_2m_max", ["--"])[0],
            "forecast_min": daily.get("temperature_2m_min", ["--"])[0],
            "rain_forecast": daily.get("precipitation_sum", ["--"])[0],
            "latitude": lat,
            "longitude": lon,
            "location_source": "Laptop browser location"
        }
        last_weather_update = now
        print("Weather updated. Rain probability:", rain_probability)
        return dict(weather_data)

    except Exception as e:
        print("Weather API error:", e)
        return dict(weather_data)


# ============================================================
# AGRICULTURAL INTELLIGENCE
# ============================================================
def agricultural_decision(sensor, weather):
    """Combine soil, weather and temperature readings into an irrigation decision."""
    SOIL_DRY_THRESHOLD = 3000

    try:
        soil = float(sensor.get("soil", 0))
    except (TypeError, ValueError):
        return {
            "state": "WAITING", "irrigation": "WAIT",
            "reason": "Waiting for valid soil data.",
            "heat_risk": "UNKNOWN", "rain_risk": "UNKNOWN",
            "flood_risk": "UNKNOWN", "risk": "UNKNOWN"
        }

    soil_is_dry = soil >= SOIL_DRY_THRESHOLD

    try:
        rain_probability = float(weather.get("rain_probability", 0))
    except (TypeError, ValueError):
        rain_probability = 0

    try:
        field_temperature = float(sensor.get("temperature", 0))
    except (TypeError, ValueError):
        field_temperature = 0

    try:
        weather_temperature = float(weather.get("temperature", 0))
    except (TypeError, ValueError):
        weather_temperature = 0

    # --- Irrigation decision ---
    if soil_is_dry:
        if rain_probability >= 60:
            state, irrigation = "RAIN_EXPECTED", "DELAY"
            reason = (f"Soil is dry (sensor {soil:.0f}), but rain probability is "
                       f"{rain_probability:.0f}%. Delay irrigation.")
        else:
            state, irrigation = "IRRIGATION_REQUIRED", "RECOMMENDED"
            reason = (f"Soil is dry (sensor {soil:.0f}) and rain probability is "
                       f"{rain_probability:.0f}%. Irrigation is recommended.")
    else:
        state, irrigation = "SOIL_SUFFICIENT", "NOT REQUIRED"
        reason = f"Soil moisture is currently sufficient (sensor {soil:.0f})."

    # --- Heat risk ---
    max_temperature = max(field_temperature, weather_temperature)
    if max_temperature >= 38:
        heat_risk = "HIGH"
    elif max_temperature >= 33:
        heat_risk = "MODERATE"
    else:
        heat_risk = "LOW"

    # --- Rain risk ---
    if rain_probability >= 70:
        rain_risk = "HIGH"
    elif rain_probability >= 40:
        rain_risk = "MODERATE"
    else:
        rain_risk = "LOW"

    # --- Flood / waterlogging risk (overrides irrigation) ---
    try:
        rain_forecast_mm = float(weather.get("rain_forecast", 0))
    except (TypeError, ValueError):
        rain_forecast_mm = 0

    if rain_forecast_mm >= 50:
        flood_risk = "HIGH"
        irrigation = "SUSPENDED"
        state = "FLOOD_RISK"
        reason = (f"Heavy rain forecast ({rain_forecast_mm:.0f}mm). "
                  f"Irrigation suspended to reduce waterlogging risk.")
    elif rain_forecast_mm >= 20:
        flood_risk = "MODERATE"
    else:
        flood_risk = "LOW"

    # --- Overall risk summary ---
    if flood_risk == "HIGH":
        overall_risk = "FLOOD / WATERLOGGING RISK"
    elif soil_is_dry and rain_probability >= 70:
        overall_risk = "HEAVY RAIN / DRY SOIL"
    elif soil_is_dry and heat_risk == "HIGH":
        overall_risk = "DROUGHT / HEAT RISK"
    elif rain_probability >= 70:
        overall_risk = "HEAVY RAIN RISK"
    elif heat_risk == "MODERATE":
        overall_risk = "HEAT RISK"
    else:
        overall_risk = "LOW"

    return {
        "state": state, "irrigation": irrigation, "reason": reason,
        "heat_risk": heat_risk, "rain_risk": rain_risk,
        "flood_risk": flood_risk, "risk": overall_risk,
        "soil": soil, "rain_probability": rain_probability
    }


# ============================================================
# AUTOMATIC IRRIGATION
# ============================================================
def automatic_pump_off():
    global pump_running_until, pump_timer
    with pump_lock:
        print("AUTOMATIC IRRIGATION: PUMP OFF")
        esp32_command("/pumpOff")
        pump_running_until = 0
        pump_timer = None


def start_automatic_irrigation():
    global last_pump_run, pump_running_until, pump_timer
    with pump_lock:
        now = time.time()

        if now < pump_running_until:
            return  # already running

        if now - last_pump_run < PUMP_COOLDOWN_SECONDS:
            remaining = PUMP_COOLDOWN_SECONDS - (now - last_pump_run)
            print("AUTOMATIC IRRIGATION: COOLDOWN", round(remaining), "seconds remaining")
            return

        print("AUTOMATIC IRRIGATION: PUMP ON")
        if not esp32_command("/pumpOn"):
            print("AUTOMATIC IRRIGATION: FAILED TO START PUMP")
            return

        last_pump_run = now
        pump_running_until = now + PUMP_RUN_SECONDS
        pump_timer = threading.Timer(PUMP_RUN_SECONDS, automatic_pump_off)
        pump_timer.daemon = True
        pump_timer.start()


def control_automatic_irrigation(decision, weather):
    if not AUTO_IRRIGATION:
        return
    if not esp32_online:
        print("AUTOMATIC IRRIGATION: ESP32 OFFLINE")
        return
    if not weather or not weather.get("available", False):
        print("AUTOMATIC IRRIGATION: WEATHER UNAVAILABLE")
        return

    irrigation = decision.get("irrigation")
    if irrigation == "RECOMMENDED":
        print("AUTOMATIC IRRIGATION: RECOMMENDED")
        start_automatic_irrigation()
    else:
        print("AUTOMATIC IRRIGATION:", irrigation)


# ============================================================
# INTER-CROP RECOMMENDATION (offline engine, no external AI service)
# ============================================================
def calculate_gap_days(harvest_date, next_planting_date):
    try:
        harvest = datetime.strptime(harvest_date, "%Y-%m-%d")
        planting = datetime.strptime(next_planting_date, "%Y-%m-%d")
        return (planting - harvest).days
    except Exception as e:
        print("Gap calculation error:", e)
        return None


def get_intercrop_ai_recommendation(previous_crop, next_crop, harvest_date,
                                     next_planting_date, sensor, weather,
                                     decision, soil_image=None):
    """Offline-first inter-crop recommendation. Runs entirely locally — no
    Gemini or other external generative-AI service required."""
    gap_days = calculate_gap_days(harvest_date, next_planting_date)
    if gap_days is None or gap_days <= 0:
        raise ValueError("Next planting date must be after harvest date.")

    result = recommend_intercrops(
        previous_crop=previous_crop,
        next_crop=next_crop,
        gap_days=gap_days,
        sensor=sensor,
        weather=weather,
        decision=decision,
        soil_image=soil_image
    )

    print("\n" + "=" * 60)
    print("OFFLINE INTER-CROP DECISION ENGINE")
    print("=" * 60)
    print("Previous crop:", previous_crop)
    print("Next crop:", next_crop)
    print("Gap:", gap_days, "days")
    print("Soil state:", result.get("soil_state"))
    print("Soil photo:", "YES" if soil_image and soil_image.get("base64") else "NO")
    print("Recommendations:", len(result.get("recommendations", [])))
    print("=" * 60)

    return result


# ============================================================
# DATABASE HISTORY API (disabled — future: sensor history graphs)
# ============================================================
@app.route("/api/sensors/history")
def sensor_history():
    try:
        limit = request.args.get("limit", default=100, type=int)
        limit = max(1, min(limit, 1000))
        history = get_sensor_history(limit)

        response = jsonify({"success": True, "count": len(history), "data": history})
        response.headers["Cache-Control"] = "no-store"
        return response

    except Exception as e:
        print("History API error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# DASHBOARD / HOME
# ============================================================
@app.route("/dashboard_data")
def dashboard_data():
    sensor = get_sensor_data()
    weather = get_weather()
    decision = agricultural_decision(sensor, weather)

    response = jsonify({
        "sensor": sensor,
        "weather": weather,
        "decision": decision,
        "esp32_online": esp32_online
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


@app.route("/")
def home():
    sensor = get_sensor_data()
    weather = get_weather()
    decision = agricultural_decision(sensor, weather)

    return render_template(
        "index.html",
        health=health_status,
        detection=last_detection,
        sensor=sensor,
        weather=weather,
        decision=decision,
        weather_location=weather_location,
        esp32_online=esp32_online
    )


# ============================================================
# PUMP CONTROLS
# ============================================================
@app.route("/pump/on")
def pump_on():
    return jsonify({"success": esp32_command("/pumpOn")})


@app.route("/pump/off")
def pump_off():
    return jsonify({"success": esp32_command("/pumpOff")})


# ============================================================
# PLANT HEALTH
# ============================================================
@app.route("/scan")
def scan():
    global health_status
    try:
        health_status = scan_plant()
    except Exception as e:
        print("Plant scan error:", e)
        health_status = "Scan Failed"
    return redirect("/")


# ============================================================
# ROVER CONTROLS
# ============================================================
@app.route("/auto")
def auto_mode():
    esp32_command("/auto")
    return redirect("/")


@app.route("/manual")
def manual_mode():
    esp32_command("/manual")
    return redirect("/")


@app.route("/forward")
def forward_cmd():
    esp32_command("/forward")
    return redirect("/")


@app.route("/left")
def left_cmd():
    esp32_command("/left")
    return redirect("/")


@app.route("/right")
def right_cmd():
    esp32_command("/right")
    return redirect("/")


@app.route("/stop")
def stop_cmd():
    esp32_command("/stop")
    return redirect("/")


# ============================================================
# CAMERA CONTROLS
# ============================================================
@app.route("/camera/pan/left")
def cam_pan_left():
    esp32_command("/panLeft")
    return redirect("/")


@app.route("/camera/pan/right")
def cam_pan_right():
    esp32_command("/panRight")
    return redirect("/")


@app.route("/camera/tilt/up")
def cam_tilt_up():
    esp32_command("/tiltUp")
    return redirect("/")


@app.route("/camera/tilt/down")
def cam_tilt_down():
    esp32_command("/tiltDown")
    return redirect("/")


@app.route("/camera/center")
def cam_center():
    esp32_command("/center")
    return redirect("/")


@app.route("/camera/scan")
def cam_scan():
    esp32_command("/scan")
    return redirect("/")


# ============================================================
# SENSOR / WEATHER / STATUS ENDPOINTS
# ============================================================
@app.route("/sensor_data")
def sensor_data():
    response = jsonify(get_sensor_data())
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/weather_data")
def weather_endpoint():
    response = jsonify(get_weather())
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/agri_intelligence")
def agri_intelligence():
    sensor = get_sensor_data()
    weather = get_weather()
    decision = agricultural_decision(sensor, weather)

    response = jsonify({"sensor": sensor, "weather": weather, "decision": decision})
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/esp32_status")
def esp32_status():
    return jsonify({"online": esp32_online, "data": get_sensor_data()})


# ============================================================
# INTER-CROP RECOMMENDATION API
# ============================================================
@app.route("/api/intercrop-recommendation", methods=["POST"])
def intercrop_recommendation():
    try:
        previous_crop = request.form.get("previous_crop", "").strip()
        next_crop = request.form.get("next_crop", "").strip()
        harvest_date = request.form.get("harvest_date", "").strip()
        next_planting_date = request.form.get("next_planting_date", "").strip()
        soil_image = request.files.get("soil_image")

        # --- Soil image (optional) ---
        soil_image_base64 = None
        soil_image_mime = None
        if soil_image and soil_image.filename:
            allowed_types = {"image/jpeg", "image/png", "image/webp"}
            soil_image_mime = soil_image.mimetype
            if soil_image_mime not in allowed_types:
                return jsonify({"success": False, "error": "Soil image must be JPG, PNG, or WebP."}), 400

            image_bytes = soil_image.read()
            if len(image_bytes) > 5 * 1024 * 1024:
                return jsonify({"success": False, "error": "Soil image must be smaller than 5 MB."}), 400

            soil_image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # --- Validation ---
        if not previous_crop:
            return jsonify({"success": False, "error": "Previous crop is required."}), 400
        if not next_crop:
            return jsonify({"success": False, "error": "Next planned crop is required."}), 400
        if not harvest_date:
            return jsonify({"success": False, "error": "Harvest date is required."}), 400
        if not next_planting_date:
            return jsonify({"success": False, "error": "Next planting date is required."}), 400

        gap_days = calculate_gap_days(harvest_date, next_planting_date)
        if gap_days is None:
            return jsonify({"success": False, "error": "Invalid dates."}), 400
        if gap_days <= 0:
            return jsonify({"success": False, "error": "Next planting date must be after harvest date."}), 400

        sensor = get_sensor_data()
        weather = get_weather()
        decision = agricultural_decision(sensor, weather)

        print("\n" + "=" * 60)
        print("OFFLINE INTER-CROP ANALYSIS")
        print("=" * 60)
        print("Previous crop:", previous_crop)
        print("Next crop:", next_crop)
        print("Gap:", gap_days, "days")
        print("Temperature:", sensor.get("temperature"))
        print("Humidity:", sensor.get("humidity"))
        print("Soil:", sensor.get("soil"))
        print("Rain probability:", weather.get("rain_probability"))
        print("Forecast rain:", weather.get("rain_forecast"))
        print("Irrigation:", decision.get("irrigation"))
        print("Overall risk:", decision.get("risk"))
        print("Soil image:", "YES" if soil_image_base64 else "NO")
        print("=" * 60)

        ai_result = get_intercrop_ai_recommendation(
            previous_crop=previous_crop,
            next_crop=next_crop,
            harvest_date=harvest_date,
            next_planting_date=next_planting_date,
            sensor=sensor,
            weather=weather,
            decision=decision,
            soil_image={"base64": soil_image_base64, "mime_type": soil_image_mime}
        )

        return jsonify({
            "success": True,
            "gap_days": gap_days,
            "recommendations": ai_result.get("recommendations", []),
            "message": ai_result.get("message", ""),
            "sensor": sensor,
            "weather": weather,
            "decision": decision,
            "engine": ai_result.get("engine", "AGRI-VISE Offline Inter-Crop Decision Engine"),
            "soil_visual": ai_result.get("soil_visual", "No soil photo used"),
            "inputs_used": ai_result.get("inputs_used", {})
        })

    except Exception as e:
        print("Inter-crop AI error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# CAMERA STREAM
# ============================================================
def generate_frames():
    global last_detection
    while True:
        try:
            img_resp = urllib.request.urlopen(ESP32_URL, timeout=CAMERA_TIMEOUT)
            img_np = np.array(bytearray(img_resp.read()), dtype=np.uint8)
            frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            frame = cv2.resize(frame, (640, 480))
            results = model(frame, imgsz=320, verbose=False)
            annotated = results[0].plot()

            best_name, best_conf = "None", 0.0
            for box in results[0].boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                if conf > best_conf and conf > 0.40:
                    best_conf = conf
                    best_name = model.names[cls]
            last_detection = best_name

            ret, buffer = cv2.imencode(".jpg", annotated)
            if not ret:
                continue

            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

        except Exception as e:
            print("Camera Error:", e)
            time.sleep(0.2)


@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


# ============================================================
# START
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
