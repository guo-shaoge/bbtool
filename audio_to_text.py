import sys
from faster_whisper import WhisperModel

if len(sys.argv) < 2:
    print("Usage: python transcribe.py audio.m4a")
    sys.exit(1)

audio_file = sys.argv[1]

# 英文专用模型
model = WhisperModel(
    "medium.en",
    compute_type="int8"
)

segments, info = model.transcribe(
    audio_file,
    beam_size=5,
    language="en"
)

print(f"Detected language: {info.language}")
print("-" * 40)

for segment in segments:
    print(segment.text)
