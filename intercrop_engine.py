"""
AGRI-VISE Inter-Crop Decision Engine

Offline-first crop recommendation layer for the SIH demo.
The engine uses:
- previous crop + next planned crop
- available gap
- rover soil/temperature/humidity
- weather/rain forecast
- existing agricultural decision
- optional soil photograph as supporting visual evidence

It deliberately does NOT infer exact pH, NPK, salinity or nutrients
from a photograph.
"""

import base64
import cv2
import numpy as np


# Durations are practical planning ranges, not guarantees. The catalogue
# intentionally favors short-duration crops suitable for a gap between
# major crop cycles.
CROP_CATALOG = [
    {
        "crop": "Mungbean (Green Gram)",
        "aliases": ["mungbean", "green gram", "moong", "mung", "greengram"],
        "duration": (52, 70),
        "water": "Low to Moderate",
        "temp": (24, 35),
        "moisture": "moderate",
        "family": "legume",
        "hot_fit": 1.0,
        "wet_fit": 0.65,
        "dry_fit": 0.85,
        "source_note": "Short-duration mungbean varieties are documented by ICAR at about 52–70 days.",
    },
    {
        "crop": "Black Gram (Urad Bean)",
        "aliases": ["black gram", "blackgram", "urad", "urad bean", "urdbean"],
        "duration": (60, 75),
        "water": "Moderate",
        "temp": (24, 35),
        "moisture": "moderate",
        "family": "legume",
        "hot_fit": 0.95,
        "wet_fit": 0.60,
        "dry_fit": 0.75,
        "source_note": "ICAR documents short-duration urdbean/blackgram options in roughly the 60–75 day range.",
    },
    {
        "crop": "Vegetable Cowpea (Lobia)",
        "aliases": ["cowpea", "lobia", "vegetable cowpea", "black eyed pea"],
        "duration": (50, 65),
        "water": "Moderate",
        "temp": (24, 36),
        "moisture": "moderate",
        "family": "legume",
        "hot_fit": 1.0,
        "wet_fit": 0.60,
        "dry_fit": 0.75,
        "source_note": "ICAR reports early vegetable cowpea harvesting around 50–55 days for Kashi Nidhi/Swarna Harita types.",
    },
    {
        "crop": "Moth Bean (Matki)",
        "aliases": ["moth bean", "matki", "mothbean", "mat bean"],
        "duration": (60, 70),
        "water": "Low",
        "temp": (25, 40),
        "moisture": "dry",
        "family": "legume",
        "hot_fit": 1.0,
        "wet_fit": 0.35,
        "dry_fit": 1.0,
        "source_note": "ICAR reports drought-hardy early moth bean types around 60–65 days.",
    },
    {
        "crop": "Vegetable Soybean",
        "aliases": ["vegetable soybean", "soybean", "edamame"],
        "duration": (70, 85),
        "water": "Moderate",
        "temp": (20, 32),
        "moisture": "moderate",
        "family": "legume",
        "hot_fit": 0.65,
        "wet_fit": 0.65,
        "dry_fit": 0.55,
        "source_note": "ICAR's Swarna Vasundhara reaches first harvest around 70–75 days and completes its cycle around 80–85 days.",
    },
    {
        "crop": "Toria (Short-Duration Rapeseed)",
        "aliases": ["toria", "rapeseed", "yellow sarson", "mustard"],
        "duration": (70, 90),
        "water": "Moderate",
        "temp": (12, 28),
        "moisture": "moderate",
        "family": "oilseed",
        "hot_fit": 0.25,
        "wet_fit": 0.70,
        "dry_fit": 0.60,
        "source_note": "ICAR describes toria as a short-duration crop used especially in eastern India, mainly as a winter crop.",
    },
]


