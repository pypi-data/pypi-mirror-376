"""Module for manipulating dices."""

from __future__ import annotations

import operator
import random
import re
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class Dice:
    """Class representing a dice or a combination of dices."""

    def __init__(
        self,
        desc: str | None = None,
        values: dict[float | bool, float] | None = None,
        *,
        value: float | bool | None = None,
    ) -> None:
        """Initialize a Dice object.

        Args:
            desc (str | None): A string description of the dice expression (e.g., "2d6+3").
            values (dict[float, float] | None): A dictionary mapping outcomes to their probabilities.
            value (float | None): A fixed numeric value representing a certain outcome.

        """
        self.__distribution: dict[float | bool, float]
        if values is not None:
            self.__distribution = values
        elif value is not None:
            self.__distribution = {value: 1.0}
        else:
            self.__distribution = Dice.parse_dice_expression(str(desc)).distribution

    @staticmethod
    def parse_dice_expression(expression: str) -> Dice:
        """Parse a dice expression string and returns a Dice object representing the distribution.

        Args:
            expression (str): The dice expression string (e.g., "1d6-3").

        Returns:
            Dice: A Dice object representing the parsed expression.

        """
        term_pattern = re.compile(r"([+-]?\d*[dD]?\d*)")
        expression = expression.replace(" ", "")
        terms = term_pattern.findall(expression)

        dice: Dice = Dice(value=0)

        for term in terms:
            if not term:
                continue
            if "d" in term.lower():
                sign = -1 if term.startswith("-") else 1
                clean_term = term.lstrip("+-")
                num, sides = clean_term.lower().split("d")
                num = int(num) if num else 1
                sides = dict.fromkeys([float(x) for x in range(1, int(sides) + 1)], 1.0)

                if sign == -1:
                    for _ in range(num):
                        dice -= Dice(values=sides)
                else:
                    for _ in range(num):
                        dice += Dice(values=sides)

            else:
                dice += Dice(value=float(term))
        return dice

    @property
    def distribution(self) -> dict[float | bool, float]:
        """Return the probability distribution of the dice.

        Returns:
            dict[float, float]: A dictionary mapping outcomes to their probabilities.

        """
        return self.__distribution

    def _combine(self, other: Dice, op: Callable[[float | bool, float | bool], float | bool]) -> Dice:
        """Combine two Dice objects using a specified binary operation.

        Args:
            other (Dice): The other Dice object to combine with.
            op (Callable[[float, float], float]): A binary operation function (e.g., addition, subtraction).

        Returns:
            Dice: A new Dice object representing the combined distribution.

        """
        combined_events: defaultdict[float | bool, float] = defaultdict(float)
        for event1, prob1 in self.distribution.items():
            for event2, prob2 in other.distribution.items():
                combined_events[float(op(event1, event2))] += prob1 * prob2
        return Dice(values=combined_events)

    def __add__(self, other: Dice) -> Dice:
        """Add two Dice objects together, combining their distributions.

        Args:
            other (Dice): The other Dice object to add.

        Returns:
            Dice: A new Dice object representing the combined distribution.

        """
        return self._combine(other, operator.add)

    def __sub__(self, other: Dice) -> Dice:
        """Subtract one Dice object from another, combining their distributions.

        Args:
            other (Dice): The other Dice object to subsctract.

        Returns:
            Dice: A new Dice object representing the combined distribution.

        """
        return self._combine(other, operator.sub)

    def __lt__(self, other: Dice) -> Dice:
        """Compare two Dice objects using the less-than operator, combining their distributions.

        Args:
            other (Dice): The other Dice object to compare.

        Returns:
            Dice: A new Dice object representing the combined distribution.

        """
        return self._combine(other, operator.lt)

    def __le__(self, other: Dice) -> Dice:
        """Compare two Dice objects using the less-than-or-equal-to operator, combining their distributions.

        Args:
            other (Dice): The other Dice object to compare.

        Returns:
            Dice: A new Dice object representing the combined distribution.

        """
        return self._combine(other, operator.le)

    def __gt__(self, other: Dice) -> Dice:
        """Compare two Dice objects using the greater-than operator, combining their distributions.

        Args:
            other (Dice): The other Dice object to compare.

        Returns:
            Dice: A new Dice object representing the combined distribution.

        """
        return self._combine(other, operator.gt)

    def __ge__(self, other: Dice) -> Dice:
        """Compare two Dice objects using the greater-than-or-equal-to operator, combining their distributions.

        Args:
            other (Dice): The other Dice object to compare.

        Returns:
            Dice: A new Dice object representing the combined distribution.

        """
        return self._combine(other, operator.ge)

    def __eq__(self, other: object) -> bool:
        """Override the equality operator to compare two Dice objects based on their distributions.

        Args:
            other (Dice): The other Dice object to compare.

        Returns:
            Dice: A new Dice object representing the combined distribution.

        """
        if not isinstance(other, Dice):
            return False
        return self.distribution == other.distribution

    def __hash__(self) -> int:
        """Override the hash function to allow Dice objects to be used in sets and as dictionary keys.

        Returns:
            int: The hash value of the Dice object.

        """
        return hash(frozenset(self.distribution.items()))

    def __ne__(self, other: object) -> bool:
        """Override the inequality operator to compare two Dice objects based on their distributions.

        Args:
            other (Dice): The other Dice object to compare.

        Returns:
            Dice: A new Dice object representing the combined distribution.

        """
        if not isinstance(other, Dice):
            return True
        return self.distribution != other.distribution

    @property
    def space_size(self) -> float:
        """Calculate the total number of possible outcomes (the size of the sample space) for the dice roll.

        Returns:
            float: The total number of possible outcomes.

        """
        return sum(self.__distribution.values())

    @property
    def expected_value(self) -> float:
        """Calculate the expected value of the dice roll based on its probability distribution.

        Returns:
            float: The expected value of the dice roll.

        """
        return sum(value * prob for value, prob in self.__distribution.items()) / self.space_size

    def normalized(self, value: float = 1.0) -> Dice:
        """Return a new Dice instance with its probability distribution normalized.

        Returns:
            Dice: A new Dice object with a normalized probability distribution.

        """
        total = self.space_size
        return Dice(values={outcome: prob * value / total for outcome, prob in self.__distribution.items()})

    def roll(self) -> float | bool:
        """Simulate a roll of the dice based on its probability distribution.

        Returns:
            float: The result of the dice roll.
         calculated 2

        """
        values, weights = zip(*self.__distribution.items(), strict=False)
        return float(sum(random.choices(values, weights=weights, k=1)))  # noqa: S311 it's good enough, it's not cryptography
