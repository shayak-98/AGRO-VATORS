// ===============================
// SENSOR HISTORY GRAPHS
// ===============================

let temperatureChart;
let humidityChart;
let soilChart;
let distanceChart;

async function loadSensorHistory() {

    try {

        const response = await fetch(
            "/api/sensors/history?limit=100&t=" + Date.now(),
            {
                method: "GET",
                cache: "no-store"
            }
        );

        if (!response.ok) {
            throw new Error("History HTTP error");
        }

        const result = await response.json();

        if (!result.success || !result.data) {
            console.log("No sensor history available");
            return;
        }

        const history = result.data;

        // Database returns newest first,
        // so reverse it for chronological graphs.
        history.reverse();

        const labels = history.map(row => {
            const date = new Date(row.timestamp);
            return date.toLocaleTimeString();
        });

        const temperature = history.map(row =>
            Number(row.temperature)
        );

        const humidity = history.map(row =>
            Number(row.humidity)
        );

        const soil = history.map(row =>
            Number(row.soil)
        );

        const distance = history.map(row =>
            Number(row.distance)
        );


        // -------------------------------
        // TEMPERATURE
        // -------------------------------

        if (temperatureChart) {
            temperatureChart.destroy();
        }

        temperatureChart = new Chart(
            document.getElementById("temperatureChart"),
            {
                type: "line",

                data: {
                    labels: labels,

                    datasets: [{
                        label: "Temperature (°C)",
                        data: temperature,
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 2,
                        fill: false
                    }]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            display: true
                        }
                    },

                    scales: {
                        x: {
                            ticks: {
                                maxTicksLimit: 6
                            }
                        },

                        y: {
                            beginAtZero: false
                        }
                    }
                }
            }
        );


        // -------------------------------
        // HUMIDITY
        // -------------------------------

        if (humidityChart) {
            humidityChart.destroy();
        }

        humidityChart = new Chart(
            document.getElementById("humidityChart"),
            {
                type: "line",

                data: {
                    labels: labels,

                    datasets: [{
                        label: "Humidity (%)",
                        data: humidity,
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 2,
                        fill: false
                    }]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            display: true
                        }
                    },

                    scales: {
                        x: {
                            ticks: {
                                maxTicksLimit: 6
                            }
                        },

                        y: {
                            beginAtZero: true
                        }
                    }
                }
            }
        );


        // -------------------------------
        // SOIL
        // -------------------------------

        if (soilChart) {
            soilChart.destroy();
        }

        soilChart = new Chart(
            document.getElementById("soilChart"),
            {
                type: "line",

                data: {
                    labels: labels,

                    datasets: [{
                        label: "Soil Sensor",
                        data: soil,
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 2,
                        fill: false
                    }]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            display: true
                        }
                    },

                    scales: {
                        x: {
                            ticks: {
                                maxTicksLimit: 6
                            }
                        },

                        y: {
                            beginAtZero: true
                        }
                    }
                }
            }
        );


        // -------------------------------
        // DISTANCE
        // -------------------------------

        if (distanceChart) {
            distanceChart.destroy();
        }

        distanceChart = new Chart(
            document.getElementById("distanceChart"),
            {
                type: "line",

                data: {
                    labels: labels,

                    datasets: [{
                        label: "Distance (cm)",
                        data: distance,
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 2,
                        fill: false
                    }]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            display: true
                        }
                    },

                    scales: {
                        x: {
                            ticks: {
                                maxTicksLimit: 6
                            }
                        },

                        y: {
                            beginAtZero: true
                        }
                    }
                }
            }
        );

    } catch (error) {

        console.error(
            "Sensor history error:",
            error
        );

    }
}
const translations = {
    en: {
        subtitle: "AI-powered agricultural rover console",
        language: "Language", auto: "Auto", manual: "Manual",
        driveMode: "Drive Mode", driveControl: "Drive Control",
        cameraDetection: "Camera & AI Detection", detection: "Detection:",
        cameraPanTilt: "Camera Pan / Tilt", cameraScan: "Camera Scan",
        plantHealth: "Plant Health", scanPlant: "Scan Plant",
        fieldConditions: "Field Conditions", obstacle: "Obstacle", pump: "Pump",
        pumpOn: "Pump ON", pumpOff: "Pump OFF",
        soilMoisture: "Soil Moisture", temperature: "Temperature", humidity: "Humidity",
        weatherIntelligence: "Weather Intelligence", condition: "Condition",
        rainProbability: "Rain Probability", forecastRain: "Forecast Rain",
        wind: "Wind", forecastHigh: "Forecast High",
        irrigation: "Agricultural Intelligence", decisionLabel: "Decision:",
        recommended: "RECOMMENDED", notRequired: "NOT REQUIRED", delay: "DELAY", suspended: "SUSPENDED",
        rainRisk: "Rain Risk", floodRisk: "Flood Risk", heatRisk: "Heat Risk", overallRisk: "Overall Risk",
        gps: "Rover GPS Location", latitude: "Latitude", longitude: "Longitude", openLocation: "Open Rover Location",
        healthy: "HEALTHY", unhealthy: "UNHEALTHY", uncertain: "UNCERTAIN",
        noPest: "No Pest Detected", pestDetected: "Pest Detected",
        noDeficiency: "No Deficiency Detected", deficiencyDetected: "Possible Nutrient Deficiency",
        checkingEsp: "Checking ESP32...", espOnline: "● ESP32 ONLINE", espOffline: "● ESP32 OFFLINE",
        requestingLocation: "Requesting laptop location...",
        requestingPermission: "Requesting laptop location permission...",
        locationDenied: "Laptop location permission denied. Weather unavailable.",
        locationSet: "Weather location: Laptop GPS",
        locationUploadFailed: "Weather location upload failed",
        gpsFix: "GPS FIX — Rover location", gpsWaiting: "Waiting for NEO-6M GPS fix",
        noGeolocation: "Browser does not support location."
    },
    hi: {
        subtitle: "AI-संचालित कृषि रोवर कंसोल",
        language: "भाषा", auto: "ऑटो", manual: "मैनुअल",
        driveMode: "ड्राइव मोड", driveControl: "ड्राइव नियंत्रण",
        cameraDetection: "कैमरा और AI डिटेक्शन", detection: "डिटेक्शन:",
        cameraPanTilt: "कैमरा पैन / टिल्ट", cameraScan: "कैमरा स्कैन",
        plantHealth: "पौधे का स्वास्थ्य", scanPlant: "पौधे की जाँच करें",
        fieldConditions: "खेत की स्थिति", obstacle: "बाधा", pump: "पंप",
        pumpOn: "पंप चालू", pumpOff: "पंप बंद",
        soilMoisture: "मिट्टी की नमी", temperature: "तापमान", humidity: "आर्द्रता",
        weatherIntelligence: "मौसम जानकारी", condition: "स्थिति",
        rainProbability: "बारिश की संभावना", forecastRain: "पूर्वानुमानित बारिश",
        wind: "हवा", forecastHigh: "अधिकतम तापमान पूर्वानुमान",
        irrigation: "कृषि बुद्धिमत्ता", decisionLabel: "निर्णय:",
        recommended: "सिंचाई आवश्यक", notRequired: "सिंचाई आवश्यक नहीं", delay: "सिंचाई स्थगित", suspended: "सिंचाई बंद",
        rainRisk: "बारिश का जोखिम", floodRisk: "बाढ़ का जोखिम", heatRisk: "गर्मी का जोखिम", overallRisk: "कुल जोखिम",
        gps: "रोवर GPS स्थान", latitude: "अक्षांश", longitude: "देशांतर", openLocation: "रोवर स्थान खोलें",
        healthy: "स्वस्थ", unhealthy: "अस्वस्थ", uncertain: "अनिश्चित",
        noPest: "कोई कीट नहीं मिला", pestDetected: "कीट का पता चला",
        noDeficiency: "पोषक तत्वों की कमी नहीं मिली", deficiencyDetected: "पोषक तत्वों की संभावित कमी",
        checkingEsp: "ESP32 जाँच रहे हैं...", espOnline: "● ESP32 ऑनलाइन", espOffline: "● ESP32 ऑफ़लाइन",
        requestingLocation: "लैपटॉप स्थान का अनुरोध...",
        requestingPermission: "लैपटॉप स्थान अनुमति का अनुरोध...",
        locationDenied: "लैपटॉप स्थान अनुमति अस्वीकृत। मौसम अनुपलब्ध।",
        locationSet: "मौसम स्थान: लैपटॉप GPS",
        locationUploadFailed: "मौसम स्थान अपलोड विफल",
        gpsFix: "GPS फिक्स — रोवर स्थान", gpsWaiting: "NEO-6M GPS फिक्स की प्रतीक्षा",
        noGeolocation: "ब्राउज़र स्थान का समर्थन नहीं करता।"
    },
    bn: {
        subtitle: "AI-চালিত কৃষি রোভার কনসোল",
        language: "ভাষা", auto: "অটো", manual: "ম্যানুয়াল",
        driveMode: "ড্রাইভ মোড", driveControl: "ড্রাইভ নিয়ন্ত্রণ",
        cameraDetection: "ক্যামেরা ও AI শনাক্তকরণ", detection: "শনাক্তকরণ:",
        cameraPanTilt: "ক্যামেরা প্যান / টিল্ট", cameraScan: "ক্যামেরা স্ক্যান",
        plantHealth: "গাছের স্বাস্থ্য", scanPlant: "গাছ পরীক্ষা করুন",
        fieldConditions: "ক্ষেত্রের অবস্থা", obstacle: "বাধা", pump: "পাম্প",
        pumpOn: "পাম্প চালু", pumpOff: "পাম্প বন্ধ",
        soilMoisture: "মাটির আর্দ্রতা", temperature: "তাপমাত্রা", humidity: "আর্দ্রতা",
        weatherIntelligence: "আবহাওয়ার তথ্য", condition: "অবস্থা",
        rainProbability: "বৃষ্টির সম্ভাবনা", forecastRain: "পূর্বাভাসিত বৃষ্টি",
        wind: "বাতাস", forecastHigh: "সর্বোচ্চ তাপমাত্রার পূর্বাভাস",
        irrigation: "কৃষি বুদ্ধিমত্তা", decisionLabel: "সিদ্ধান্ত:",
        recommended: "সেচ প্রয়োজন", notRequired: "সেচ প্রয়োজন নেই", delay: "সেচ স্থগিত", suspended: "সেচ বন্ধ",
        rainRisk: "বৃষ্টির ঝুঁকি", floodRisk: "বন্যার ঝুঁকি", heatRisk: "তাপের ঝুঁকি", overallRisk: "সামগ্রিক ঝুঁকি",
        gps: "রোভার GPS অবস্থান", latitude: "অক্ষাংশ", longitude: "দ্রাঘিমাংশ", openLocation: "রোভারের অবস্থান খুলুন",
        healthy: "সুস্থ", unhealthy: "অসুস্থ", uncertain: "অনিশ্চিত",
        noPest: "কোনও পোকা শনাক্ত হয়নি", pestDetected: "পোকা শনাক্ত হয়েছে",
        noDeficiency: "পুষ্টির ঘাটতি শনাক্ত হয়নি", deficiencyDetected: "পুষ্টির সম্ভাব্য ঘাটতি",
        checkingEsp: "ESP32 পরীক্ষা করা হচ্ছে...", espOnline: "● ESP32 অনলাইন", espOffline: "● ESP32 অফলাইন",
        requestingLocation: "ল্যাপটপের অবস্থান অনুরোধ করা হচ্ছে...",
        requestingPermission: "ল্যাপটপ অবস্থান অনুমতির অনুরোধ করা হচ্ছে...",
        locationDenied: "ল্যাপটপ অবস্থানের অনুমতি প্রত্যাখ্যাত। আবহাওয়া অনুপলব্ধ।",
        locationSet: "আবহাওয়ার অবস্থান: ল্যাপটপ GPS",
        locationUploadFailed: "অবস্থান আপলোড ব্যর্থ হয়েছে",
        gpsFix: "GPS ফিক্স — রোভারের অবস্থান", gpsWaiting: "NEO-6M GPS ফিক্সের অপেক্ষায়",
        noGeolocation: "ব্রাউজার অবস্থান সমর্থন করে না।"
    }
};

