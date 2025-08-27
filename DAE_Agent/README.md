# README for DAE Agent Project

## Project Overview
This project implements an AI-based emergency access system for DAE (Desfibrilhador Automático Externo) equipment locks using the VAPI API. The system consists of an AI agent that handles emergency calls to verify need, collect user information, and grant access while prioritizing speed in life-critical situations. To test and iterate, the project includes scripts for creating the agent, personas for simulation, and web-based call initiators. System prompts are stored separately for easy iteration.

The agent is designed to follow a structured conversation flow in Portuguese, with improvements across versions (e.g., intelligent parsing in newer prompts). Personas simulate users in emergency scenarios to stress-test the agent without real-world risks. The call scripts provide a simple web interface to initiate simulated calls and display results.

Key goals:
- Rapid DAE access with minimal user interaction.
- Testing different models and prompts to optimize latency, cost, and accuracy.
- Extensibility for more personas, agents, and features.

## File Descriptions

### Agent-Related Files
- **agent.py**: Python script to create the DAE AI agent using the VAPI API. It configures the model, voice, transcriber, and other settings. Loads the system prompt from an external file (e.g., agent_prompt_v1.txt) for easy updates. Run this to deploy or update the agent.

- **agent_prompt_v0.txt**: The initial version of the system prompt for the DAE agent. Defines basic conversation flow, personality, and handling without advanced features like dynamic skipping or health professional detection.

- **agent_prompt_v1.txt**: The current and improved version of the system prompt for the DAE agent. Includes enhancements such as intelligent response parsing to skip questions, health professional detection for immediate access, phone number validation, and dynamic acknowledgments for missing info. Use this for the latest agent behavior.

- **agent_v1.py**: Python script to create the DAE AI agent but for the task of Minimum Value Model (MVM), where this agent will be tested by using different models.

### Persona-Related Files
- **persona_v0.py**: Python script to create the first persona (a simulated emergency user) using the VAPI API. Configures a basic user simulation for testing the agent. Loads the system prompt from persona_prompt_v0.txt.

- **persona_prompt_v0.txt**: System prompt for the first persona version. Simulates João Silva in an emergency at Praia de São Jacinto, with predefined responses emphasizing urgency and brevity.

- **persona_v1.py**: Python script to create the second persona using the VAPI API. Similar to persona_v0.py but for an updated simulation scenario. Loads the system prompt from persona_v1_prompt_v0.txt.

- **persona_v1_prompt_v0.txt**: System prompt for the second persona version. An iteration on the first, with refined urgency cues and context for testing agent responses in the same emergency scenario.

- **persona_v2.py**: Python script to create a persona with an increased temperature (t=0.4)

- **persona_v3.py**: Python script to create a persona with an increased temperature (t=0.8)

### Call Initiation Files
- **call.py**: Basic web application (using FastAPI) to simulate pushing the emergency button. Provides a simple HTML interface to input a phone number and initiate a call to the DAE agent. Does not poll for call results or display analysis tables—use for quick tests.

- **call_v1.py**: Improved version of the call initiation web app. Includes polling to wait for call completion and displays structured data results (e.g., needs_dae, mobile_number) in an attractive HTML table after the call ends. Recommended for full testing with result visualization.

## Usage Instructions
1. **Prerequisites**:
   - Python 3.8+ installed.
   - Install dependencies: `pip install requests fastapi uvicorn` (for call scripts).
   - Ensure VAPI API token and IDs are updated in scripts (e.g., ASSISTANT_ID, PHONE_NUMBER_ID).
   - Place system prompt files (e.g., agent_prompt_v1.txt) in the same directory as the scripts.

2. **Creating Agents/Personas**:
   - Run `python agent.py` to create/update the DAE agent (uses agent_prompt_v1.txt by default; edit `__init__` to switch prompts).
   - Run `python persona_v0.py` or `python persona_v1.py` to create personas for testing.

3. **Initiating Calls**:
   - Run `uvicorn call.py:app --reload` (or call_v1.py for results table).
   - Open http://127.0.0.1:8000 in a browser.
   - Enter a phone number and submit to start a simulated call.

4. **Testing and Iteration**:
   - Update prompts in .txt files and re-run creation scripts.
   - Use personas to simulate calls and evaluate agent responses via VAPI dashboard or call logs.
   - Compare versions: v0 prompts are basic; v1 are optimized.

5. **Twillio Phone Numbers Credentials**:
   To go over the vapi phone number daily limits, we needed to go and buy twillio phone numbers, so here is the credentials:
   - Go to https://console.twilio.com/us1/develop/onboarding-v2/athena?flow=sms-dev-us
   - Account SID: <TWILIO_ACCOUNT_SID>
   - Auth Token: <TWILIO_AUTH_TOKEN>
   - Phone number: <TWILIO_PHONE_NUMBER>

## Future Improvements
This project is designed for extensibility:
- **Additional Personas**: Add new scripts like persona_v2.py with corresponding prompts (e.g., persona_v2_prompt_v0.txt) for diverse scenarios (e.g., different emergencies, user behaviors).
- **Multiple Agents**: Create variants like agent_v2.py to test lower-cost models (e.g., GPT-3.5 or smaller) by updating MODEL_CONFIGS. Evaluate latency/cost via VAPI metrics.
- **Enhanced Call System**: Extend call_v1.py with features like real-time monitoring, exportable logs, or integration with external services for dispatch messages.
- **Prompt Iterations**: Add more prompt files (e.g., agent_prompt_v2.txt) for A/B testing improvements like better error handling or multilingual support.
- **Evaluation Framework**: Implement automated testing to compare agent versions/personas on metrics like response time, accuracy, and cost.
- **Deployment**: Containerize with Docker for cloud hosting; integrate with hardware for real DAE locks.

For questions or contributions, contact blsmakeit@gmail.com. Last updated: August 26, 2025.