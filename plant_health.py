import requests
import urllib.request
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("API:", os.getenv("ROBOFLOW_API_KEY"))
print("MODEL:", os.getenv("ROBOFLOW_MODEL_ID"))

API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID")

# ESP32-CAM
ESP32_URL = "http://10.191.83.238/capture"


def scan_plant():
    try:
        print("📷 Capturing from ESP32-CAM...")

        # Capture image from ESP32-CAM
        img = urllib.request.urlopen(
            ESP32_URL,
            timeout=10
        ).read()

        print("✅ Image received:", len(img), "bytes")

        # Send image to Roboflow
        print("🤖 Sending image to Roboflow...")
        print("MODEL:", MODEL_ID)

        response = requests.post(
            f"https://classify.roboflow.com/{MODEL_ID}",
            params={
                "api_key": API_KEY
            },
            files={
                "file": (
                    "plant.jpg",
                    img,
                    "image/jpeg"
                )
            },
            timeout=30
        )

        print("Roboflow status:", response.status_code)

        if response.status_code != 200:
         print("❌ Roboflow error response:")
         print(response.text)
         return f"Roboflow Error ({response.status_code})"

        response.raise_for_status()

        data = response.json()

        print("Roboflow response:")
        print(data)

        predictions = data.get("predictions", {})

        if not predictions:
            return "❓ No prediction returned"

        # Find class with highest confidence
        best_class = max(
            predictions,
            key=lambda x: predictions[x]["confidence"]
        )

        confidence = predictions[best_class]["confidence"] * 100

        print(f"🌱 Prediction: {best_class}")
        print(f"🎯 Confidence: {confidence:.2f}%")

        # --------------------------------
        # CONFIDENCE HANDLING
        # --------------------------------

        # Very low confidence
        if confidence < 20:
            return f"❓ No Plant Detected ({confidence:.1f}%)"

        # Medium confidence
        elif confidence < 60:
            return f"❓ UNCERTAIN ({confidence:.1f}%) — likely {best_class}"

        # High confidence
        elif best_class.lower() == "healthy":
            return f"HEALTHY ✅ ({confidence:.1f}%)"

        elif best_class.lower() == "leaf":
            return f"Leaf Detected 🌱 ({confidence:.1f}%)"

        else:
            return f"UNHEALTHY ❌ {best_class} ({confidence:.1f}%)"

    except Exception as e:
     print("\n❌ PLANT SCAN ERROR")
     print("Error type:", type(e).__name__)
     print("Error:", e)

     return f"Scan Failed: {type(e).__name__}"


# --------------------------------
# TEST
# --------------------------------

if __name__ == "__main__":

    result = scan_plant()

    print("\n====================")
    print("FINAL RESULT")
    print("====================")
    print(result)