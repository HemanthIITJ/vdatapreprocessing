from functools import cache
from re import A
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from typing import List, Union, Generator, Tuple
import librosa
import numpy as np
import logging
from tqdm import tqdm

# Configure logging for better error tracking and information
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants for audio processing and batching
DEFAULT_CHUNK_LENGTH_SECONDS = 30  # seconds
DEFAULT_OVERLAP_SECONDS = 2  # seconds
DEFAULT_BATCH_SIZE = 8  # Adjust based on your GPU memory
SAMPLE_RATE = 16000  # Standard sample rate for Whisper

# Device and data type setup
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Model ID
model_id = "openai/whisper-large-v3-turbo"


class AudioTranscriber:
    """
    A class to handle the transcription of long audio files using the Whisper model.
    It chunks the audio, processes it in batches, and handles errors gracefully.
    """

    def __init__(
            self,
            model_id: str,
            device: str,
            torch_dtype: torch.dtype,
            chunk_length_seconds: int = DEFAULT_CHUNK_LENGTH_SECONDS,
            overlap_seconds: int = DEFAULT_OVERLAP_SECONDS,
            batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        """
        Initializes the AudioTranscriber with the model, processor, and pipeline.

        Args:
            model_id (str): The ID of the Whisper model to use.
            device (str): The device to run the model on ('cuda:0' or 'cpu').
            torch_dtype (torch.dtype): The data type to use for the model (torch.float16 or torch.float32).
            chunk_length_seconds (int): The length of each audio chunk in seconds.
            overlap_seconds (int): The overlap between consecutive chunks in seconds.
            batch_size (int): The batch size for processing chunks.
        """
        self.model_id = model_id
        self.device = device
        self.torch_dtype = torch_dtype
        self.chunk_length_seconds = chunk_length_seconds
        self.overlap_seconds = overlap_seconds
        self.batch_size = batch_size
        self.sample_rate = SAMPLE_RATE

        self.model, self.processor, self.pipe = self._load_model_and_pipeline()

    def _load_model_and_pipeline(
            self
    ) -> Tuple[AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline]:
        """
        Loads the Whisper model, processor, and initializes the pipeline.

        Returns:
            Tuple[AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline]: The model, processor, and pipeline.
        """
        try:
            logging.info(f"Loading model: {self.model_id}")
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
                cache_dir="./cache",
            )
            model.to(self.device)
            logging.info(f"Model loaded to device: {self.device}")

            processor = AutoProcessor.from_pretrained(self.model_id,cache_dir="./cache")
            logging.info("Processor loaded")

            pipe = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                torch_dtype=self.torch_dtype,
                device=self.device,
            )
            logging.info("Pipeline created")

            return model, processor, pipe
        except Exception as e:
            logging.error(f"Error loading model and pipeline: {e}")
            raise

    def load_audio(self, audio_file: str) -> np.ndarray:
        """
        Loads an audio file and resamples it to the required sample rate.

        Args:
            audio_file (str): Path to the audio file.

        Returns:
            np.ndarray: The audio data as a numpy array.
        """
        try:
            logging.info(f"Loading audio file: {audio_file}")
            audio_data, sr = librosa.load(
                audio_file, sr=self.sample_rate, mono=True
            )
            logging.info(f"Audio loaded with sample rate: {sr}")
            return audio_data

        except Exception as e:
            logging.error(f"Error loading audio file {audio_file}: {e}")
            raise

    def chunk_audio(
            self, audio_data: np.ndarray
    ) -> Generator[np.ndarray, None, None]:
        """
        Splits the audio data into chunks with specified length and overlap.

        Args:
            audio_data (np.ndarray): The audio data as a numpy array.

        Yields:
            np.ndarray: An audio chunk.
        """
        try:
            chunk_length_samples = int(self.chunk_length_seconds * self.sample_rate)
            overlap_samples = int(self.overlap_seconds * self.sample_rate)
            start = 0
            while start < len(audio_data):
                end = min(start + chunk_length_samples, len(audio_data))
                chunk = audio_data[start:end]
                yield chunk
                if end == len(audio_data):
                    break
                start += chunk_length_samples - overlap_samples
        except Exception as e:
            logging.error(f"Error chunking audio data: {e}")
            raise

    def transcribe_batch(self, audio_chunks: List[np.ndarray]) -> List[str]:
        """
         Transcribes a batch of audio chunks using the Whisper pipeline.

         Args:
              audio_chunks (List[np.ndarray]): A list of audio chunks.

         Returns:
              List[str]: A list of transcriptions corresponding to the audio chunks.
         """
        try:
            logging.info("Transcribing batch of audio chunks")
            transcriptions = self.pipe(
                audio_chunks, generate_kwargs={"language": "en"}, batch_size=self.batch_size
            )
            return [chunk["text"] for chunk in transcriptions]
        except Exception as e:
            logging.error(f"Error transcribing batch of audio chunks: {e}")
            raise

    def transcribe_audio(self, audio_file: str) -> str:
        """
        Transcribes a long audio file by chunking, batching, and processing.

        Args:
            audio_file (str): Path to the audio file.

        Returns:
            str: The full transcription of the audio file.
        """
        try:
            audio_data = self.load_audio(audio_file)
            audio_chunks_generator = self.chunk_audio(audio_data)

            all_transcriptions = []
            batch_chunks = []

            logging.info("Starting transcription process")
            for chunk in tqdm(
                    audio_chunks_generator, desc="Processing", unit="chunks"
            ):
                batch_chunks.append(chunk.copy())  # Ensure each chunk is a new copy

                if len(batch_chunks) == self.batch_size:
                    transcriptions = self.transcribe_batch(batch_chunks)
                    all_transcriptions.extend(transcriptions)
                    batch_chunks = []
                    torch.cuda.empty_cache()  # Clear GPU cache after processing each batch

            if batch_chunks:  # Process any remaining chunks
                transcriptions = self.transcribe_batch(batch_chunks)
                all_transcriptions.extend(transcriptions)

            full_transcription = " ".join(all_transcriptions)
            logging.info("Transcription complete")
            return full_transcription

        except Exception as e:
            logging.error()

