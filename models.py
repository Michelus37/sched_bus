from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional


class Suit(Enum):
    SPADES = "pik"
    HEARTS = "herz"
    CLUBS = "kreuz"
    DIAMONDS = "karo"

    @property
    def color_group(self) -> "ColorGroup":
        if self in (Suit.SPADES, Suit.CLUBS):
            return ColorGroup.BLACK
        return ColorGroup.RED


class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class ColorGroup(Enum):
    RED = "rot"
    BLACK = "schwarz"


class HigherLowerGuess(Enum):
    HIGHER = "hoeher"
    LOWER = "tiefer"


class InOutGuess(Enum):
    INSIDE = "innerhalb"
    OUTSIDE = "ausserhalb"


class ComparisonResult(Enum):
    HIGHER = "higher"
    LOWER = "lower"
    EQUAL = "equal"


class PositionResult(Enum):
    INSIDE = "inside"
    OUTSIDE = "outside"


class RoundState(Enum):
    ROUND_INIT = auto()
    AWAIT_GUESS_COLOR = auto()
    DRAW_FIRST_CARD = auto()
    AWAIT_GUESS_HIGHER_LOWER = auto()
    DRAW_SECOND_CARD = auto()
    AWAIT_GUESS_INSIDE_OUTSIDE = auto()
    DRAW_THIRD_CARD = auto()
    AWAIT_GUESS_SUIT = auto()
    DRAW_FOURTH_CARD = auto()
    ROUND_WON = auto()
    ROUND_LOST = auto()


@dataclass(frozen=True, slots=True)
class Card:
    rank: Rank
    suit: Suit

    @property
    def value(self) -> int:
        return self.rank.value

    @property
    def color_group(self) -> ColorGroup:
        return self.suit.color_group

    def __str__(self) -> str:
        return f"{self.rank.name}:{self.suit.value}"


@dataclass(slots=True)
class EvaluationResult:
    step: int
    success: bool
    expected: str
    actual: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GameEvent:
    type: str
    state: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RoundContext:
    stake: int = 500
    state: RoundState = RoundState.ROUND_INIT
    deck: list[Card] = field(default_factory=list)
    drawn_cards: list[Card] = field(default_factory=list)

    guess_color: Optional[ColorGroup] = None
    guess_higher_lower: Optional[HigherLowerGuess] = None
    guess_inside_outside: Optional[InOutGuess] = None
    guess_suit: Optional[Suit] = None

    evaluations: list[EvaluationResult] = field(default_factory=list)
    events: list[GameEvent] = field(default_factory=list)

    is_finished: bool = False
    is_won: Optional[bool] = None
    loss_reason: Optional[str] = None

    @property
    def card1(self) -> Optional[Card]:
        return self.drawn_cards[0] if len(self.drawn_cards) >= 1 else None

    @property
    def card2(self) -> Optional[Card]:
        return self.drawn_cards[1] if len(self.drawn_cards) >= 2 else None

    @property
    def card3(self) -> Optional[Card]:
        return self.drawn_cards[2] if len(self.drawn_cards) >= 3 else None

    @property
    def card4(self) -> Optional[Card]:
        return self.drawn_cards[3] if len(self.drawn_cards) >= 4 else None

    def add_event(self, event_type: str, **payload: Any) -> None:
        self.events.append(
            GameEvent(
                type=event_type,
                state=self.state.name,
                payload=payload,
            )
        )

    def add_evaluation(self, evaluation: EvaluationResult) -> None:
        self.evaluations.append(evaluation)
        self.add_event(
            "STEP_EVALUATED",
            step=evaluation.step,
            success=evaluation.success,
            expected=evaluation.expected,
            actual=evaluation.actual,
            details=evaluation.details,
        )

    def finish_as_lost(self, reason: str) -> None:
        self.state = RoundState.ROUND_LOST
        self.is_finished = True
        self.is_won = False
        self.loss_reason = reason
        self.add_event("ROUND_LOST", reason=reason)

    def finish_as_won(self) -> None:
        self.state = RoundState.ROUND_WON
        self.is_finished = True
        self.is_won = True
        self.loss_reason = None
        self.add_event("ROUND_WON")
