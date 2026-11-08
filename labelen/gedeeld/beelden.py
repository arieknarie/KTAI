"""De plaatjes voor de browser: stap 2 en stap 3 laten hiermee elk beeld zien.

De beelden worden altijd op volgorde uit de video gelezen (OpenCV springt soms een beeld verkeerd bij het zoeken naar
een beeldnummer). Verder gaan na een herstart, of ver terug gaan, duurt daarom even.
"""

import threading
from collections import OrderedDict

import cv2

from gedeeld.paden import MOVIES

WIDTH = 1920     # zo breed (in pixels) gaat een beeld hoogstens naar de browser
CACHE = 400      # zoveel beelden blijven klaarliggen, zodat een paar beelden terug meteen kan
AHEAD = 25       # zoveel beelden leest het programma alvast vooruit


def jpg(image) -> bytes:
    if image.shape[1] > WIDTH:
        image = cv2.resize(image, (WIDTH, round(image.shape[0] * WIDTH / image.shape[1])), interpolation=cv2.INTER_AREA)
    return cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()


class Images:
    """Geeft het plaatje van elk item. Beelden uit een video worden op volgorde gelezen; de laatste CACHE plaatjes
    blijven klaarliggen."""

    def __init__(self, todo: list):
        self.todo, self.lock, self.cache = todo, threading.Lock(), OrderedDict()
        self.video, self.capture, self.next = None, None, 0
        self.want, self.wake = 0, threading.Event()
        threading.Thread(target=self.read_ahead, daemon=True).start()

    def get(self, i: int) -> bytes:
        item = self.todo[i]
        with self.lock:
            if i not in self.cache:
                if "path" in item:
                    self.keep(i, cv2.imread(item["path"]))
                else:
                    self.read_until(i)
            self.cache.move_to_end(i)
            return self.cache[i]

    def read_until(self, i: int) -> None:
        video, frame = self.todo[i]["video"], self.todo[i]["frame"]
        if video != self.video or frame < self.next:
            if self.capture is not None:
                self.capture.release()
            self.video, self.capture, self.next = video, cv2.VideoCapture(str(MOVIES / video)), 0
        while self.next <= frame:
            ok, image = self.capture.read()
            if not ok:
                raise RuntimeError(f"{video}: beeld {self.next} kon niet gelezen worden")
            if self.next > frame - CACHE:
                self.keep(i - (frame - self.next), image)       # zelfde video: item i hoort bij beeld frame
            self.next += 1

    def keep(self, i: int, image) -> None:
        self.cache[i] = jpg(image)
        while len(self.cache) > CACHE:
            self.cache.popitem(last=False)

    def read_ahead(self) -> None:
        while True:
            self.wake.wait()
            self.wake.clear()
            try:
                for i in range(self.want, min(self.want + AHEAD, len(self.todo))):
                    self.get(i)
            except RuntimeError as error:                     # de browser krijgt de fout bij het beeld zelf
                print(error)

    def show(self, i: int) -> bytes:
        self.want = i + 1
        self.wake.set()
        return self.get(i)
