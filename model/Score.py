from dataclasses import dataclass, field

@dataclass
class Score:
    name: float
    path: float
    content: float
    total: float | None = field(init=False)

    def weight_and_calculate(self):
        self.total = (self.name * 3 + self.path * 2 + self.content) / 6
