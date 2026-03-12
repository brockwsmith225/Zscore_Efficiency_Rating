from ratingsystems import Stat


class Efficiency(Stat):

    def __init__(self, value: float):
        super().__init__(value)

    def formatted(self, precision: int = 1) -> str:
        return f"{('+' if self.value >= 0 else '')}%.{precision}f%%" % round(self.value * 100, precision)
    