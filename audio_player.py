from typing import Optional

import os
import time
import pyaudio
import librosa
import numpy as np

from pyaudio import PyAudio, Stream


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AudioPlayer(metaclass=Singleton):
    def __init__(self):
        self._idx = 0
        self._sr = 0
        self._pa: PyAudio = PyAudio()
        self._stream: Optional[Stream] = None
        self.reset()

    def __del__(self):
        self._pa.terminate()

    def reset(self):
        # reset stream
        if self._stream is not None:
            if not self._stream.is_stopped():
                self._stream.stop_stream()
            self._stream.close()
        self._stream = None
        # reset idx
        self._idx = 0
        self._sr = 0
    
    @property
    def curr_msec(self):
        if self._stream is not None:
            return self._idx * 1000.0 / self._sr
        else:
            return 0.0
    
    def seek(self, msec):
        if self._stream is not None:
            self._idx = int(np.round(self._sr * msec / 1000.0))

    def open(self, audio_filepath):
        self.reset()
        # TODO: audio reader (using ffmpeg)
        # set the data
        signal, sr = librosa.load(audio_filepath, sr=48000, mono=False)
        signal = signal.transpose(1, 0)
        assert signal.dtype == np.float32
        self._signal = signal
        self._sr = sr
        # open a new stream
        fmt = self._pa.get_format_from_width(4)
        chs = 1 if signal.ndim == 1 else signal.shape[1]
        self._stream = self._pa.open(
            format=fmt,
            channels=chs,
            rate=sr,
            frames_per_buffer=1024,
            output=True,
            stream_callback=AudioPlayer.stream_callback
        )
        self._stream.stop_stream()
        self._idx = 0
    
    def toggle(self, playing):
        if playing:
            self.play()
        else:
            self.pause()

    def play(self):
        if self._stream is not None:
            if self._stream.is_stopped():
                self._stream.start_stream()

    def pause(self):
        if self._stream is not None:
            if not self._stream.is_stopped():
                self._stream.stop_stream()
    
    def close(self):
        self.reset()

    def is_active(self):
        return self._stream is not None and self._stream.is_active()

    @staticmethod
    def stream_callback(in_data, frame_count, time_info, status):
        ap = AudioPlayer()
        data = ap._signal[ap._idx: ap._idx + frame_count]
        ap._idx = ap._idx + frame_count
        return (data.tobytes(), pyaudio.paContinue)


if __name__ == "__main__":

    def play_audio_file(fname):
        ap = AudioPlayer()
        ap.open(fname)

        ap.play()
        while ap.is_active():
            time.sleep(0.1)
        ap.close()

    play_audio_file(os.path.expanduser("~/Videos/love_poem.webm"))
