"""
Mockup for onboard logic for Momobox
"""
import time

import audiomp3
import audiopwmio
import board
import busio
import digitalio
import sdcardio
import storage

import mfrc522


# Dictionary to map RFID codes to song/story path names
# TODO: Make this into human-readable file outside of
# operational code
LIBRARY = {
    "23d95433": "wappin.mp3",
    "b8003433": "shavingcream.mp3",
    "88046318": "/sd/wildthings.mp3",
    "8804710a": "/sd/greeneggs.mp3",
    "8804635b": "/sd/peppa.mp3",
}

RESET_CLOCK_S = 5


class AudioPlayer:
    def __init__(self):
        self.audio = audiopwmio.PWMAudioOut(board.GP16)
        self.song: Option[str] = None  # RFID string for last song
        self.decoder = None
        #  self.hall_sensor = hall_sensor  # GPIO Pin 18
        self.reset_clock = 0
        self.rfid_reader = rfid_reader_init()

        self.listen()

    def play(self):
        self.decoder = audiomp3.MP3Decoder(open(LIBRARY[self.song], "rb"))
        self.audio.play(self.decoder)
        print("Playing a song for you...")
        #  while self.audio.playing:
        #  if not check_rfid(self.rfid_reader, self.song):
        #  print("Momie removed!")
        #  self.pause()
        #  break

    def pause(self):
        self.audio.pause()
        self.reset_clock = time.time()
        #  while self.audio.paused:
        #  if check_rfid(self.rfid_reader, self.song):
        #  self.resume()

    def resume(self):
        self.audio.resume()

    def unload(self):
        self.audio.stop()

    @property
    def is_playing(self):
        return self.audio.playing

    @property
    def is_paused(self):
        return self.audio.paused

    def listen(self):
        # State machine
        while True:
            if self.is_paused:
                # Check RFID chip
                rfid_key = read_rfid(self.rfid_reader)
                # If same as current song, then resume
                time_paused = time.time() - self.reset_clock
                if rfid_key == self.song and time_paused < RESET_CLOCK_S:
                    self.resume()
                # If different song, start that song
                else:
                    self.song = rfid_key
                    self.play()
            if self.is_playing:
                # Check to make sure the momie is still there
                if not check_rfid(self.rfid_reader, self.song):
                    print("Momie removed!")
                    self.pause()
            else:  # not paused or playing i.e. stopped
                # We need one failed RFID check before we start playing
                # the same song again. This prevents songs from
                # repeating if a momie is left attached.
                if self.song is not None and check_rfid(self.rfid_reader, self.song):
                    continue
                print("Place RFID card on sensor to select song")
                self.song = read_rfid(self.rfid_reader)
                self.play()

    def get_input(self):
        print("Place RFID card on sensor to select song")
        self.song = read_rfid(self.rfid_reader)
        self.play()


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


def check_rfid(rfid_reader, expected_data):
    for _ in range(4):
        (status, tag_type) = rfid_reader.request(rfid_reader.REQALL)
        #  print("First Check: ", status, tag_type)
        if status == rfid_reader.OK:
            (status, raw_uid) = rfid_reader.anticoll()
            #  print("Second Check: ", status, raw_uid)
            if status == rfid_reader.OK:
                rfid_data = "{:02x}{:02x}{:02x}{:02x}".format(
                    raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]
                )
                if rfid_data == expected_data:
                    return True
                return False
    return False


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

    # Mount SD card
    p1 = digitalio.DigitalInOut(board.GP22)  # assign pin for DET
    assert p1.value is True  # no SD card inserted
    spi = busio.SPI(board.GP14, board.GP11, board.GP12)
    cs = board.GP13
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")

    #  p18 = digitalio.DigitalInOut(board.GP18)
    #  read_rfid()
    player = AudioPlayer()


if __name__ == "__main__":
    main()
