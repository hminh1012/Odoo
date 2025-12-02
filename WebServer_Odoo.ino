#include <Arduino.h>
#include <WiFi.h>
#include <AsyncTCP.h>           // Async TCP Library
#include <ESPAsyncWebServer.h>  // Async Web Server Library
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "esp_camera.h"
#include "base64.h"       
#include "soc/soc.h"      
#include "soc/rtc_cntl_reg.h"

// ================= NETWORK & SERVER CONFIGURATION =================
const char* ssid = "Bubuchacha";
const char* password = "umbalaxibua";
// Replace with your Odoo server IP
const char* serverUrl = "http://10.157.98.1:8069/api/transport/attendance";

// ================= FIXED DATA INFORMATION =================
const char* vehicle_id = "DN-01";


// ================= VIRTUAL GPS GENERATOR (DA NANG) =================
String getRandomDaNangGPS() {
  // DA NANG BOUNDARIES (Approximate Rectangle)
  // Min Lat (South): 16.0300 | Max Lat (North): 16.0900
  // Min Lon (West): 108.1900 | Max Lon (East): 108.2600

  float latMin = 16.0300;
  float latMax = 16.0900;
  float lonMin = 108.1900;
  float lonMax = 108.2600;

  // Generate random float between 0.0 and 1.0
  float r1 = (float)esp_random() / UINT32_MAX; 
  float r2 = (float)esp_random() / UINT32_MAX;

  // Calculate random coordinate
  float randLat = latMin + (r1 * (latMax - latMin));
  float randLon = lonMin + (r2 * (lonMax - lonMin));

  // Return formatted string "Lat, Lon"
  return String(randLat, 6) + ", " + String(randLon, 6);
}



// ================= CAMERA PINS (AI-THINKER) =================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ================= ASYNC WEB SERVER OBJECT =================
AsyncWebServer server(80);

// ================= WEB INTERFACE (HTML) =================
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Smart Bus Attendance</title>
  <style>
    /* --- GENERAL STRUCTURE --- */
    body { 
        margin: 0; 
        padding: 0; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        background-color: #f4f6f9; 
        color: #333;
    }

    /* --- HEADER (Updated Color) --- */
    .header {
        background-color: #980000; /* Updated color */
        padding: 15px 0;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        color: white;
    }
    .header img {
        height: 80px;
        width: auto;
        display: block;
        margin: 0 auto 10px auto;
        background: white;
        border-radius: 50%;
        padding: 5px;
    }
    .header h1 {
        margin: 0;
        font-size: 18px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .header p {
        margin: 5px 0 0 0;
        font-size: 13px;
        opacity: 0.9;
    }

    /* --- CONTAINER & CARD --- */
    .main-container {
        padding: 20px;
        display: flex;
        justify-content: center;
    }
    .card {
        background: white;
        width: 100%;
        max-width: 400px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        padding: 25px;
        text-align: left;
    }
    
    /* --- FORM ELEMENTS --- */
    .form-group { margin-bottom: 20px; }
    label { 
        display: block; 
        font-weight: 600; 
        margin-bottom: 8px; 
        color: #444; 
        font-size: 14px;
    }
    input[type="text"], select {
        width: 100%;
        padding: 12px;
        border: 1px solid #ddd;
        border-radius: 6px;
        font-size: 16px;
        box-sizing: border-box;
        transition: border 0.3s;
    }
    input:focus, select:focus {
        border-color: #980000;
        outline: none;
    }

    /* --- BUTTON --- */
    button {
        width: 100%;
        padding: 14px;
        background-color: #22e65c;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        transition: background 0.3s;
        text-transform: uppercase;
    }
    button:hover { background-color: #d35400; }
    button:disabled { background-color: #bdc3c7; cursor: not-allowed; }

    /* --- UTILITIES --- */
    .notify-box {
        font-size: 13px;
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 10px;
        display: none;
        border: 1px solid #c8e6c9;
    }
    .loader {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #980000;
        border-radius: 50%;
        width: 25px;
        height: 25px;
        animation: spin 1s linear infinite;
        margin: 15px auto;
        display: none;
    }
    #status-text {
        text-align: center;
        margin-top: 15px;
        font-weight: bold;
        color: #555;
    }
    .footer {
        text-align: center;
        font-size: 12px;
        color: #888;
        margin-top: 30px;
        padding-bottom: 20px;
    }

    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
  </style>
</head>
<body>

  <div class="header">
    <img src="data:image/png;base64,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" alt="DUT Logo">
    
    <h1>DANANG UNIVERSITY OF SCIENCE AND TECHNOLOGY</h1>
    <p>Smart Attendance System</p>
  </div>

  <div class="main-container">
    <div class="card">
      
      <div id="saved-msg" class="notify-box">
        Student ID auto-filled from device memory.
      </div>

      <div class="form-group">
        <label for="student_code">Student ID:</label>
        <input type="text" id="student_code" placeholder="Enter ID or scan QR..." autocomplete="off">
      </div>

      <div class="form-group">
        <label for="type">Attendance Type:</label>
        <select id="type">
          <option value="pickup"> Pickup (Boarding)</option>
          <option value="dropoff"> Dropoff (Alighting)</option>
        </select>
      </div>
      
      <button id="btn" onclick="capture()">CONFIRM & CAPTURE</button>
      
      <div class="loader" id="loader"></div>
      <p id="status-text">Ready...</p>

    </div>
  </div>

  <div class="footer">
    &copy; 2025 Smart Transport System. Powered by DUT IoT Lab.
  </div>

  <script>
    // === AUTO-FILL LOGIC ===
    window.onload = function() {
        const inputField = document.getElementById("student_code");
        const msgField = document.getElementById("saved-msg");
        
        // 1. Check URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const codeFromUrl = urlParams.get('code');

        if (codeFromUrl) {
            // CASE 1: Code found in URL (QR Scan)
            inputField.value = codeFromUrl;
            localStorage.setItem("my_student_code", codeFromUrl);
            
            msgField.innerText = " Loaded ID from QR Code";
            msgField.style.display = "block";
        } else {
            // CASE 2: No URL param -> Check LocalStorage
            var savedCode = localStorage.getItem("my_student_code");
            if (savedCode) {
                inputField.value = savedCode;
                msgField.style.display = "block";
            }
        }
    }

    function capture() {
      var btn = document.getElementById("btn");
      var status = document.getElementById("status-text");
      var loader = document.getElementById("loader");
      var code = document.getElementById("student_code").value;
      var type = document.getElementById("type").value;
      
      if(code.trim() === "") {
        alert("Please enter Student ID!");
        return;
      }

      // Save to local storage
      localStorage.setItem("my_student_code", code);

      btn.disabled = true;
      btn.innerHTML = "PROCESSING...";
      status.innerHTML = "Connecting to camera & server...";
      status.style.color = "#555";
      loader.style.display = "block";

      var xhr = new XMLHttpRequest();
      var url = "/capture?code=" + encodeURIComponent(code) + "&type=" + encodeURIComponent(type);
      
      xhr.open("GET", url, true);
      xhr.onload = function() {
        loader.style.display = "none";
        btn.disabled = false;
        btn.innerHTML = "CONFIRM & CAPTURE";
        
        if (xhr.status === 200) {
          if(xhr.responseText.includes("Success")) {
             status.innerHTML = "Attendance Logged Successfully!";
             status.style.color = "green";
          } else {
             status.innerHTML = " Error: " + xhr.responseText;
             status.style.color = "#d35400";
          }
        } else {
          status.innerHTML = " Connection Failed!";
          status.style.color = "red";
        }
      };
      xhr.onerror = function() {
        loader.style.display = "none";
        btn.disabled = false;
        btn.innerHTML = "RETRY";
        status.innerHTML = "Cannot connect to server!";
        status.style.color = "red";
      };
      xhr.send();
    }
  </script>
</body>
</html>
)rawliteral";

// ================= INITIALIZATION FUNCTIONS =================
void initCamera();
String captureAndEncodeImage();
// Update sendToOdoo function to accept dynamic parameters
String sendToOdoo(String code, String attType); 

void setup() {
  Serial.begin(115200);
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  // 1. Connect to WiFi
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("Web Server IP: http://"); 
  Serial.println(WiFi.localIP());

  // 2. Initialize Camera
  initCamera();

  // 3. Configure Async Web Server
  // Root route: Return HTML interface
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send(200, "text/html", index_html);
  });

  // Capture route: Receive parameters from URL and process
  server.on("/capture", HTTP_GET, [](AsyncWebServerRequest *request){
    String code = "UNKNOWN";
    String attType = "pickup";

    // Get parameters from URL (e.g., /capture?code=123&type=dropoff)
    if (request->hasParam("code")) {
      code = request->getParam("code")->value();
    }
    if (request->hasParam("type")) {
      attType = request->getParam("type")->value();
    }

    Serial.println("Request: Code=" + code + ", Type=" + attType);

    // Call Odoo send function with dynamic data
    String result = sendToOdoo(code, attType);
    request->send(200, "text/plain", result);
  });

  // Start Server
  server.begin();
  Serial.println("Async HTTP server started");
}

