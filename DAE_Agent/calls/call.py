import requests
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount static directory if you have CSS/JS, but for simplicity, we'll inline styles
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Vapi API configuration
VAPI_BASE_URL = "https://api.vapi.ai"
API_TOKEN = "2dcbbb0a-e8ff-4257-94ab-36ab5ea93b95"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Hardcoded Assistant ID from your provided agent config
ASSISTANT_ID = "e42aa5e1-4a33-4ed6-a3b4-58176a919f7f"

# For simplicity, assume you have a pre-created phoneNumberId for outbound calls.
# If not, you can create one via VAPI API (POST /phone-number) and hardcode it here.
# Example: PHONE_NUMBER_ID = "your-phone-number-id"
PHONE_NUMBER_ID = "bf2a06fb-9f9c-4440-89f0-b1e43e6876bd"  # Replace with your actual phoneNumberId if required; it's optional for some setups but recommended for outbound.

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Simple, cozy, beautiful HTML with a button and input for phone number
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DAE Emergency Access</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(to bottom right, #f0f8ff, #e6e6fa);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                color: #333;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                text-align: center;
                max-width: 400px;
            }
            h1 {
                color: #4a90e2;
                margin-bottom: 20px;
            }
            input[type="text"] {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
            }
            button {
                background: #4a90e2;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 18px;
                cursor: pointer;
                transition: background 0.3s;
            }
            button:hover {
                background: #357abd;
            }
            #response {
                margin-top: 20px;
                font-size: 14px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>DAE Emergency Button</h1>
            <p>Enter your phone number to simulate pushing the button and starting the call.</p>
            <form id="callForm">
                <input type="text" id="phoneNumber" name="phoneNumber" placeholder="+351XXXXXXXXX" required>
                <button type="submit">Push to Access DAE</button>
            </form>
            <div id="response"></div>
        </div>
        <script>
            document.getElementById('callForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const phoneNumber = document.getElementById('phoneNumber').value;
                const responseDiv = document.getElementById('response');
                responseDiv.textContent = 'Initiating call...';
                
                try {
                    const res = await fetch('/start_call', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: `phoneNumber=${encodeURIComponent(phoneNumber)}`
                    });
                    const data = await res.json();
                    if (res.ok) {
                        responseDiv.textContent = `Call initiated! ID: ${data.id}`;
                    } else {
                        responseDiv.textContent = `Error: ${data.detail}`;
                    }
                } catch (err) {
                    responseDiv.textContent = `Error: ${err.message}`;
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/start_call")
async def start_call(phoneNumber: str = Form(...)):
    # Initiate the call using VAPI API
    payload = {
        "assistantId": ASSISTANT_ID,
        "customer": {
            "number": phoneNumber
        }
    }
    if PHONE_NUMBER_ID:
        payload["phoneNumberId"] = PHONE_NUMBER_ID

    try:
        response = requests.post(
            f"{VAPI_BASE_URL}/call",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        call_data = response.json()
        return call_data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))