const irrigationStatusKeyMap = {
    "RECOMMENDED": "recommended", "NOT REQUIRED": "notRequired",
    "DELAY": "delay", "SUSPENDED": "suspended", "WAIT": "notRequired"
};

let currentLanguage = "en";
let lastIrrigationStatus = null;

function t(key) {
    const dict = translations[currentLanguage];
    return (dict && dict[key]) ? dict[key] : (translations.en[key] || key);
}

function renderIrrigationText() {
    const irrigation = document.getElementById("irrigation");
    if (!irrigation) return;
    const key = irrigationStatusKeyMap[lastIrrigationStatus];
    irrigation.innerText = key ? t(key) : (lastIrrigationStatus || irrigation.innerText);
}

// Re-renders any JS-driven status text (ESP32 status, GPS status, location box)
// based on the "kind" tag stored on the element, so switching language mid-session
// updates dynamic text too, not just static labels.
function renderStatusElements() {
    const esp = document.getElementById("espStatus");
    const kind = esp.dataset.statusKind;
    if (kind === "checking") esp.innerText = t("checkingEsp");
    else if (kind === "online") esp.innerText = t("espOnline");
    else if (kind === "offline") esp.innerText = t("espOffline");

    const gpsStatus = document.getElementById("gpsStatus");
    const gpsKind = gpsStatus.dataset.statusKind;
    if (gpsKind === "waiting") gpsStatus.innerText = t("gpsWaiting");
    else if (gpsKind === "fix") gpsStatus.innerText = t("gpsFix");

    const weatherLoc = document.getElementById("weatherLocationStatus");
    const wlKind = weatherLoc.dataset.statusKind;
    if (wlKind === "requesting") weatherLoc.innerText = t("requestingLocation");
    else if (wlKind === "requestingPermission") weatherLoc.innerText = t("requestingPermission");
    else if (wlKind === "denied") weatherLoc.innerText = t("locationDenied");
    else if (wlKind === "set") weatherLoc.innerText = t("locationSet");
    else if (wlKind === "uploadFailed") weatherLoc.innerText = t("locationUploadFailed");
    else if (wlKind === "noSupport") weatherLoc.innerText = t("noGeolocation");
}

