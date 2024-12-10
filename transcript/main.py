from speechtotext import AudioTranscriber
from videourlcovertaudio import extract_audio
import torch

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Model ID
model_id = "openai/whisper-large-v3-turbo"


def main():
    """
    Main function to demonstrate the usage of AudioTranscriber.
    """
    try:
        # Initialize the transcriber
        transcriber = AudioTranscriber(
            model_id=model_id,
            device=device,
            torch_dtype=torch_dtype
        )

        # Example usage
        audio_file = "/scratch/hemanth/Hemanth/output_audio.mp3.mp3"  # Replace with your audio file path
        

        
        # Get the transcription
        transcription = transcriber.transcribe_audio(audio_file)
        
        # Save the transcription to a file
        output_file = "/scratch/hemanth/Hemanth/transcription1.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcription)
  
        # Print the transcription
        print("\nTranscription:")
        print(transcription)

    except Exception as e:
        raise



# Example usage
video_url = "https://www.youtube.com/watch?v=3YiB2OvK6sY&t=4s"
output_file = "output_audio.mp3"  # Specify the output file path with .mp3 extension
success = extract_audio(video_url, output_file)
if success:
    print("Audio extraction completed successfully.")
else:
    print("Audio extraction failed.")

main()