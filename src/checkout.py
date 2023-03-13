import os

import audiomp3
import audiopwmio
import board
import busio
import storage
import sdcardio

import code

# Test that SD card is working
def test_sd_mount():
    print("Checking SD Card")
    spi = busio.SPI(board.GP14, board.GP11, board.GP12)
    cs = board.GP13
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    try:
        sd_mount = os.listdir("/sd")
        print("SD Card mounted at '/sd'")
        total_size = 0
        for file in sd_mount:
            total_size += os.stat(f"/sd/{file}")[6]
        print(f"{len(sd_mount)} files")
        print(f"{total_size} bytes")
        storage.umount(vfs)
        sdcard.deinit()

    except OSError:
        print("SD Card not mounted!")


def test_audio():
    print("Playing Audio Test...", end="")
    audio = audiopwmio.PWMAudioOut(board.GP16)
    decoder = audiomp3.MP3Decoder(open("soundcheck.mp3", "rb"))
    audio.play(decoder)
    while audio.playing:
        pass
    audio.stop()
    audio.deinit()
    print("Audio test complete!")


def main():
    test_sd_mount()
    test_audio()


if __name__ == "__main__":
    main()