function changeLanguage(language) {
    currentLanguage = language;
    document.querySelectorAll("[data-i18n]").forEach(element => {
        element.innerText = t(element.dataset.i18n);
    });
    renderIrrigationText();
    renderStatusElements();
    localStorage.setItem("agrivise_language", language);
}

console.log("DASHBOARD SCRIPT LOADED — build " + Date.now());

let commandBusy = false;

async function sendCommand(path, button) {
    if (commandBusy) return;
    commandBusy = true;
    const status = document.getElementById("espStatus");
    if (button) button.disabled = true;
    try {
        status.dataset.statusKind = "sending";
        status.innerText = "..."; // brief transient state, not worth a translation key
        status.className = "status";
        const response = await fetch(path + "?t=" + Date.now(), {
            method:"GET", cache:"no-store", headers:{"Cache-Control":"no-cache"}
        });
        if (!response.ok) throw new Error("HTTP " + response.status);
        const result = await response.json();
        if (result.success) {
            status.dataset.statusKind = "online";
            status.innerText = t("espOnline");
            status.className = "status online";
            updateSensors();
        } else {
            status.dataset.statusKind = "offline";
            status.innerText = t("espOffline");
            status.className = "status offline";
        }
    } catch(error) {
        status.dataset.statusKind = "offline";
        status.innerText = t("espOffline");
        status.className = "status offline";
    } finally {
        if (button) button.disabled = false;
        commandBusy = false;
    }
}
window.sendCommand = sendCommand;