void loop() {
  // With AsyncWebServer, loop is empty, server runs in background
  delay(1000);
}

// ================= CAMERA & ODOO LOGIC =================
void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if(psramFound()){
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 12;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed 0x%x", err);
    return;
  }

  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_whitebal(s, 1);
    s->set_awb_gain(s, 1);
    s->set_wb_mode(s, 0);
    s->set_hmirror(s, 1);
    s->set_vflip(s, 1);
  }
}

String captureAndEncodeImage() {
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Capture failed");
    return "";
  }
  String imageFile = base64::encode(fb->buf, fb->len);
  esp_camera_fb_return(fb);
  return imageFile;
}

// Updated to receive input parameters
String sendToOdoo(String code, String attType) {
  if (WiFi.status() != WL_CONNECTED) return "WiFi Disconnected";

  String imageBase64 = captureAndEncodeImage();
  if(imageBase64 == "") return "Camera Error";
  String gps_coords = getRandomDaNangGPS();

  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");

  // Calculate buffer size
  size_t capacity = imageBase64.length() + 1024; 
  DynamicJsonDocument doc(capacity);

  JsonObject params = doc.createNestedObject("params");
  params["student_code"] = code;     // Use dynamic variable from Web
  params["vehicle_id"] = vehicle_id;
  params["gps"] = gps_coords;
  params["type"] = attType;          // Use dynamic variable from Web
  params["image"] = imageBase64;

  String requestBody;
  serializeJson(doc, requestBody);

  Serial.println("Sending to Odoo: Code=" + code + ", Type=" + attType);
  int httpResponseCode = http.POST(requestBody);
  
  String resultMsg = "";

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println(httpResponseCode);
    if(httpResponseCode == 200) {
        resultMsg = "Success (200 OK)";
    } else {
        resultMsg = "Error Server: " + String(httpResponseCode);
    }
  } else {
    resultMsg = "Error HTTP: " + http.errorToString(httpResponseCode);
    Serial.println(resultMsg);
  }
  
  http.end();
  return resultMsg;
}