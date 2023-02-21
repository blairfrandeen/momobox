"""
Mockup for onboard logic for Momobox
"""
import time

import audiomp3
import audiopwmio
import board
import busio
import digitalio

import mfrc522


class Song:
    """Mockup for MP3 files that can be played"""

    def __init__(self, filename, length):
        self.filename = filename
        self.length = length


# Mockup for database: keys in this dictionary mock the
# RFID codes on individual momies. Songs mock pointers to
# MP3 files on the SD card
library = {
    "23d95433": Song("wappin.mp3", 50),
    "b8003433": Song("shavingcream.mp3", 70),
}

RESET_CLOCK_S = 5


class AudioPlayer:
    def __init__(self, hall_sensor):
        self.audio = audiopwmio.PWMAudioOut(board.GP16)
        self.song = None
        self.decoder = None
        self.hall_sensor = hall_sensor  # GPIO Pin 18
        self.reset_clock = 0
        self.rfid_reader = rfid_reader_init()

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
        print("Place RFID card on sensor to select song")
        song = read_rfid(self.rfid_reader)
        self.play(library[song].filename)


def rfid_reader_init():
    sck = board.GP2
    mosi = board.GP3
    miso = board.GP4
    spi = busio.SPI(sck, MOSI=mosi, MISO=miso)

    cs = digitalio.DigitalInOut(board.GP1)
    rst = digitalio.DigitalInOut(board.GP0)
    rfid = mfrc522.MFRC522(spi, cs, rst)

    rfid.set_antenna_gain(0x07 << 4)
    return rfid


def read_rfid(rfid_reader):
    while True:
        (status, tag_type) = rfid_reader.request(rfid_reader.REQALL)
        if status == rfid_reader.OK:
            (status, raw_uid) = rfid_reader.anticoll()
            if status == rfid_reader.OK:
                print("Found something!")
                rfid_data = "{:02x}{:02x}{:02x}{:02x}".format(
                    raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]
                )
                print(rfid_data)
                return rfid_data


def main():
    stop_time: int = 0  # state variable, when was most recent song stopped
    most_recent: int = None  # most recent song id
    pause_ts: float = 0.0  # last pause

    p18 = digitalio.DigitalInOut(board.GP18)
    #  read_rfid()
    player = AudioPlayer(p18)


if __name__ == "__main__":
    main()
