import os

# Construct the absolute path to the audio file
base_dir = os.path.dirname(os.path.abspath(__file__))
audio_path = os.path.join(base_dir, "vote_to_mute.mp3")

print(audio_path)  # Debug: Check the path being constructed


# Check if the file exists
if os.path.exists(audio_path):
    print("Audio file found.")
else:
    print("Audio file not found.")
