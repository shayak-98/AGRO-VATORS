
import requests
import urllib.request
import os
from dotenv import load_dotenv
load_dotenv() 
print("API:", os.getenv("ROBOFLOW_API_KEY"))
print("MODEL:", os.getenv("ROBOFLOW_MODEL_ID"))
API_KEY = os.getenv("ROBOFLOW_API_KEY")

MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID")

ESP32_URL = "http://10.190.91.238/capture"


def scan_plant():

    try:

        img = urllib.request.urlopen(
            ESP32_URL,
            timeout=3
        ).read()

        response = requests.post(
            f"https://classify.roboflow.com/{MODEL_ID}?api_key={API_KEY}",
            files={
                "file": (
                    "plant.jpg",
                    img,
                    "image/jpeg"
                )
            }
        )

        data = response.json()

        print(data)

        predictions = data["predictions"]

        best_class = max(
            predictions,
            key=lambda x: predictions[x]["confidence"]
        )

        confidence = (
            predictions[best_class]["confidence"]
            * 100
        )

        if confidence < 20:

            return (
                f"❓ No Plant Detected "
                f"({confidence:.1f}%)"
            )

        elif best_class == "healthy":

            return (
                f"HEALTHY ✅ "
                f"({confidence:.1f}%)"
            )

        elif best_class == "leaf":

            return (
                f"Leaf Detected 🌱 "
                f"({confidence:.1f}%)"
            )

        else:

            return (
                f"UNHEALTHY ❌ "
                f"{best_class} "
                f"({confidence:.1f}%)"
            )

    except Exception as e:

        print("Plant Scan Error:", e)

        return "Scan Failed"