function requestLaptopLocation() {
    const status = document.getElementById("weatherLocationStatus");
    if (!navigator.geolocation) {
        status.dataset.statusKind = "noSupport";
        status.innerText = t("noGeolocation");
        return;
    }
    status.dataset.statusKind = "requestingPermission";
    status.innerText = t("requestingPermission");
    navigator.geolocation.getCurrentPosition(
        async function(position) {
            const { latitude, longitude, accuracy } = position.coords;
            try {
                const response = await fetch("/set_weather_location", {
                    method:"POST",
                    headers:{"Content-Type":"application/json"},
                    cache:"no-store",
                    body:JSON.stringify({ latitude, longitude, accuracy })
                });
                const result = await response.json();
                if (result.success) {
                    status.dataset.statusKind = "set";
                    status.innerText = t("locationSet");
                    status.className = "location-box online";
                    updateIntelligence();
                }
            } catch(error) {
                status.dataset.statusKind = "uploadFailed";
                status.innerText = t("locationUploadFailed");
                status.className = "location-box offline";
            }
        },
        function(error) {
            status.dataset.statusKind = "denied";
            status.innerText = t("locationDenied");
            status.className = "location-box offline";
        },
        { enableHighAccuracy:true, timeout:15000, maximumAge:300000 }
    );
}

