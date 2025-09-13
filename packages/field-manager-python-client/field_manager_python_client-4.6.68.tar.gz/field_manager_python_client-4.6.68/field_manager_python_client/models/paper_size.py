from enum import Enum


class PaperSize(str, Enum):
    A0 = "A0"
    A1 = "A1"
    A10 = "A10"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"
    A6 = "A6"
    A7 = "A7"
    A8 = "A8"
    A9 = "A9"

    def __str__(self) -> str:
        return str(self.value)
