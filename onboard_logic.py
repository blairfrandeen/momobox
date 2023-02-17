"""
Mockup for onboard logic for Momobox
"""
from dataclasses import dataclass
import time


@dataclass
class Song:
    """Mockup for MP3 files that can be played"""

    title: str
    length: int  # seconds


# Mockup for database: keys in this dictionary mock the
# RFID codes on individual momies. Songs mock pointers to
# MP3 files on the SD card
library = {
    1: Song("you are my sunshine", 50),
    2: Song("Where have all the cowboys gone?", 70),
}

# admin set variable for how long a song can be paused before it starts
# over from the beginning
RESET_CLOCK_S = 5


def play_song(song_id: int, start_time: int = 0) -> int:
    """Mockup for function that plays MP3 files.
    Arguments:
        song_id: index of song in library (RFID code mock)
        start_time: time at which song was last left off.

    Returns:
        If song is stopped prematurely, returns time at which
        the song was paused."""
    song = library[song_id]
    print(f"Playing {song.title}")
    try:
        for c in range(start_time, song.length):
            # print a string of characters to the screen
            # where it's obvious when we left off and picked up
            print(chr(c + 48), end="", flush=True)
            time.sleep(0.1)
        print("\nSong completed")
        return 0
    except KeyboardInterrupt:  # mocks removing Momie from box
        print()
        return c


def main():
    stop_time: int = 0  # state variable, when was most recent song stopped
    most_recent: int = None  # most recent song id
    pause_ts: float = 0.0  # last pause
    while True:
        # no error checking here rn
        selection = int(input("Select Song ID: "))
        if (
            most_recent is None  # if no recent song
            or selection != most_recent  # or a new song
            or (time.time() - pause_ts) > RESET_CLOCK_S  # or if it's been too long
        ):
            # if not resuming, start at beginning
            start_time = 0
        else:
            # pick up where we left off
            start_time = stop_time
        most_recent = selection
        stop_time = play_song(selection, start_time)

        # Record the time as soon as a song is stopped to compare
        # against RESET_CLOCK_S if time is resumed
        pause_ts = time.time()


if __name__ == "__main__":
    main()
