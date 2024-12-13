import cv2
import threading
import time
from enum import Enum
from typing import Optional, Tuple
import os


class PlayerState(Enum):
    """Enumeration to represent the player's state."""
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2


class VideoPlayer:
    """A video player class with controls for play, pause, stop, and resume."""

    def __init__(self, video_path: str) -> None:
        """
        Initializes the VideoPlayer with the video path and sets initial state.

        Args:
            video_path: Path to the video file.
        """
        if not isinstance(video_path, str):
           raise TypeError("video_path must be a string.")

        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")
        
        self.video_path = video_path
        self.cap: Optional[cv2.VideoCapture] = None
        self.current_frame: Optional[cv2.Mat] = None  # Store the current frame
        self._state = PlayerState.STOPPED
        self.frame_delay = 0.03  #  delay for displaying frames
        self._frame_thread: Optional[threading.Thread] = None # Thread to handle frames reading
        self._stop_event: Optional[threading.Event] = None #  stop signal for the thread
        self.is_looping: bool = False

    
    def is_video_open(self) -> bool:
         """Check if a video is currently open."""
         return self.cap is not None and self.cap.isOpened()
    

    @property
    def state(self) -> PlayerState:
        """Returns the current state of the video player."""
        return self._state

    def _read_frames(self) -> None:
        """Reads frames from the video and displays them (thread function)."""
        if not self.cap:
            print("error: Video capture is not initialized")
            return
       
        while not self._stop_event.is_set():
            if self._state == PlayerState.PLAYING :
                ret, frame = self.cap.read()
                if not ret :
                   if not self.is_looping:
                        self.stop()
                        break
                   else:
                       self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # restart from the beginning of the video 
                       continue
                self.current_frame = frame
                cv2.imshow('Video Player', frame)
                cv2.waitKey(int(self.frame_delay * 1000))  # Delay before the next frame
            elif self._state == PlayerState.PAUSED and self.current_frame is not None:
               cv2.imshow('Video Player', self.current_frame)
               cv2.waitKey(int(self.frame_delay*1000))
            
                
                

    def play(self, loop:bool=False) -> None:
        """Starts playing the video.

        Args:
             loop: if true, video should loop
        """

        if self._state == PlayerState.PLAYING:
            print("info: Video is already playing.")
            return
        
        self.is_looping = loop

        if self._state == PlayerState.STOPPED or not self.is_video_open():
             self._open_video()


        self._state = PlayerState.PLAYING
        
        if self._frame_thread is None or not self._frame_thread.is_alive():
             self._stop_event = threading.Event()
             self._frame_thread = threading.Thread(target=self._read_frames, daemon=True)
             self._frame_thread.start()
       
       

    def pause(self) -> None:
        """Pauses the video playback."""

        if self._state == PlayerState.PAUSED :
            print("info: Video is already paused.")
            return
        
        if self._state == PlayerState.STOPPED :
             print("warning: Cannot pause the video because it is stopped")
             return
        
        self._state = PlayerState.PAUSED
        


    def stop(self) -> None:
        """Stops the video playback."""
        if self._state == PlayerState.STOPPED :
            print("info: Video is already stopped")
            return
        

        self._state = PlayerState.STOPPED
        if self._stop_event is not None:
            self._stop_event.set()
        if self._frame_thread is not None:
            self._frame_thread.join()
            self._frame_thread = None
            self._stop_event = None
            

        self._release_resources()
        cv2.destroyAllWindows()
        

    def resume(self) -> None:
        """Resumes the video playback."""

        if self._state == PlayerState.PLAYING:
            print("info: Video is already playing")
            return
        
        if self._state == PlayerState.STOPPED :
            print("warning: Cannot resume the video because it is stopped")
            return

        self._state = PlayerState.PLAYING
        if self._frame_thread is None or not self._frame_thread.is_alive():
             self._stop_event = threading.Event()
             self._frame_thread = threading.Thread(target=self._read_frames, daemon=True)
             self._frame_thread.start()


    def get_frame_rate(self) -> float:
        """Get the frame rate of the video."""
        if self.cap is None or not self.cap.isOpened():
             raise Exception("Video is not opened yet")
        return self.cap.get(cv2.CAP_PROP_FPS)

    def _open_video(self) -> None:
          """Initializes the video capture object."""
          try:
                self.cap = cv2.VideoCapture(self.video_path)
                if not self.cap.isOpened():
                    raise IOError(f"Error: Could not open the video file {self.video_path}")
          except Exception as e:
             raise  IOError(f"An unexpected error occurred: {e}")
    

    def _release_resources(self) -> None:
        """Releases all resources, including the video capture."""

        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            self.cap = None
        self.current_frame = None

    def set_frame_delay(self, delay:float) -> None:
        """Set the frame display delay.

        Args:
            delay (float) : display delay
        """

        if not isinstance(delay, float):
            raise TypeError("Delay must be a float")
        
        if delay <= 0 :
            raise ValueError("Delay must be a positive number")
        
        self.frame_delay = delay




if __name__ == '__main__':
    try:
         # Replace with your video file path
        video_file = "E:/LLMS/Fine-tuning/output.mp4"  

        # Check if the sample video file exists in the directory
        if not os.path.exists(video_file):
            print(f"Error: Video file {video_file} not found. Please make sure you have a sample video file in the same directory.")
        else:
            player = VideoPlayer(video_file)
            
            player.play()
            time.sleep(30) # Keep playing for 5 seconds
            player.pause()
            time.sleep(2)
            player.resume()
            time.sleep(3)
            player.set_frame_delay(0.05)
            time.sleep(3)
            player.stop()
            
            player.play(loop=True)
            time.sleep(5)
            player.stop()
           
    except FileNotFoundError as e:
        print(f"File error: {e}")
    except Exception as e:
      print(f"An unexpected error occurred: {e}")