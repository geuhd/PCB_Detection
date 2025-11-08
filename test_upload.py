import requests
import os

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/login" 
UPLOAD_URL = f"{BASE_URL}/detections"

# IMPORTANT: REPLACE with your actual application credentials
USERNAME = "YOUR_APP_USERNAME" 
PASSWORD = "YOUR_APP_PASSWORD"

# 2. Path to the image file (Uses the correct, absolute path you provided)
FILE_NAME = r"C:\Users\miken\Desktop\THESIS\pcb.yolov8\train\images\DuetWIFI_Top_jpg.rf.8664cc628106c8eba7891ed726aee8bb.jpg"

def get_jwt_token(username, password):
    """Performs the OAuth2 login request and returns the access token."""
    print("\n--- Attempting Login ---")
    
    # OAuth2 token endpoint expects form-urlencoded data (key/value pairs)
    login_data = {
        "username": "prince@gmail.com",
        "password": "pass123"
    }
    
    try:
        response = requests.post(LOGIN_URL, data=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                print("✅ Successfully retrieved JWT Token.")
                return access_token
            else:
                print("❌ Login successful, but 'access_token' not found in response.")
                return None
        else:
            print(f"❌ Login failed. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not reach login server at {LOGIN_URL}. Is your server running?")
        return None

# --- Main Execution ---
ACCESS_TOKEN = get_jwt_token(USERNAME, PASSWORD)

if ACCESS_TOKEN:
    print("\n--- Attempting File Upload with Token ---")
    
    # 3. Authorization Header constructed with the obtained token
    HEADERS = {
        "Authorization": f"Bearer {ACCESS_TOKEN}" 
    }
    
    FORM_DATA = {
        "title": "my_pcb_test_upload",
        "published": "True"
    }

    files = None # Initialize outside try-block
    try:
        if not os.path.exists(FILE_NAME):
            print(f"❌ Error: File '{FILE_NAME}' not found.")
        else:
            # Open the file and prepare the multipart/form-data payload
            files = {
                'file': (os.path.basename(FILE_NAME), open(FILE_NAME, 'rb'), 'image/jpeg')
            }
            
            # Send the POST request to the detections endpoint, including HEADERS
            response = requests.post(UPLOAD_URL, data=FORM_DATA, files=files, headers=HEADERS)
            
            print("\n--- Upload Response ---")
            print(f"Status Code: {response.status_code}")
            try:
                print("Response Body:")
                print(response.json())
            except requests.exceptions.JSONDecodeError:
                print("Response Body is not valid JSON. Raw text response:")
                print(response.text)
            print("-----------------------")

    finally:
        # Ensure the file handle is closed
        if files and 'file' in files and files['file'][1]:
            files['file'][1].close()