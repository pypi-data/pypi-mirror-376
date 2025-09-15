from dataclasses import dataclass


@dataclass
class Language:
    name: str | None = None

    def __post_init__(self) -> None:
        self.clean()

    def clean(self) -> None:
        if self.name:
            self.name = self.name.strip().lower() or None

    def is_valid(self) -> bool:
        if not self.name:
            return False

        return len(self.name) == 2 and self.name.isalpha()

    def ask(self) -> None:
        self.name = None
        while not self.name:
            self.name = input("Enter the language (2-letter ISO 639-1 code): ")
            self.clean()
            if not self.is_valid():
                self.name = None
