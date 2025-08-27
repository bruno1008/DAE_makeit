#!/usr/bin/env python3
"""
start_on_button_polling.py — polling loop detects button press, starts call, LED on during call
"""

import os, queue, signal, numpy as np, threading, time
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import (
    Conversation, ConversationInitiationData, ClientTools
)
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
import lgpio

GAIN = 2.5

class DuplexAudio(DefaultAudioInterface):
    INPUT_FRAMES_PER_BUFFER = 320
    OUTPUT_FRAMES_PER_BUFFER = 640
    _gate = False

    def _output_thread(self):
        while not self.should_stop.is_set():
            try:
                pcm = self.output_queue.get(timeout=0.25)
                self._gate = True
                self.out_stream.write(pcm)
                self._gate = False
            except queue.Empty:
                pass

    def in_callback(self, in_data, *_):
        if not self._gate and self.input_callback:
            if GAIN != 1.0:
                arr = (np.frombuffer(in_data, np.int16).astype(np.float32)*GAIN).clip(-32768,32767)
                in_data = arr.astype(np.int16).tobytes()
            self.input_callback(in_data)
        return (None, self.pyaudio.paContinue)

def open_door(params: dict):
    print("🔓 open_door() called")
    chip = lgpio.gpiochip_open(0)
    pin = 5
    lgpio.gpio_claim_output(chip, pin)
    lgpio.gpio_write(chip, pin, 1)
    time.sleep(0.1)
    lgpio.gpio_write(chip, pin, 0)

tools = ClientTools()
tools.register("openAEDDoor", open_door)

convo = None
led_chip = lgpio.gpiochip_open(0)
led_pin = 6
lgpio.gpio_claim_output(led_chip, led_pin)

def start_conversation():
    global convo
    # turn LED on
    lgpio.gpio_write(led_chip, led_pin, 1)

    load_dotenv()
    AGENT = os.getenv("AGENT_ID") or exit("Set AGENT_ID")
    KEY = os.getenv("XI_API_KEY")

    client = ElevenLabs(api_key=KEY or None)
    audio = DuplexAudio()
    convo = Conversation(
        client=client,
        agent_id=AGENT,
        requires_auth=bool(KEY),
        audio_interface=audio,
        client_tools=tools,
        config=ConversationInitiationData(
            conversation_config_override={"tts": {"audio_format": "pcm_16000"}}
        ),
        callback_agent_response=lambda t: print(f"\n\033[94mAgent>\033[0m {t}"),
        callback_user_transcript=lambda t: print(f"\033[92mYou >\033[0m {t}", end="\r"),
    )

    threading.Thread(target=run_and_cleanup, args=(convo,), daemon=True).start()

def run_and_cleanup(convo):
    convo.start_session()
    convo.wait_for_session_end()
    # turn LED off when done
    lgpio.gpio_write(led_chip, led_pin, 0)

def main():
    chip = lgpio.gpiochip_open(0)
    button_pin = 16
    lgpio.gpio_claim_input(chip, button_pin)

    print("Polling button… press button to start (CTRL+C to exit)")
    signal.signal(signal.SIGINT, lambda *_: os._exit(0))
    prev = 0
    while True:
        level = lgpio.gpio_read(chip, button_pin)
        if level == 0 and prev == 1:
            print("🔘 Button pressed — starting call")
            start_conversation()
        prev = level
        time.sleep(0.05)  # poll every 50 ms

if __name__ == "__main__":
    main()