import requests
import json
from dataclasses import dataclass

# Configuration dictionaries with provider-specific parameters
MODEL_CONFIGS = {
    "openai": {
        "models": ["gpt-4o"],
        "params": {
            "temperature": 0.1,
            "maxTokens": 200
        }
    }
}

VOICE_CONFIGS = {
    "11labs": {
        "voices": [
            {"voiceId": "OYTbf65OHHFELVut7v2H", "model": "eleven_multilingual_v2"}
        ],
        "params": {
            "speed": 1.1,
            "stability": 0.6,
            "similarityBoost": 0.9,
            "useSpeakerBoost": True
        }
    }
}

TRANSCRIBER_CONFIGS = {
    "deepgram": {
        "models": ["nova-2"],
        "params": {
            "language": "pt-BR",
            "confidenceThreshold": 0.39
        }
    }
}

@dataclass
class AgentConfig:
    """Configuration for an agent with provider and model settings."""
    provider: str
    model: str
    voice_provider: str
    voice_config: dict
    transcriber_provider: str
    transcriber_model: str

class AgentAssistant:
    """Class to create and manage agent assistants with Vapi API."""
    VAPI_BASE_URL = "https://api.vapi.ai"
    API_TOKEN = "2dcbbb0a-e8ff-4257-94ab-36ab5ea93b95"
    HEADERS = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    def __init__(self, agent_config: AgentConfig, assistant_name: str):
        self.agent_config = agent_config
        self.assistant_name = assistant_name
        with open('agent_prompt_v2.txt', 'r', encoding='utf-8') as file:
            self.agent_system_prompt = file.read().strip()

    def _build_assistant_config(self) -> dict:
        """Build the assistant configuration dictionary with provider-specific parameters."""
        model_params = MODEL_CONFIGS[self.agent_config.provider]["params"]
        voice_params = VOICE_CONFIGS[self.agent_config.voice_provider]["params"]
        transcriber_params = TRANSCRIBER_CONFIGS[self.agent_config.transcriber_provider]["params"]

        return {
            "name": self.assistant_name,
            "model": {
                "provider": self.agent_config.provider,
                "model": self.agent_config.model,
                "messages": [{"role": "system", "content": self.agent_system_prompt}],
                **model_params
            },
            "voice": {
                "provider": self.agent_config.voice_provider,
                "voiceId": self.agent_config.voice_config["voiceId"],
                "model": self.agent_config.voice_config["model"],
                **voice_params
            },
            "transcriber": {
                "provider": self.agent_config.transcriber_provider,
                "model": self.agent_config.transcriber_model,
                **transcriber_params
            },
            "firstMessage": "Precisa do DAE?",
            "voicemailMessage": "Telefona-me de novo se for uma emergência!",
            "endCallFunctionEnabled": True,
            "endCallMessage": "Adeus.",
            "silenceTimeoutSeconds": 20,
            "serverMessages": ["conversation-update", "end-of-call-report", "hang"],
            "maxDurationSeconds": 145,
            "backgroundDenoisingEnabled": True,
            "backgroundSound": "off",
            "artifactPlan": {
                "recordingFormat": "mp3"
            },
            "analysisPlan": {
                "structuredDataPlan": {
                    "enabled": True,
                    "schema": {
                        "type": "object",
                        "required": [
                            "needs_dae",
                            "mobile_number",
                            "wants_rescuers",
                            "first_last_name",
                            "dispatch_message",
                            "emergency_location"
                        ],
                        "properties": {
                            "needs_dae": {
                                "description": "Whether the user confirmed they need the DAE (true for \"Sim\", false for \"Não\" or unclear). This is the first yes/no response in the transcript.",
                                "type": "boolean"
                            },
                            "mobile_number": {
                                "description": "The user's mobile phone number as stated in response to \"Diga o seu número de telemóvel.\" Extract as a string, including any prefixes or formatting provided.",
                                "type": "string"
                            },
                            "wants_rescuers": {
                                "description": "Whether the user wants rescuers called (true for \"Sim\", false for \"Não\" or unclear). This is the final yes/no response in the transcript.",
                                "type": "boolean"
                            },
                            "first_last_name": {
                                "description": "The user's full first and last name as stated in response to \"Diga o seu primeiro e último nome.\" Extract verbatim, no formatting changes.",
                                "type": "string"
                            },
                            "dispatch_message": {
                                "description": "The compiled text message for rescuers, only if wants_rescuers is true. Format exactly as: \"Está a ocorrer uma emergência junto ao {emergency_location}, onde está a ser usado um DAE, se se encontrar junto do local, por favor dê assistência. Ligue para {mobile_number}, para entrar em contacto com o utilizador do DAE.\" Use extracted values for placeholders. Set to null if wants_rescuers is false or data is incomplete.",
                                "type": "string"
                            },
                            "emergency_location": {
                                "description": "The emergency location with reference point as stated in response to \"Diga o local da emergência, com ponto de referência.\" Extract the full response verbatim.",
                                "type": "string"
                            }
                        }
                    },
                    "messages": [
                        {
                            "content": "You are extracting structured data from a short emergency call transcript for a DAE equipment lock access system. The conversation follows a strict flow: \n1. Ask if they need the DAE (\"Precisa do DAE?\") – expect \"Sim\" (yes) or \"Não\" (no).\n2. If yes, collect full name (\"Diga o seu primeiro e último nome.\").\n3. Collect mobile number (\"Diga o seu número de telemóvel.\").\n4. Collect emergency location with reference point (\"Diga o local da emergência, com ponto de referência.\").\n5. Ask if they want rescuers (\"Pretende que sejam chamados socorristas?\") – expect \"Sim\" (yes) or \"Não\" (no).\n\nExtract ONLY the data directly provided in the user's responses. Do not infer, add, or modify anything. If a field is unclear or missing, leave it as null. For yes/no fields, map responses like \"yes/sí/sim\" to true and \"no/não\" to false. Ignore any extraneous talk.\n\nIf wants_rescuers is true, compile the dispatch_message exactly as: \"Está a ocorrer uma emergência junto ao {emergency_location}, onde está a ser usado um DAE, se se encontrar junto do local, por favor dê assistência. Ligue para {mobile_number}, para entrar em contacto com o utilizador do DAE.\" Replace placeholders with extracted values. If wants_rescuers is false, set dispatch_message to null.\n\nOutput in strict JSON matching the schema, with no extra text.\n\nJson Schema:\n{{schema}}\n\nOnly respond with the JSON.",
                            "role": "system"
                        },
                        {
                            "content": "Here is the transcript:\n\n{{transcript}}\n\n. Here is the ended reason of the call:\n\n{{endedReason}}\n\n",
                            "role": "user"
                        }
                    ]
                }
            },
            "startSpeakingPlan": {
                "smartEndpointingPlan": {
                    "provider": "vapi"
                }
            }
        }

    def create(self) -> None:
        """Create the agent assistant."""
        assistant_config = self._build_assistant_config()
        try:
            response = requests.post(
                f"{self.VAPI_BASE_URL}/assistant",
                headers=self.HEADERS,
                data=json.dumps(assistant_config)
            )
            response.raise_for_status()
            assistant_data = response.json()
            vapi_assistant_id = assistant_data['id']
            print(f"Created assistant {self.assistant_name} with ID {vapi_assistant_id}")
        except requests.exceptions.RequestException as e:
            print(f"Error creating assistant {self.assistant_name}: {str(e)}")
            return

def main():
    """Create the specific DAE agent."""
    provider = "openai"
    model = MODEL_CONFIGS[provider]["models"][0]
    voice_provider = "11labs"
    voice_config = VOICE_CONFIGS[voice_provider]["voices"][0]
    transcriber_provider = "deepgram"
    transcriber_model = TRANSCRIBER_CONFIGS[transcriber_provider]["models"][0]

    agent_config = AgentConfig(
        provider=provider,
        model=model,
        voice_provider=voice_provider,
        voice_config=voice_config,
        transcriber_provider=transcriber_provider,
        transcriber_model=transcriber_model
    )
    assistant_name = "DAE Agent V1"
    AgentAssistant(agent_config, assistant_name).create()

if __name__ == "__main__":
    main()