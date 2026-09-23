from flask import Flask, render_template_string, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID")

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AGRI-VISE Plant Scanner</title>

    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #111827;
            color: white;
            text-align: center;
            margin: 0;
            padding: 20px;
        }

        h1 {
            margin-bottom: 5px;
        }

        .subtitle {
            color: #9ca3af;
            margin-bottom: 20px;
        }

        video,
        #preview {
            width: 100%;
            max-width: 600px;
            border-radius: 15px;
            background: black;
        }

        video {
            display: block;
            margin: auto;
        }

        canvas {
            display: none;
        }

        .buttons {
            margin: 15px auto;
            max-width: 600px;
        }

        button,
        .upload-label {
            display: inline-block;
            margin: 5px;
            padding: 14px 20px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            color: white;
        }

        #scanBtn {
            background: #22c55e;
        }

        #uploadLabel {
            background: #2563eb;
        }

        #switchBtn {
            background: #374151;
        }

        #imageInput {
            display: none;
        }

        #result {
            margin: 25px auto;
            padding: 20px;
            max-width: 600px;
            border-radius: 15px;
            background: #1f2937;
            font-size: 22px;
        }

        .loading {
            color: #facc15;
        }

        .healthy {
            color: #4ade80;
        }

        .unhealthy {
            color: #f87171;
        }

        .uncertain {
            color: #facc15;
        }
    </style>
</head>

<body>

    <h1>🌱 AGRI-VISE</h1>

    <div class="subtitle">
        AI-Powered Plant Health Scanner
    </div>

    <!-- Camera -->
    <video id="video" autoplay playsinline></video>

    <canvas id="canvas"></canvas>

    <div class="buttons">

        <!-- Camera Scan -->
        <button id="scanBtn" onclick="scanPlant()">
            📷 Scan Plant
        </button>

        <!-- Upload Image -->
        <label
            for="imageInput"
            id="uploadLabel"
            class="upload-label">
            📁 Upload Image
        </label>

        <input
            type="file"
            id="imageInput"
            accept="image/*"
            onchange="uploadImage(event)"
        >

        <!-- Switch Camera -->
        <button id="switchBtn" onclick="switchCamera()">
            🔄 Switch Camera
        </button>

    </div>

    <img id="preview">

    <div id="result">
        Ready to scan
    </div>


<script>

let stream = null;
let currentFacingMode = "environment";


/* =========================
   START CAMERA
========================= */

async function startCamera() {

    try {

        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }

        stream = await navigator.mediaDevices.getUserMedia({

            video: {
                facingMode: currentFacingMode
            },

            audio: false

        });

        document.getElementById("video").srcObject = stream;

    }

    catch (error) {

        document.getElementById("result").innerHTML =
            "❌ Camera Error: " + error.message;

    }
}


/* =========================
   SWITCH CAMERA
========================= */

async function switchCamera() {

    currentFacingMode =
        currentFacingMode === "environment"
        ? "user"
        : "environment";

    await startCamera();

}


/* =========================
   SCAN CAMERA IMAGE
========================= */

async function scanPlant() {

    const video =
        document.getElementById("video");

    const canvas =
        document.getElementById("canvas");

    const result =
        document.getElementById("result");

    const preview =
        document.getElementById("preview");


    if (!video.videoWidth) {

        result.innerHTML =
            "❌ Camera is not ready";

        return;

    }


    result.innerHTML =
        "<span class='loading'>🤖 Analyzing plant...</span>";


    canvas.width =
        video.videoWidth;

    canvas.height =
        video.videoHeight;


    const ctx =
        canvas.getContext("2d");


    ctx.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );


    canvas.toBlob(
        async function(blob) {

            preview.src =
                URL.createObjectURL(blob);

            preview.style.display =
                "block";


            await sendImageToServer(
                blob
            );

        },
        "image/jpeg",
        0.9
    );

}


/* =========================
   UPLOAD IMAGE
========================= */