def _number(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _text(value, default="Unavailable"):
    if value is None or value == "":
        return default
    return str(value)


def _normalise(value):
    return " ".join(str(value or "").lower().replace("-", " ").split())


def _crop_matches(crop_name, aliases):
    name = _normalise(crop_name)
    return any(alias in name or name in alias for alias in aliases)


def _crop_family(crop_name):
    name = _normalise(crop_name)
    for item in CROP_CATALOG:
        if _crop_matches(name, item["aliases"]):
            return item["family"]
    if any(x in name for x in ["rice", "paddy", "wheat", "maize", "corn", "barley"]):
        return "cereal"
    if any(x in name for x in ["mustard", "toria", "rapeseed", "sesame", "sunflower"]):
        return "oilseed"
    if any(x in name for x in ["potato", "tomato", "brinjal", "vegetable"]):
        return "vegetable"
    return "other"


def _soil_state(sensor_soil):
    """Use the same 3000 dry threshold already present in AGRI-VISE."""
    soil = _number(sensor_soil)
    if soil is None:
        return "unknown"
    if soil >= 3000:
        return "dry"
    if soil < 1200:
        return "wet"
    return "moderate"


def _decode_soil_image(soil_image):
    if not soil_image or not isinstance(soil_image, dict):
        return None
    data = soil_image.get("base64")
    if not data:
        return None
    try:
        raw = base64.b64decode(data)
        arr = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None:
            return None
        return image
    except Exception:
        return None


def analyze_soil_photo(soil_image):
    """Return conservative visual evidence only; never claim lab chemistry."""
    image = _decode_soil_image(soil_image)
    if image is None:
        return {
            "available": False,
            "label": "No usable soil photo",
            "dry_visual": 0.0,
            "wet_visual": 0.0,
        }

    # Ignore a narrow border where hands/tools may dominate the image.
    h, w = image.shape[:2]
    y1, y2 = int(h * 0.08), int(h * 0.92)
    x1, x2 = int(w * 0.08), int(w * 0.92)
    roi = image[y1:y2, x1:x2]
    if roi.size == 0:
        roi = image

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    brightness = float(np.mean(gray))
    saturation = float(np.mean(hsv[:, :, 1]))
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # These are visual signals only. Lighting and camera exposure can affect them.
    dark_fraction = float(np.mean(gray < 90))
    bright_fraction = float(np.mean(gray > 175))
    brown_mask = (
        (hsv[:, :, 0] >= 5)
        & (hsv[:, :, 0] <= 35)
        & (hsv[:, :, 1] >= 35)
        & (hsv[:, :, 2] <= 190)
    )
    brown_fraction = float(np.mean(brown_mask))

    dry_visual = min(1.0, max(0.0, (bright_fraction * 0.55) + (1.0 - dark_fraction) * 0.25))
    wet_visual = min(1.0, max(0.0, dark_fraction * 0.75 + brown_fraction * 0.15))

    if bright_fraction > 0.55:
        label = "Surface appears relatively light/dry-looking (lighting can affect this)."
    elif dark_fraction > 0.55:
        label = "Surface appears relatively dark; photo alone cannot confirm moisture."
    elif lap_var > 250:
        label = "Surface has strong visible texture/roughness; photo is supporting evidence only."
    else:
        label = "Mixed soil surface appearance; photo is supporting evidence only."

    return {
        "available": True,
        "label": label,
        "brightness": round(brightness, 1),
        "saturation": round(saturation, 1),
        "texture_index": round(lap_var, 1),
        "brown_fraction": round(brown_fraction, 3),
        "dry_visual": round(dry_visual, 3),
        "wet_visual": round(wet_visual, 3),
    }


def _gap_fit(item, gap_days):
    lo, hi = item["duration"]
    # Leave a small operational buffer before the next crop.
    if gap_days < lo:
        return 0.0
    if gap_days >= hi + 10:
        return 1.0
    return max(0.0, min(1.0, (gap_days - lo + 1) / max(1, hi - lo + 1)))


def _temperature_fit(item, temperature):
    if temperature is None:
        return 0.7
    lo, hi = item["temp"]
    if lo <= temperature <= hi:
        return 1.0
    if temperature < lo:
        distance = lo - temperature
    else:
        distance = temperature - hi
    if distance >= 10:
        return 0.15
    return max(0.2, 1.0 - distance * 0.08)


def _water_fit(item, soil_state, rain_probability, flood_risk):
    score = 0.7
    if soil_state == "dry":
        score *= item["dry_fit"]
    elif soil_state == "wet":
        score *= item["wet_fit"]

    if rain_probability is not None:
        if rain_probability >= 70:
            score *= item["wet_fit"]
        elif rain_probability >= 40:
            score *= 0.92

    flood = _normalise(flood_risk)
    if flood in {"high", "critical"}:
        score *= 0.55 if item["water"] != "Low" else 0.75
    elif flood == "moderate":
        score *= 0.82
    return score


def _rotation_fit(previous_crop, next_crop, item):
    previous_family = _crop_family(previous_crop)
    next_family = _crop_family(next_crop)
    score = 0.7

    # A legume in a cereal-dominated rotation gets a small diversification bonus.
    if item["family"] == "legume" and previous_family == "cereal":
        score += 0.22
    if item["family"] == "legume" and next_family == "cereal":
        score += 0.12

    # Avoid repeating the same broad crop family when the alternative is available.
    if item["family"] == previous_family:
        score -= 0.18
    if item["family"] == next_family:
        score -= 0.12

    return max(0.15, min(1.0, score))


def _season_fit(item, condition, temperature):
    condition_text = _normalise(condition)
    score = 0.75
    if item["family"] == "oilseed" and temperature is not None and temperature > 30:
        score *= 0.45
    if item["family"] == "oilseed" and any(x in condition_text for x in ["hot", "heat"]):
        score *= 0.65
    return score


def _soil_photo_fit(photo, soil_state, item):
    if not photo.get("available"):
        return 0.7
    dry_visual = photo.get("dry_visual", 0.0)
    wet_visual = photo.get("wet_visual", 0.0)
    score = 0.72
    if soil_state == "dry" and dry_visual > 0.55:
        score *= item["dry_fit"] + 0.15
    elif soil_state == "wet" and wet_visual > 0.55:
        score *= item["wet_fit"] + 0.10
    return max(0.25, min(1.0, score))


def _suitability(score):
    if score >= 0.78:
        return "High"
    if score >= 0.60:
        return "Medium"
    return "Conditional"


def _risk(item, temperature, rain_probability, flood_risk, soil_state, gap_days):
    risks = []
    if gap_days < item["duration"][0]:
        risks.append("gap too short")
    if temperature is not None:
        lo, hi = item["temp"]
        if temperature > hi + 4:
            risks.append("heat stress")
        elif temperature < lo - 4:
            risks.append("cool conditions")
    if rain_probability is not None and rain_probability >= 70:
        risks.append("high rain probability")
    if _normalise(flood_risk) in {"high", "critical"}:
        risks.append("waterlogging risk")
    if soil_state == "dry" and item["water"] in {"Moderate", "High"}:
        risks.append("irrigation needed")
    return ", ".join(risks[:2]) if risks else "Manageable with monitoring"


def _reason(item, gap_days, previous_crop, next_crop, soil_state, photo, temperature):
    lo, hi = item["duration"]
    reasons = [f"{lo}–{hi} day maturity window fits the {gap_days}-day crop gap"]
    if _crop_family(previous_crop) == "cereal" and item["family"] == "legume":
        reasons.append("adds a legume break after a cereal crop")
    if _crop_family(next_crop) == "cereal" and item["family"] == "legume":
        reasons.append("can fit before the planned cereal cycle")
    if soil_state == "dry":
        reasons.append("selected with the current dry-soil signal in mind")
    elif soil_state == "wet":
        reasons.append("selected with the current wet-soil signal in mind")
    if photo.get("available"):
        reasons.append("soil photo used only as supporting visual evidence")
    if temperature is not None:
        reasons.append(f"current field temperature is {temperature:.1f}°C")
    return "; ".join(reasons[:4]) + "."


def _caution(item, temperature, rain_probability, flood_risk, soil_state):
    notes = []
    if soil_state == "dry":
        notes.append("confirm irrigation availability before sowing")
    if rain_probability is not None and rain_probability >= 60:
        notes.append("recheck forecast before field operations")
    if _normalise(flood_risk) in {"high", "critical"}:
        notes.append("avoid planting while waterlogging risk remains high")
    if temperature is not None:
        lo, hi = item["temp"]
        if temperature > hi:
            notes.append("heat conditions may reduce suitability")
    if not notes:
        notes.append("confirm local variety, soil-test and crop-calendar guidance")
    return "; ".join(notes) + "."


def recommend_intercrops(
    previous_crop,
    next_crop,
    gap_days,
    sensor,
    weather,
    decision,
    soil_image=None,
):
    """Return the same recommendation fields expected by the existing frontend."""
    sensor = sensor or {}
    weather = weather or {}
    decision = decision or {}

    temperature = _number(sensor.get("temperature"), _number(weather.get("temperature")))
    humidity = _number(sensor.get("humidity"), _number(weather.get("humidity")))
    soil = sensor.get("soil")
    soil_state = _soil_state(soil)
    rain_probability = _number(weather.get("rain_probability"))
    rain_forecast = _number(weather.get("rain_forecast"))
    condition = _text(weather.get("condition"), "Unavailable")
    flood_risk = _text(decision.get("flood_risk"), "LOW")
    overall_risk = _text(decision.get("risk"), "UNKNOWN")

    photo = analyze_soil_photo(soil_image)
    scored = []

    for item in CROP_CATALOG:
        fit_gap = _gap_fit(item, gap_days)
        if fit_gap <= 0:
            continue

        fit_temp = _temperature_fit(item, temperature)
        fit_water = _water_fit(item, soil_state, rain_probability, flood_risk)
        fit_rotation = _rotation_fit(previous_crop, next_crop, item)
        fit_season = _season_fit(item, condition, temperature)
        fit_photo = _soil_photo_fit(photo, soil_state, item)

        # Weighted score: crop-cycle fit is intentionally dominant.
        score = (
            0.34 * fit_gap
            + 0.22 * fit_water
            + 0.17 * fit_temp
            + 0.15 * fit_rotation
            + 0.07 * fit_season
            + 0.05 * fit_photo
        )

        # A high-risk field should not be allowed to look artificially perfect.
        if _normalise(overall_risk) in {"high", "critical"}:
            score *= 0.88

        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Keep three genuinely different crop options.
    selected = []
    families = set()
    for score, item in scored:
        if len(selected) >= 3:
            break
        # Prefer diversity but allow two legumes because the short-gap catalogue
        # is intentionally pulse-heavy and ICAR documents that use case.
        if item["family"] in families and len(selected) < 2:
            continue
        selected.append((score, item))
        families.add(item["family"])

    # If diversity filtering was too strict, fill remaining slots.
    if len(selected) < min(3, len(scored)):
        for pair in scored:
            if pair not in selected:
                selected.append(pair)
            if len(selected) >= 3:
                break

    recommendations = []
    for score, item in selected:
        lo, hi = item["duration"]
        duration = min(hi, max(lo, int(round((lo + hi) / 2))))
        recommendations.append({
            "crop": item["crop"],
            "duration_days": duration,
            "suitability": _suitability(score),
            "reason": _reason(
                item, gap_days, previous_crop, next_crop,
                soil_state, photo, temperature
            ),
            "water_need": item["water"],
            "climate_fit": (
                f"Best around {item['temp'][0]}–{item['temp'][1]}°C; "
                f"current field temperature: {temperature:.1f}°C."
                if temperature is not None
                else f"Best around {item['temp'][0]}–{item['temp'][1]}°C."
            ),
            "risk": _risk(
                item, temperature, rain_probability,
                flood_risk, soil_state, gap_days
            ),
            "caution": _caution(
                item, temperature, rain_probability,
                flood_risk, soil_state
            ),
            "score": round(score, 3),
        })

    if recommendations:
        message = (
            f"Offline-first inter-crop analysis found {len(recommendations)} "
            f"short-duration options for the {gap_days}-day gap. "
            f"The ranking combines crop-cycle fit, rover/weather data, "
            f"rotation logic and optional soil-photo evidence."
        )
    else:
        message = (
            f"No catalogue crop has a verified duration that fits the "
            f"{gap_days}-day gap."
        )

    return {
        "message": message,
        "recommendations": recommendations,
        "engine": "AGRI-VISE Offline Inter-Crop Decision Engine",
        "soil_visual": photo.get("label"),
        "soil_state": soil_state,
        "inputs_used": {
            "previous_crop": previous_crop,
            "next_crop": next_crop,
            "gap_days": gap_days,
            "soil_sensor": soil,
            "temperature": temperature,
            "humidity": humidity,
            "rain_probability": rain_probability,
            "rain_forecast": rain_forecast,
            "agricultural_risk": overall_risk,
            "soil_photo_used": bool(photo.get("available")),
        },
    }
