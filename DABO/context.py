from dataclasses import dataclass


@dataclass
class ContextObj:
    number: int
    role: str
    content: str


class Context:
    """represent the memory of the conversation"""

    def __init__(self):
        self.history: list[ContextObj] = []
        self.counter = 0

    def append(self, role: str, content: str) -> None:
        self.history.append(ContextObj(self.counter, role, content))
        self.counter += 1

    def getContextList(self, start: int = 0, end: int | None = None) -> list[dict[str, str]]:
        if end is None:
            end = len(self.history) - 1

        messages = []

        for obj in self.history:
            if start <= obj.number <= end:
                messages.append({
                    "role": obj.role,
                    "content": obj.content,
                })

        return messages