let sensorBusy = false;
async function updateSensors() {
    if (sensorBusy) return;
    sensorBusy = true;
    try {
        const response = await fetch("/sensor_data?t=" + Date.now(), { method:"GET", cache:"no-store" });
        if (!response.ok) throw new Error("Sensor HTTP error");
        const data = await response.json();

        document.getElementById("temperature").innerText = data.temperature;
        document.getElementById("humidity").innerText = data.humidity;
        document.getElementById("soil").innerText = data.soil;
        document.getElementById("distance").innerText = data.distance;
        document.getElementById("mode").innerText = data.mode;

        const pump = document.getElementById("pump");
        pump.innerText = data.pump;
        pump.className = (data.pump && data.pump.toString().toUpperCase() === "ON") ? "badge badge-on" : "badge badge-off";

        const gpsStatus = document.getElementById("gpsStatus");
        if (data.lat !== undefined && data.lon !== undefined) {
            document.getElementById("lat").innerText = data.lat;
            document.getElementById("lon").innerText = data.lon;
            gpsStatus.dataset.statusKind = "fix";
            gpsStatus.innerText = t("gpsFix");
            gpsStatus.className = "location-box online";
            document.getElementById("mapLink").href = "https://www.google.com/maps?q=" + data.lat + "," + data.lon;
        } else {
            gpsStatus.dataset.statusKind = "waiting";
            gpsStatus.innerText = t("gpsWaiting");
            gpsStatus.className = "location-box";
        }

        const esp = document.getElementById("espStatus");
        if (!commandBusy) {
            esp.dataset.statusKind = "online";
            esp.innerText = t("espOnline");
            esp.className = "status online";
        }
    } catch(error) {
        const esp = document.getElementById("espStatus");
        esp.dataset.statusKind = "offline";
        esp.innerText = t("espOffline");
        esp.className = "status offline";
    } finally {
        sensorBusy = false;
    }
}

