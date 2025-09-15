from dataclasses import dataclass
from typing import Any, Final, override

from predicate.predicate import Predicate


@dataclass
class AlwaysFalsePredicate(Predicate):
    """A predicate class that models the 'False' predicate."""

    def __call__(self, *args, **kwargs) -> bool:
        return False

    def __repr__(self) -> str:
        return "always_false_p"

    @override
    def explain_failure(self, *args, **kwargs) -> dict:
        return {"reason": "Always returns False"}

    @override
    def get_klass(self) -> type:
        return type(Any)


always_false_p: Final[AlwaysFalsePredicate] = AlwaysFalsePredicate()
"""Predicate that always evaluates to False."""

never_p = always_false_p
"""Synonym for always_false_p."""