async function uploadImage(event) {

    const file =
        event.target.files[0];

    const result =
        document.getElementById("result");

    const preview =
        document.getElementById("preview");


    if (!file) {
        return;
    }


    /* Check image */

    if (!file.type.startsWith("image/")) {

        result.innerHTML =
            "❌ Please select an image file";

        return;

    }


    /* Show uploaded image */

    preview.src =
        URL.createObjectURL(file);

    preview.style.display =
        "block";


    result.innerHTML =
        "<span class='loading'>🤖 Analyzing uploaded image...</span>";


    await sendImageToServer(file);

}


/* =========================
   SEND IMAGE TO FLASK
========================= */

async function sendImageToServer(imageBlob) {

    const result =
        document.getElementById("result");


    const formData =
        new FormData();


    formData.append(
        "image",
        imageBlob,
        "plant.jpg"
    );


    try {

        const response =
            await fetch(
                "/scan",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        result.innerHTML =
            data.result;


    }

    catch (error) {

        result.innerHTML =
            "❌ Scan failed: " +
            error.message;

    }

}


/* =========================
   START
========================= */

startCamera();

</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/scan", methods=["POST"])
def scan():

    try:

        if "image" not in request.files:
            return jsonify({
                "result": "❌ No image received"
            })

        image = request.files["image"].read()

        print("\n📷 Image received:", len(image), "bytes")

        if not API_KEY:
            return jsonify({
                "result": "❌ ROBOFLOW_API_KEY missing"
            })

        if not MODEL_ID:
            return jsonify({
                "result": "❌ ROBOFLOW_MODEL_ID missing"
            })

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
                    image,
                    "image/jpeg"
                )
            },
            timeout=30
        )

        print("Roboflow status:", response.status_code)

        if response.status_code != 200:

            print("Roboflow error:")
            print(response.text)

            return jsonify({
                "result":
                f"❌ Roboflow Error ({response.status_code})"
            })

        data = response.json()

        print("Roboflow response:")
        print(data)

        predictions = data.get("predictions", {})

        if not predictions:

            return jsonify({
                "result": "❓ No prediction returned"
            })

        best_class = max(
            predictions,
            key=lambda x: predictions[x]["confidence"]
        )

        confidence = (
            predictions[best_class]["confidence"] * 100
        )

        print(
            f"🌱 Prediction: {best_class}"
        )

        print(
            f"🎯 Confidence: {confidence:.2f}%"
        )

        # Confidence handling

        if confidence < 20:

            result = (
                f"❓ No Plant Detected "
                f"({confidence:.1f}%)"
            )

        elif confidence < 60:

            result = (
                f"❓ UNCERTAIN — likely "
                f"{best_class} "
                f"({confidence:.1f}%)"
            )

        elif best_class.lower() == "healthy":

            result = (
                f"🌱 HEALTHY ✅ "
                f"({confidence:.1f}%)"
            )

        elif best_class.lower() == "leaf":

            result = (
                f"🍃 Leaf Detected "
                f"({confidence:.1f}%)"
            )

        else:

            result = (
                f"⚠️ UNHEALTHY ❌ "
                f"{best_class} "
                f"({confidence:.1f}%)"
            )

        return jsonify({
            "result": result,
            "class": best_class,
            "confidence": confidence
        })

    except Exception as e:

        print("\n❌ PLANT SCAN ERROR")
        print("Error:", type(e).__name__, e)

        return jsonify({
            "result":
            f"❌ Scan Failed: {type(e).__name__}"
        })


if __name__ == "__main__":

    print("\n===================================")
    print("      AGRI-VISE PLANT SCANNER")
    print("===================================")

    print("Model:", MODEL_ID)

    print("\nLaptop:")
    print("http://127.0.0.1:5001")

    print("\nFor phone:")
    print("Use your laptop IP or Cloudflare Tunnel")

    print("\n===================================\n")

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False
    )