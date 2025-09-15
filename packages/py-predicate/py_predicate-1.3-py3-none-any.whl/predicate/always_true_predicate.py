from dataclasses import dataclass
from typing import Any, Final, override

from predicate.predicate import Predicate


@dataclass
class AlwaysTruePredicate(Predicate):
    """A predicate class that models the 'True' predicate."""

    def __call__(self, *args, **kwargs) -> bool:
        return True

    def __repr__(self) -> str:
        return "always_true_p"

    @override
    def get_klass(self) -> type:
        return type(Any)


always_true_p: Final[AlwaysTruePredicate] = AlwaysTruePredicate()
"""Predicate that always evaluates to True."""

always_p = always_true_p
"""Synonym for always_true_p."""
