"""
Represents an abstract item on the menu.
Do not import this class directly, import it from .menu instead.
"""
from abc import ABC, abstractmethod
from typing import Annotated


class MenuItem(ABC):
    """Represents an item on the main menu"""

    weight: Annotated[float, "The weight of the menu item. A lower number means it will be placed higher."] = 10.0
    name: Annotated[str, "Name of the item"] = "Unnamed item"
    description: Annotated[str, "The item's description, what it's supposed to do"] = "Coders fix this"

    @abstractmethod
    def run(self) -> None:
        """What it says on the tin. Interactively runs what the item's supposed to do. What else did you expect?"""

    # The methods below are very useful for sorting
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"

    def __lt__(self, other) -> bool:
        return self.weight < other.weight and self.description < other.name

    def __gt__(self, other) -> bool:
        return self.weight > other.weight and self.description > other.name

    def __eq__(self, other) -> bool:
        return self.weight == other.weight and self.description == other.name

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)
