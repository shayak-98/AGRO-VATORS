from flask import Flask, render_template, Response, jsonify, request, redirect
from ultralytics import YOLO

import cv2
import urllib.request
import numpy as np
import requests
import time
import threading

from plant_health import scan_plant
# ============================================================
# DATABASE — DISABLED FOR CURRENT VERSION
# Future upgrade: historical sensor data + graphs
# ============================================================

# from database import (
#     init_database,
#     save_sensor_reading,
#     get_sensor_history
# )


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)

# DATABASE DISABLED FOR CURRENT VERSION
# init_database()

# ============================================================
# ESP32
# ============================================================

ESP32_CAM_IP = "10.191.83.238"
ESP32_MAIN_IP = "10.191.83.209"

ESP32_URL = f"http://{ESP32_CAM_IP}/capture"
ESP32_DATA_URL = f"http://{ESP32_MAIN_IP}/data"
ESP32_CONTROL_URL = f"http://{ESP32_MAIN_IP}"

REQUEST_TIMEOUT = 3
CAMERA_TIMEOUT = 3


# ============================================================
# DATABASE
# ============================================================

# DATABASE DISABLED FOR CURRENT VERSION
# last_database_save = 0
# DATABASE_SAVE_INTERVAL = 5


# ============================================================
# AUTOMATIC IRRIGATION
# ============================================================

AUTO_IRRIGATION = True

# Pump will run for 10 seconds
PUMP_RUN_SECONDS = 10

# After automatic watering, wait 5 minutes
# before another automatic watering cycle
PUMP_COOLDOWN_SECONDS = 300

last_pump_run = 0

pump_running_until = 0

pump_timer = None

pump_lock = threading.Lock()


# ============================================================
# YOLO
# ============================================================

model = YOLO(
    "models/yolov8n.pt"
)

last_detection = "None"


# ============================================================
# SENSOR DATA
# ============================================================

OFFLINE_SENSOR = {

    "temperature": "--",

    "humidity": "--",

    "soil": "--",

    "distance": "--",

    "pump": "OFF",

    "mode": "--",

    "lat": "--",

    "lon": "--",

    "pan": 90,

    "tilt": 90

}


last_sensor_data = dict(
    OFFLINE_SENSOR
)

esp32_online = False


# ============================================================
# PLANT HEALTH
# ============================================================

health_status = "Waiting for Scan..."


# ============================================================
# LAPTOP LOCATION
# ============================================================

weather_location = {

    "available": False,

    "latitude": None,

    "longitude": None,

    "accuracy": None,

    "source": "Waiting for laptop location",

    "updated": None

}


# ============================================================
# WEATHER
# ============================================================

weather_data = {

    "available": False,

    "temperature": "--",

    "humidity": "--",

    "condition": "Waiting for laptop location",

    "rain_probability": "--",

    "precipitation": "--",

    "wind_speed": "--",

    "forecast_max": "--",

    "forecast_min": "--",

    "rain_forecast": "--",

    "latitude": "--",

    "longitude": "--",

    "location_source":
        "Laptop location unavailable"

}


last_weather_update = 0

WEATHER_CACHE_TIME = 300


# ============================================================
# GET ESP32 SENSOR DATA
# ============================================================

