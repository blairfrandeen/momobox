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

# Controls how long the momobox can be paused (momie removed)
# before the song is stopped. After this amount of time, any
# momie placed on the box will start the song from the beginning
RESET_CLOCK_S = 15


class AudioPlayer:
    def __init__(self, hall_sensor, audio_out):
        self.audio = audiopwmio.PWMAudioOut(audio_out)  # board.GP16
        self.song: Optional[str] = None
        self.decoder = None
        self.hall_sensor = digitalio.DigitalInOut(hall_sensor)  # GPIO Pin 18
        self.reset_clock: int = 0
        self.rfid_reader = rfid_reader_init()

        self.listen()

    def play(self):
        self.decoder = audiomp3.MP3Decoder(open(LIBRARY[self.song], "rb"))
        self.audio.play(self.decoder)

    def pause(self):
        self.audio.pause()
        self.reset_clock = time.time()

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
        while True:
            if self.hall_sensor.value is True:
                # Figure out what to play
                if self.is_paused:
                    # See what's on the RFID reader:
                    new_song = read_rfid(self.rfid_reader)

                    time_paused = time.time() - self.reset_clock
                    # check that we still have the same song
                    # and that we haven't been gone too long
                    if new_song == self.song and time_paused < RESET_CLOCK_S:
                        self.resume()
                    else:  # start a new song
                        self.audio.stop()
                        self.song = new_song
                        self.play()
                elif not self.is_playing:
                    # play a new song
                    new_song = read_rfid(self.rfid_reader)

                    # Avoid repeating songs if momie left on top
                    if new_song != self.song:
                        self.song = new_song
                        self.play()
                else:
                    # Keep going!
                    pass
            else:
                if self.is_playing and not self.is_paused:
                    self.pause()
                #  if self.is_paused:
                #  time_paused = time.time() - self.reset_clock
                #  print(time_paused, time.time(), self.reset_clock)
                #  if time_paused < RESET_CLOCK_S:
                #  print("Timeout, stopping!")
                #  self.audio.stop()


def rfid_reader_init():
    sck = board.GP2
    mosi = board.GP3
    miso = board.GP4
    spi = busio.SPI(sck, MOSI=mosi, MISO=miso)

    cs = digitalio.DigitalInOut(board.GP1)
    rst = digitalio.DigitalInOut(board.GP0)
    rfid = mfrc522.MFRC522(spi, cs, rst)

    rfid.set_antenna_gain(0x00 << 4)
    return rfid


def read_rfid(rfid_reader):
    while True:
        print("Making RFID request")
        (status, tag_type) = rfid_reader.request(rfid_reader.REQALL)
        if status == rfid_reader.OK:
            (status, raw_uid) = rfid_reader.anticoll()
            if status == rfid_reader.OK:
                print("Found RFID key: ", end="")
                rfid_data = "{:02x}{:02x}{:02x}{:02x}".format(
                    raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]
                )
                print(rfid_data)
                return rfid_data


def test_hall():
    hall = digitalio.DigitalInOut(board.GP8)
    while True:
        print(hall.value)
        time.sleep(0.2)


def mount_sd_card():
    # Mount SD card
    p1 = digitalio.DigitalInOut(board.GP22)  # assign pin for DET
    try:
        assert p1.value is True  # no SD card inserted
    except AssertionError:
        print("NO SD Card Inserted!")
        exit(-1)
    spi = busio.SPI(board.GP14, board.GP11, board.GP12)
    cs = board.GP13
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")


def main():
    stop_time: int = 0  # state variable, when was most recent song stopped
    most_recent: int = None  # most recent song id
    pause_ts: float = 0.0  # last pause

    hall_sensor = board.GP8
    audio_out = board.GP16
    mount_sd_card()
    #  read_rfid()
    player = AudioPlayer(hall_sensor, audio_out)
    #  test_hall()


if __name__ == "__main__":
    main()