let intelligenceBusy = false;
async function updateIntelligence() {
    if (intelligenceBusy) return;
    intelligenceBusy = true;
    try {
        const response = await fetch("/agri_intelligence?t=" + Date.now(), { method:"GET", cache:"no-store" });
        if (!response.ok) throw new Error("Intelligence HTTP error");
        const result = await response.json();
        const weather = result.weather;
        const decision = result.decision;

        document.getElementById("weatherCondition").innerText = weather.condition;
        document.getElementById("weatherTemperature").innerText = weather.temperature;
        document.getElementById("rainProbability").innerText = weather.rain_probability;
        document.getElementById("rainForecast").innerText = weather.rain_forecast;
        document.getElementById("wind").innerText = weather.wind_speed;
        document.getElementById("forecastMax").innerText = weather.forecast_max;

        const irrigation = document.getElementById("irrigation");
        irrigation.className = "decision";
        if (decision.irrigation === "RECOMMENDED") irrigation.classList.add("recommended");
        else if (decision.irrigation === "DELAY" || decision.irrigation === "SUSPENDED") irrigation.classList.add("delay");
        else irrigation.classList.add("wait");

        lastIrrigationStatus = decision.irrigation;
        renderIrrigationText();

        document.getElementById("reason").innerText = decision.reason;
        document.getElementById("heatRisk").innerText = decision.heat_risk;
        document.getElementById("rainRisk").innerText = decision.rain_risk;
        document.getElementById("floodRisk").innerText = decision.flood_risk;
        document.getElementById("overallRisk").innerText = decision.risk;
    } catch(error) {
        console.log("Intelligence error:", error);
    } finally {
        intelligenceBusy = false;
    }
}

// ============================================================
// AI INTER-CROP ADVISOR
// ============================================================