def get_sensor_data():

    global last_sensor_data
    global esp32_online
    global last_database_save

    try:

        response = requests.get(
            ESP32_DATA_URL,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()


        # ----------------------------------------------------
        # Update cached sensor values
        # ----------------------------------------------------

        for key in OFFLINE_SENSOR:

            if (
                key in data
                and
                data[key] is not None
            ):

                last_sensor_data[key] = data[key]


        esp32_online = True


        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        # now = time.time()


        # if (
        #     now - last_database_save
        #     >= DATABASE_SAVE_INTERVAL
        # ):

        #     save_sensor_reading(

        #         temperature=
        #             data.get("temperature"),

        #         humidity=
        #             data.get("humidity"),

        #         soil=
        #             data.get("soil"),

        #         distance=
        #             data.get("distance"),

        #         pump=
        #             data.get("pump"),

        #         mode=
        #             data.get("mode"),

        #         latitude=
        #             data.get("lat"),
 
        #         longitude=
        #             data.get("lon")

        #     )


        #     last_database_save = now


        return dict(
            last_sensor_data
        )


    except Exception as e:

        print(
            "ESP32 sensor error:",
            e
        )

        esp32_online = False

        return dict(
            last_sensor_data
        )


# ============================================================
# SEND COMMAND TO ESP32
# ============================================================

def esp32_command(path):

    try:

        url = (
            f"{ESP32_CONTROL_URL}"
            f"{path}"
        )

        print(
            "ESP32 COMMAND:",
            url
        )


        response = requests.get(

            url,

            timeout=REQUEST_TIMEOUT

        )


        response.raise_for_status()


        print(
            "ESP32 RESPONSE:",
            response.text
        )


        return True


    except Exception as e:

        print(
            "ESP32 COMMAND ERROR:",
            e
        )

        return False


# ============================================================
# WEATHER DESCRIPTION
# ============================================================

def weather_description(code):

    descriptions = {

        0: "Clear sky",

        1: "Mainly clear",

        2: "Partly cloudy",

        3: "Overcast",

        45: "Fog",

        48: "Rime fog",

        51: "Light drizzle",

        53: "Moderate drizzle",

        55: "Dense drizzle",

        61: "Slight rain",

        63: "Moderate rain",

        65: "Heavy rain",

        71: "Slight snow",

        73: "Moderate snow",

        75: "Heavy snow",

        80: "Slight rain showers",

        81: "Moderate rain showers",

        82: "Violent rain showers",

        95: "Thunderstorm",

        96: "Thunderstorm with hail",

        99: "Thunderstorm with heavy hail"

    }


    try:

        code = int(code)

    except:

        return "Unknown"


    return descriptions.get(
        code,
        "Unknown"
    )


# ============================================================
# LAPTOP LOCATION
# ============================================================

@app.route(
    "/set_weather_location",
    methods=["POST"]
)
def set_weather_location():

    global weather_location
    global last_weather_update

    try:

        data = request.get_json()


        latitude = float(
            data["latitude"]
        )


        longitude = float(
            data["longitude"]
        )


        if not (

            -90 <= latitude <= 90

            and

            -180 <= longitude <= 180

        ):

            raise ValueError(
                "Invalid coordinates"
            )


        accuracy = data.get(
            "accuracy"
        )


        weather_location = {

            "available": True,

            "latitude": latitude,

            "longitude": longitude,

            "accuracy": accuracy,

            "source":
                "Laptop browser location",

            "updated":
                time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

        }


        last_weather_update = 0


        print(
            "Laptop weather location:",
            latitude,
            longitude
        )


        return jsonify({

            "success": True,

            "latitude": latitude,

            "longitude": longitude

        })


    except Exception as e:

        print(
            "Location error:",
            e
        )


        return jsonify({

            "success": False,

            "error": str(e)

        }), 400


# ============================================================
# WEATHER API
# ============================================================

def get_weather():

    global weather_data
    global last_weather_update


    if not weather_location["available"]:

        return dict(
            weather_data
        )


    now = time.time()


    if (

        weather_data["available"]

        and

        now - last_weather_update
        < WEATHER_CACHE_TIME

    ):

        return dict(
            weather_data
        )


    lat = weather_location["latitude"]

    lon = weather_location["longitude"]


    url = (

        "https://api.open-meteo.com/v1/forecast"

        f"?latitude={lat}"

        f"&longitude={lon}"

        "&current="
        "temperature_2m,"
        "relative_humidity_2m,"
        "precipitation,"
        "weather_code,"
        "wind_speed_10m"

        "&hourly="
        "temperature_2m,"
        "precipitation_probability,"
        "precipitation"

        "&daily="
        "temperature_2m_max,"
        "temperature_2m_min,"
        "precipitation_sum"

        "&forecast_days=2"

        "&timezone=auto"

    )


    try:

        response = requests.get(

            url,

            timeout=8

        )


        response.raise_for_status()


        data = response.json()


        current = data["current"]

        hourly = data["hourly"]

        daily = data["daily"]


        temperature = current.get(

            "temperature_2m",

            "--"

        )


        humidity = current.get(

            "relative_humidity_2m",

            "--"

        )


        precipitation = current.get(

            "precipitation",

            "--"

        )


        wind = current.get(

            "wind_speed_10m",

            "--"

        )


        code = current.get(

            "weather_code",

            0

        )


        # ----------------------------------------------------
        # Rain probability next 12 hours
        # ----------------------------------------------------

        probabilities = (

            hourly

            .get(

                "precipitation_probability",

                []

            )[:12]

        )


        if probabilities:

            rain_probability = max(
                probabilities
            )

        else:

            rain_probability = 0


        forecast_max = (

            daily

            .get(

                "temperature_2m_max",

                ["--"]

            )[0]

        )


        forecast_min = (

            daily

            .get(

                "temperature_2m_min",

                ["--"]

            )[0]

        )


        rain_forecast = (

            daily

            .get(

                "precipitation_sum",

                ["--"]

            )[0]

        )


        weather_data = {

            "available": True,

            "temperature":
                temperature,

            "humidity":
                humidity,

            "condition":
                weather_description(code),

            "rain_probability":
                rain_probability,

            "precipitation":
                precipitation,

            "wind_speed":
                wind,

            "forecast_max":
                forecast_max,

            "forecast_min":
                forecast_min,

            "rain_forecast":
                rain_forecast,

            "latitude":
                lat,

            "longitude":
                lon,

            "location_source":
                "Laptop browser location"

        }


        last_weather_update = now


        print(
            "Weather updated:"
        )


        print(
            "Rain probability:",
            rain_probability
        )


        return dict(
            weather_data
        )


    except Exception as e:

        print(
            "Weather API error:",
            e
        )

        return dict(
            weather_data
        )


# ============================================================
# AGRICULTURAL INTELLIGENCE
# ============================================================

# ============================================================
# AGRICULTURAL INTELLIGENCE
# ============================================================

def agricultural_decision(
    sensor,
    weather
):

    # ========================================================
    # DEFAULT FLOOD RISK
    # ========================================================

    flood_risk = "LOW"

    # ========================================================
    # SOIL
    # ========================================================

    try:

        soil = float(
            sensor.get(
                "soil",
                0
            )
        )

    except:

        return {
            "state": "WAITING",
            "irrigation": "WAIT",
            "reason": "Waiting for valid soil data.",
            "heat_risk": "UNKNOWN",
            "rain_risk": "UNKNOWN",
            "flood_risk": "UNKNOWN",
            "risk": "UNKNOWN"
        }


    SOIL_DRY_THRESHOLD = 3000

    soil_is_dry = (
        soil >= SOIL_DRY_THRESHOLD
    )


    # ========================================================
    # RAIN
    # ========================================================

    try:

        rain_probability = float(
            weather.get(
                "rain_probability",
                0
            )
        )

    except:

        rain_probability = 0


    # ========================================================
    # TEMPERATURE
    # ========================================================

    try:

        field_temperature = float(
            sensor.get(
                "temperature",
                0
            )
        )

    except:

        field_temperature = 0


    try:

        weather_temperature = float(
            weather.get(
                "temperature",
                0
            )
        )

    except:

        weather_temperature = 0


    # ========================================================
    # IRRIGATION
    # ========================================================

    if soil_is_dry:

        if rain_probability >= 60:

            state = "RAIN_EXPECTED"

            irrigation = "DELAY"

            reason = (
                f"Soil is dry "
                f"(sensor {soil:.0f}), "
                f"but rain probability is "
                f"{rain_probability:.0f}%. "
                f"Delay irrigation."
            )

        else:

            state = "IRRIGATION_REQUIRED"

            irrigation = "RECOMMENDED"

            reason = (
                f"Soil is dry "
                f"(sensor {soil:.0f}) "
                f"and rain probability is "
                f"{rain_probability:.0f}%. "
                f"Irrigation is recommended."
            )

    else:

        state = "SOIL_SUFFICIENT"

        irrigation = "NOT REQUIRED"

        reason = (
            f"Soil moisture is currently "
            f"sufficient "
            f"(sensor {soil:.0f})."
        )


    # ========================================================
    # HEAT RISK
    # ========================================================

    maximum_temperature = max(
        field_temperature,
        weather_temperature
    )


    if maximum_temperature >= 38:

        heat_risk = "HIGH"

    elif maximum_temperature >= 33:

        heat_risk = "MODERATE"

    else:

        heat_risk = "LOW"


    # ========================================================
    # RAIN RISK
    # ========================================================

    if rain_probability >= 70:

        rain_risk = "HIGH"

    elif rain_probability >= 40:

        rain_risk = "MODERATE"

    else:

        rain_risk = "LOW"


    # ========================================================
    # FLOOD / WATERLOGGING RISK
    # ========================================================

    try:

        rain_forecast_mm = float(
            weather.get(
                "rain_forecast",
                0
            )
        )

    except:

        rain_forecast_mm = 0


    if rain_forecast_mm >= 50:

        flood_risk = "HIGH"

        irrigation = "SUSPENDED"

        state = "FLOOD_RISK"

        reason = (
            f"Heavy rain forecast "
            f"({rain_forecast_mm:.0f}mm). "
            f"Irrigation suspended to reduce "
            f"waterlogging risk."
        )

    elif rain_forecast_mm >= 20:

        flood_risk = "MODERATE"

    else:

        flood_risk = "LOW"


    # ========================================================
    # OVERALL RISK
    # ========================================================

    if flood_risk == "HIGH":

        overall_risk = (
            "FLOOD / WATERLOGGING RISK"
        )

    elif (
        soil_is_dry
        and
        rain_probability >= 70
    ):

        overall_risk = (
            "HEAVY RAIN / DRY SOIL"
        )

    elif (
        soil_is_dry
        and
        heat_risk == "HIGH"
    ):

        overall_risk = (
            "DROUGHT / HEAT RISK"
        )

    elif rain_probability >= 70:

        overall_risk = (
            "HEAVY RAIN RISK"
        )

    elif heat_risk == "MODERATE":

        overall_risk = "HEAT RISK"

    else:

        overall_risk = "LOW"


    # ========================================================
    # RETURN DECISION
    # ========================================================

    return {

        "state":
            state,

        "irrigation":
            irrigation,

        "reason":
            reason,

        "heat_risk":
            heat_risk,

        "rain_risk":
            rain_risk,

        "flood_risk":
            flood_risk,

        "risk":
            overall_risk,

        "soil":
            soil,

        "rain_probability":
            rain_probability

    }


# ============================================================
# AUTOMATIC IRRIGATION
# ============================================================

def automatic_pump_off():

    global pump_running_until
    global pump_timer


    with pump_lock:

        print(
            "AUTOMATIC IRRIGATION: PUMP OFF"
        )


        esp32_command(
            "/pumpOff"
        )


        pump_running_until = 0

        pump_timer = None


# ------------------------------------------------------------
# Start automatic watering
# ------------------------------------------------------------

def start_automatic_irrigation():

    global last_pump_run
    global pump_running_until
    global pump_timer


    with pump_lock:

        now = time.time()


        # Already running
        if now < pump_running_until:

            return


        # Cooldown
        if (

            now - last_pump_run

            <

            PUMP_COOLDOWN_SECONDS

        ):

            remaining = (

                PUMP_COOLDOWN_SECONDS

                -

                (now - last_pump_run)

            )


            print(

                "AUTOMATIC IRRIGATION: "
                "COOLDOWN",

                round(remaining),

                "seconds remaining"

            )

            return


        print(
            "AUTOMATIC IRRIGATION: PUMP ON"
        )


        success = esp32_command(
            "/pumpOn"
        )


        if not success:

            print(
                "AUTOMATIC IRRIGATION: "
                "FAILED TO START PUMP"
            )

            return


        last_pump_run = now

        pump_running_until = (

            now +

            PUMP_RUN_SECONDS

        )


        pump_timer = threading.Timer(

            PUMP_RUN_SECONDS,

            automatic_pump_off

        )


        pump_timer.daemon = True

        pump_timer.start()


# ------------------------------------------------------------
# Main automatic irrigation decision
# ------------------------------------------------------------

def control_automatic_irrigation(
    decision,
    weather
):

    if not AUTO_IRRIGATION:
        return

    # ESP32 must be online
    if not esp32_online:

        print(
            "AUTOMATIC IRRIGATION: ESP32 OFFLINE"
        )

        return

    # Weather data must be available
    if not weather or not weather.get("available", False):

        print(
            "AUTOMATIC IRRIGATION: WEATHER UNAVAILABLE"
        )

        return

    irrigation = decision.get(
        "irrigation"
    )

    # Start pump only when irrigation is recommended
    if irrigation == "RECOMMENDED":

        print(
            "AUTOMATIC IRRIGATION: RECOMMENDED"
        )

        start_automatic_irrigation()

    else:

        print(
            "AUTOMATIC IRRIGATION:",
            irrigation
        )


# ============================================================
# DATABASE HISTORY API
# ============================================================
# ============================================================
# DATABASE HISTORY API — DISABLED
# Future upgrade: sensor history graphs
# ============================================================

# @app.route(
#     "/api/sensors/history"
# )
# def sensor_history():

#     try:

#         limit = request.args.get(

#             "limit",

#             default=100,

#             type=int

#         )


#         limit = max(

#             1,

#             min(

#                 limit,

#                 1000

#             )

#         )


#         history = get_sensor_history(
#             limit
#         )


#         response = jsonify({

#             "success": True,

#             "count":
#                 len(history),

#             "data":
#                 history

#         })


#         response.headers[
#             "Cache-Control"
#         ] = "no-store"


#         return response


#     except Exception as e:

#         print(
#             "History API error:",
#             e
#         )


#         return jsonify({

#             "success": False,

#             "error":
#                 str(e)

#         }), 500


# ============================================================
# DASHBOARD DATA
# ============================================================

@app.route(
    "/dashboard_data"
)
def dashboard_data():

    sensor = get_sensor_data()

    weather = get_weather()

    decision = agricultural_decision(

        sensor,

        weather

    )


    response = jsonify({

        "sensor":
            sensor,

        "weather":
            weather,

        "decision":
            decision,

        "esp32_online":
            esp32_online

    })


    response.headers[

        "Cache-Control"

    ] = (

        "no-store, "
        "no-cache, "
        "must-revalidate, "
        "max-age=0"

    )


    return response


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    sensor = get_sensor_data()

    weather = get_weather()

    decision = agricultural_decision(

        sensor,

        weather

    )


    return render_template(

        "index.html",

        health=health_status,

        detection=last_detection,

        sensor=sensor,

        weather=weather,

        decision=decision,

        weather_location=
            weather_location,

        esp32_online=
            esp32_online

    )


# ============================================================
# PUMP ON
# ============================================================

@app.route(
    "/pump/on"
)
def pump_on():

    success = esp32_command(
        "/pumpOn"
    )


    return jsonify({

        "success":
            success

    })


# ============================================================
# PUMP OFF
# ============================================================

@app.route(
    "/pump/off"
)
def pump_off():

    success = esp32_command(
        "/pumpOff"
    )


    return jsonify({

        "success":
            success

    })


# ============================================================
# PLANT HEALTH
# ============================================================

@app.route(
    "/scan"
)
def scan():

    global health_status


    try:

        health_status = scan_plant()


    except Exception as e:

        print(
            "Plant scan error:",
            e
        )

        health_status = "Scan Failed"


    return redirect("/")


# ============================================================
# ROVER CONTROLS
# ============================================================

@app.route("/auto")
def auto_mode():

    esp32_command(
        "/auto"
    )

    return redirect("/")


@app.route("/manual")
def manual_mode():

    esp32_command(
        "/manual"
    )

    return redirect("/")


@app.route("/forward")
def forward_cmd():

    esp32_command(
        "/forward"
    )

    return redirect("/")


@app.route("/left")
def left_cmd():

    esp32_command(
        "/left"
    )

    return redirect("/")


@app.route("/right")
def right_cmd():

    esp32_command(
        "/right"
    )

    return redirect("/")


@app.route("/stop")
def stop_cmd():

    esp32_command(
        "/stop"
    )

    return redirect("/")


# ============================================================
# CAMERA CONTROLS
# ============================================================

@app.route(
    "/camera/pan/left"
)
def cam_pan_left():

    esp32_command(
        "/panLeft"
    )

    return redirect("/")


@app.route(
    "/camera/pan/right"
)
def cam_pan_right():

    esp32_command(
        "/panRight"
    )

    return redirect("/")


@app.route(
    "/camera/tilt/up"
)
def cam_tilt_up():

    esp32_command(
        "/tiltUp"
    )

    return redirect("/")


@app.route(
    "/camera/tilt/down"
)
def cam_tilt_down():

    esp32_command(
        "/tiltDown"
    )

    return redirect("/")


@app.route(
    "/camera/center"
)
def cam_center():

    esp32_command(
        "/center"
    )

    return redirect("/")


@app.route(
    "/camera/scan"
)
def cam_scan():

    esp32_command(
        "/scan"
    )

    return redirect("/")


# ============================================================
# SENSOR ENDPOINT
# ============================================================

@app.route(
    "/sensor_data"
)
def sensor_data():

    response = jsonify(
        get_sensor_data()
    )


    response.headers[
        "Cache-Control"
    ] = "no-store"


    return response


# ============================================================
# WEATHER ENDPOINT
# ============================================================

@app.route(
    "/weather_data"
)
def weather_endpoint():

    response = jsonify(
        get_weather()
    )


    response.headers[
        "Cache-Control"
    ] = "no-store"


    return response


# ============================================================
# AGRICULTURAL INTELLIGENCE
# ============================================================

@app.route(
    "/agri_intelligence"
)
def agri_intelligence():

    sensor = get_sensor_data()

    weather = get_weather()

    decision = agricultural_decision(

        sensor,

        weather

    )


    # ========================================================
    # AUTOMATIC IRRIGATION
    # ========================================================

    control_automatic_irrigation(
        decision,weather
    )


    response = jsonify({

        "sensor":
            sensor,

        "weather":
            weather,

        "decision":
            decision

    })


    response.headers[
        "Cache-Control"
    ] = "no-store"


    return response


# ============================================================
# ESP32 STATUS
# ============================================================

@app.route(
    "/esp32_status"
)
def esp32_status():

    data = get_sensor_data()


    return jsonify({

        "online":
            esp32_online,

        "data":
            data

    })


# ============================================================
# CAMERA STREAM
# ============================================================

def generate_frames():

    global last_detection


    while True:

        try:

            img_resp = (

                urllib.request.urlopen(

                    ESP32_URL,

                    timeout=
                        CAMERA_TIMEOUT

                )

            )


            img_np = np.array(

                bytearray(
                    img_resp.read()
                ),

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


            annotated = (

                results[0].plot()

            )


            best_name = "None"

            best_conf = 0.0


            for box in results[0].boxes:

                cls = int(

                    box.cls[0]

                )


                conf = float(

                    box.conf[0]

                )


                if (

                    conf > best_conf

                    and

                    conf > 0.40

                ):

                    best_conf = conf

                    best_name = (

                        model.names[cls]

                    )


            last_detection = (
                best_name
            )


            ret, buffer = cv2.imencode(

                ".jpg",

                annotated

            )


            if not ret:

                continue


            frame_bytes = (

                buffer.tobytes()

            )


            yield (

                b"--frame\r\n"

                b"Content-Type: image/jpeg\r\n\r\n"

                + frame_bytes

                + b"\r\n"

            )


        except Exception as e:

            print(

                "Camera Error:",

                e

            )


            time.sleep(0.2)


@app.route(
    "/video_feed"
)
def video_feed():

    return Response(

        generate_frames(),

        mimetype=

        "multipart/x-mixed-replace; boundary=frame"

    )


# ============================================================
# START
# ============================================================

# if __name__ == "__main__":

#     app.run(

#         host="0.0.0.0",

#         port=5000,

#         debug=False,

#         threaded=True

#     )
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )