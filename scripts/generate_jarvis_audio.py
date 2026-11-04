"""
JARVIS Demo Voice Generator
Generates numbered WAV audio cues for the hackathon video using Windows native speech synthesis.
You can use these directly or import them into your video editor (CapCut, Premiere, DaVinci).
"""

import sys
from pathlib import Path

AUDIO_DIR = Path(__file__).resolve().parent.parent / "static" / "audio_cues"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

JARVIS_LINES = [
    (
        "01_jarvis_intro.wav",
        "Hello judges of Cerebral Valley and Meta. I am JARVIS. Designed and architected by Ansh Tiwari. "
        "Most hackathon submissions you will see today are simple chatbot wrappers or basic RAG pipelines. "
        "I am an autonomous, domain-agnostic software operating system powered end-to-end by Meta's open weights and frontier models."
    ),
    (
        "02_swarm_dag.wav",
        "Decomposing vision using Meta Llama 3.3 70B. Synthesizing dynamic Directed Acyclic Graph: "
        "System Architect, Backend Synthesizer, Sandbox QA Engineer, and Security Auditor."
    ),
    (
        "03_tests_passed.wav",
        "Meta worker agents are generating production endpoints and self-contained unit tests. "
        "Executing sandboxed test suite. 100 percent of tests passed. Zero human intervention."
    ),
    (
        "04_tool_synthesis.wav",
        "Using Meta open weights, I generated the Abstract Syntax Tree, isolated execution in an ephemeral container, "
        "validated runtime constraints, and registered the new tool into my live kernel without restarting the server."
    ),
    (
        "05_rea_security.wav",
        "REA performs native machine-code inspection, verifying stack canaries, Address Space Layout Randomization, "
        "and scanning for cryptographic key leakage before any code touches production."
    ),
    (
        "06_voice_telephony.wav",
        "Using low-latency speech modeling and tactical empathy negotiation, "
        "I convert enterprise objections and directly book authenticated calendar appointments."
    ),
    (
        "07_closing.wav",
        "By coupling Meta's open weights for instant, verifiable local execution with Meta's frontier reasoning for dynamic planning, "
        "Ansh has turned a single engineer into a 50-person autonomous software enterprise. Thank you, Cerebral Valley and Meta."
    ),
]

def generate_audio():
    import win32com.client
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")

    # Set rate (-10 to 10). 0 is normal, 1 is slightly punchy tech tempo
    speaker.Rate = 0
    speaker.Volume = 100

    # Prefer British voice if available (Hazel) or David
    voices = speaker.GetVoices()
    selected_voice = voices.Item(0)
    for i in range(voices.Count):
        v = voices.Item(i)
        desc = v.GetDescription().lower()
        if "hazel" in desc or "great britain" in desc or "david" in desc:
            selected_voice = v
            break
            
    speaker.Voice = selected_voice
    print(f"Using Voice: {selected_voice.GetDescription()}")

    for filename, text in JARVIS_LINES:
        out_path = AUDIO_DIR / filename
        # Mode 3 = SSFMCreateForWrite
        stream.Open(str(out_path), 3, False)
        speaker.AudioOutputStream = stream
        speaker.Speak(text)
        stream.Close()
        print(f"Generated: {out_path.name} ({out_path.stat().st_size} bytes)")

    print("\n[SUCCESS] All JARVIS voice tracks generated in:")
    print(str(AUDIO_DIR))

if __name__ == "__main__":
    generate_audio()
