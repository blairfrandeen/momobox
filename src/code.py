"""
Mockup for onboard logic for Momobox
"""
import time

import audiomp3
import audiopwmio
import board
import digitalio


class Song:
    """Mockup for MP3 files that can be played"""

    def __init__(self, filename, length):
        self.filename = filename
        self.length = length


# Mockup for database: keys in this dictionary mock the
# RFID codes on individual momies. Songs mock pointers to
# MP3 files on the SD card
library = {
    1: Song("wappin.mp3", 50),
    2: Song("shavingcream_32_mono.mp3", 70),
}

RESET_CLOCK_S = 5


class AudioPlayer:
    def __init__(self, hall_sensor):
        self.audio = audiopwmio.PWMAudioOut(board.GP16)
        self.song = None
        self.decoder = None
        self.hall_sensor = hall_sensor  # GPIO Pin 18
        self.reset_clock = 0

        self.listen()

    def play(self, filename):
        self.song = filename
        self.decoder = audiomp3.MP3Decoder(open(self.song, "rb"))
        self.audio.play(self.decoder)

    def pause(self):
        self.audio.pause()
        self.reset_clock = time.time()

    def resume(self):
        time_paused = time.time() - self.reset_clock
        if time_paused < RESET_CLOCK_S:
            self.audio.resume()
        else:
            self.audio.stop()

    def unload(self):
        self.audio.stop()

    @property
    def is_playing(self):
        return self.audio.playing

    @property
    def is_paused(self):
        return self.audio.paused

    def listen(self):
        while True:
            if (
                self.hall_sensor.value is True
                and not self.is_playing
                and not self.is_paused
            ):
                self.get_input()
            if self.hall_sensor.value is False:
                print("Hall sensor disconnected.")
                if not self.is_paused:
                    self.pause()
                time.sleep(1)
            if self.hall_sensor.value is True and self.is_paused:
                self.resume()

    def get_input(self):
        selection = int(input("Select Song ID: "))
        self.play(library[selection].filename)


def main():
    stop_time: int = 0  # state variable, when was most recent song stopped
    most_recent: int = None  # most recent song id
    pause_ts: float = 0.0  # last pause

    p18 = digitalio.DigitalInOut(board.GP18)
    player = AudioPlayer(p18)


if __name__ == "__main__":
    main()
