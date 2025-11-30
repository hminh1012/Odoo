import urllib.request
import json
import base64
import os

def get_input(prompt, default_value):
    value = input(f"{prompt} [{default_value}]: ").strip()
    return value if value else default_value

def encode_image(image_path):
    if not image_path or not os.path.exists(image_path):
        return False
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        print(f"Error encoding image: {e}")
        return False

# 1. Configuration
url = "http://localhost:8069/api/transport/attendance"

print("--- ODOO TRANSPORT API TESTER ---")

# 2. Get Data from User
student_code = get_input("Student Code", "123210091")
vehicle_id = get_input("Vehicle ID", "BUS-29A-9999")
gps = get_input("GPS Coordinates", "10.762622, 106.660172")
attendance_type = get_input("Type (pickup/dropoff)", "pickup")
image_path = get_input("Image Path (optional)", "")

data = {
    "params": {
        "student_code": student_code, 
        "vehicle_id": vehicle_id,
        "gps": gps,
        "type": attendance_type,
        "image": encode_image(image_path) if image_path else False
    }
}

# 3. Send Request
headers = {'Content-Type': 'application/json'}
print(f"\nSending data to {url}...")
print(json.dumps(data, indent=2))

try:
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
    response = urllib.request.urlopen(req)
    result = response.read().decode('utf-8')
    
    print("\nRESPONSE:")
    try:
        # Try to pretty print JSON response
        json_result = json.loads(result)
        print(json.dumps(json_result, indent=2))
    except:
        print(result)
        
except Exception as e:
    print(f"\nERROR: {e}")

input("\nPress Enter to exit...")