async function getIntercropRecommendation() {

    const previousCrop =
        document.getElementById(
            "previousCrop"
        ).value;

    const nextCrop =
        document.getElementById(
            "nextCrop"
        ).value;

    const harvestDate =
        document.getElementById(
            "harvestDate"
        ).value;

    const nextPlantingDate =
        document.getElementById(
            "nextPlantingDate"
        ).value;

    const soilImage =
        document.getElementById(
            "soilImage"
        ).files[0];


    const validation =
        document.getElementById(
            "intercropValidation"
        );


    const resultBox =
        document.getElementById(
            "intercropResult"
        );


    const button =
        document.getElementById(
            "intercropButton"
        );


    // --------------------------------------------------------
    // VALIDATION
    // --------------------------------------------------------

    if (!previousCrop) {

        showIntercropMessage(
            "❌ Please select the previous crop.",
            "error"
        );

        return;
    }


    if (!nextCrop) {

        showIntercropMessage(
            "❌ Please select the next planned crop.",
            "error"
        );

        return;
    }


    if (!harvestDate) {

        showIntercropMessage(
            "❌ Please select the previous crop harvest date.",
            "error"
        );

        return;
    }


    if (!nextPlantingDate) {

        showIntercropMessage(
            "❌ Please select the next crop planting date.",
            "error"
        );

        return;
    }


    const harvest =
        new Date(harvestDate);

    const planting =
        new Date(nextPlantingDate);


    const gapDays =
        Math.ceil(
            (planting - harvest)
            / (1000 * 60 * 60 * 24)
        );


    if (gapDays <= 0) {

        showIntercropMessage(
            "❌ Invalid dates: next planting date must be after the harvest date.",
            "error"
        );

        return;
    }


    if (gapDays < 7) {

        showIntercropMessage(
            `⚠️ Only ${gapDays} days are available. A useful inter-crop may not fit this window.`,
            "warning"
        );

    }

    else {

        showIntercropMessage(
            `✅ Valid ${gapDays}-day inter-crop window. Ready for AI analysis.`,
            "success"
        );

    }


    // --------------------------------------------------------
    // IMAGE VALIDATION
    // --------------------------------------------------------

    if (soilImage) {

        const allowedTypes = [
            "image/jpeg",
            "image/png",
            "image/webp"
        ];


        if (
            !allowedTypes.includes(
                soilImage.type
            )
        ) {

            showIntercropMessage(
                "❌ Soil image must be JPG, PNG or WEBP.",
                "error"
            );

            return;
        }


        if (
            soilImage.size >
            5 * 1024 * 1024
        ) {

            showIntercropMessage(
                "❌ Soil image must be smaller than 5 MB.",
                "error"
            );

            return;
        }

    }


    // --------------------------------------------------------
    // PREPARE FORM
    // --------------------------------------------------------

    const formData =
        new FormData();


    formData.append(
        "previous_crop",
        previousCrop
    );

    formData.append(
        "next_crop",
        nextCrop
    );

    formData.append(
        "harvest_date",
        harvestDate
    );

    formData.append(
        "next_planting_date",
        nextPlantingDate
    );


    if (soilImage) {

        formData.append(
            "soil_image",
            soilImage
        );

    }


    // --------------------------------------------------------
    // BUTTON
    // --------------------------------------------------------

    button.disabled = true;

    button.innerHTML =
        '<i class="fa-solid fa-spinner fa-spin"></i> AI Analyzing...';


    resultBox.innerHTML = "";


    try {

        const response =
            await fetch(
                "/api/intercrop-recommendation",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!response.ok ||
            !data.success) {

            throw new Error(
                data.error ||
                "AI recommendation failed."
            );

        }


        renderIntercropResult(
            data
        );


    }

    catch (error) {

        showIntercropMessage(
            "❌ " + error.message,
            "error"
        );

    }

    finally {

        button.disabled = false;

        button.innerHTML =
            '<i class="fa-solid fa-brain"></i> Analyze Gap With AI';

    }

}
function renderIntercropResult(data) {

    const resultBox =
        document.getElementById(
            "intercropResult"
        );


    let html = `

        <div class="info">

            <strong>
                🌱 AI Inter-Crop Analysis
            </strong>

            <p>
                Available farming gap:
                <strong>
                    ${data.gap_days} days
                </strong>
            </p>

            <p>
                ${data.message || ""}
            </p>

        </div>

    `;


    if (
        !data.recommendations ||
        data.recommendations.length === 0
    ) {

        html += `

            <div class="info">

                ⚠️
                No suitable recommendation
                was returned for this gap.

            </div>

        `;

        resultBox.innerHTML = html;

        return;
    }


    data.recommendations.forEach(
        (item, index) => {

            html += `

                <div
                    class="info"
                    style="margin-top:10px;"
                >

                    <h3
                        style="margin-top:0;"
                    >

                        🌱 ${index + 1}.
                        ${escapeHtml(item.crop)}

                    </h3>


                    <div class="row">

                        <span>
                            Duration
                        </span>

                        <strong>
                            ${item.duration_days}
                            days
                        </strong>

                    </div>


                    <div class="row">

                        <span>
                            Suitability
                        </span>

                        <strong>
                            ${escapeHtml(
                                item.suitability
                            )}
                        </strong>

                    </div>


                    <p>

                        <strong>
                            Why:
                        </strong>

                        ${escapeHtml(
                            item.reason
                        )}

                    </p>


                    <p>

                        <strong>
                            ⚠️ Caution:
                        </strong>

                        ${escapeHtml(
                            item.caution
                        )}

                    </p>

                </div>

            `;

        }
    );


    resultBox.innerHTML =
        html;
}
function showIntercropMessage(
    message,
    type
) {

    const box =
        document.getElementById(
            "intercropValidation"
        );


    box.style.display = "block";

    box.innerText = message;


    if (type === "error") {

        box.style.borderColor =
            "var(--red)";

    }

    else if (type === "warning") {

        box.style.borderColor =
            "var(--rust)";

    }

    else {

        box.style.borderColor =
            "var(--green)";

    }

}


function escapeHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}
window.addEventListener("DOMContentLoaded", function() {
    const savedLanguage = localStorage.getItem("agrivise_language") || "en";
    document.getElementById("languageSelect").value = savedLanguage;
    changeLanguage(savedLanguage);

    requestLaptopLocation();
    updateSensors();
    updateIntelligence();
    loadSensorHistory();
});

setInterval(updateSensors, 1000);
setInterval(updateIntelligence, 30000);
setInterval(requestLaptopLocation, 600000);
setInterval(loadSensorHistory, 10000);
