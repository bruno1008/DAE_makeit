import requests
import time
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI()

# Vapi API configuration
VAPI_BASE_URL = "https://api.vapi.ai"
API_TOKEN = "7d550746-272a-4f20-9918-908c562aa4a3"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Hardcoded Assistant ID from your provided agent config
ASSISTANT_ID = "4532d78f-4ffc-4b69-a4cb-692d95ed7013"

# For simplicity, assume you have a pre-created phoneNumberId for outbound calls.
# If not, you can create one via VAPI API (POST /phone-number) and hardcode it here.
# Example: PHONE_NUMBER_ID = "your-phone-number-id"
PHONE_NUMBER_ID = "d178c35d-0f64-40d3-86dd-1a8aca8cad97"  # Replace with your actual phoneNumberId if required; it's optional for some setups but recommended for outbound.

# Polling settings
POLL_INTERVAL = 10  # seconds between checks
MAX_POLL_TIME = 145  # max wait time in seconds (5 minutes)

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
                max-width: 600px;  /* Increased width for table */
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
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #4a90e2;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f1f1f1;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>DAE Emergency Button</h1>
            <p>Enter your phone number to simulate pushing the button and starting the call.</p>
            <form id="callForm">
                <input type="text" id="phoneNumber" name="phoneNumber" placeholder="+1351XXXXXXXXX" required>
                <button type="submit">Push to Access DAE</button>
            </form>
            <div id="response"></div>
        </div>
        <script>
            document.getElementById('callForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const phoneNumber = document.getElementById('phoneNumber').value;
                const responseDiv = document.getElementById('response');
                responseDiv.innerHTML = 'Initiating call...';
                
                try {
                    const res = await fetch('/start_call', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: `phoneNumber=${encodeURIComponent(phoneNumber)}`
                    });
                    const data = await res.json();
                    if (res.ok) {
                        let html = `<p>Call initiated! ID: ${data.call_id}</p>`;
                        if (data.structured_data) {
                            html += '<table><tr><th>Field</th><th>Value</th></tr>';
                            for (const [key, value] of Object.entries(data.structured_data)) {
                                html += `<tr><td>${key}</td><td>${value}</td></tr>`;
                            }
                            html += '</table>';
                        } else {
                            html += '<p>No structured data available (call may not have ended yet).</p>';
                        }
                        responseDiv.innerHTML = html;
                    } else {
                        responseDiv.innerHTML = `Error: ${data.detail}`;
                    }
                } catch (err) {
                    responseDiv.innerHTML = `Error: ${err.message}`;
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/start_call")
async def start_call(phoneNumber: str = Form(...)):
    # Step 1: Initiate the call using VAPI API
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
        call_id = call_data.get("id")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

    # Step 2: Poll until the call ends
    start_time = time.time()
    while time.time() - start_time < MAX_POLL_TIME:
        try:
            poll_response = requests.get(
                f"{VAPI_BASE_URL}/call/{call_id}",
                headers=HEADERS
            )
            poll_response.raise_for_status()
            poll_data = poll_response.json()
            if poll_data.get("status") == "ended":
                # Extract structuredData from analysis
                analysis = poll_data.get("analysis", {})
                structured_data = analysis.get("structuredData", None)
                return {
                    "call_id": call_id,
                    "structured_data": structured_data
                }
        except requests.exceptions.RequestException as e:
            # Log error but continue polling
            print(f"Polling error: {str(e)}")
        time.sleep(POLL_INTERVAL)

    raise HTTPException(status_code=504, detail="Call did not end within the timeout period.")