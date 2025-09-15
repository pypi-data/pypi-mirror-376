from abc import abstractmethod
from dataclasses import dataclass
from typing import override

from predicate.predicate import ConstrainedT, Predicate


@dataclass
class RangePredicate[T](Predicate[T]):
    """Abstract base class."""

    @abstractmethod
    def __call__(self, x: T) -> bool: ...

    lower: ConstrainedT
    upper: ConstrainedT

    @override
    def get_klass(self) -> type:
        return type(self.lower)


@dataclass
# class GeLePredicate[T](Predicate[T]):
class GeLePredicate[T](RangePredicate[T]):
    """A predicate class that models the 'lower <= x <= upper' predicate."""

    def __call__(self, x: T) -> bool:
        return self.lower <= x <= self.upper

    def __repr__(self) -> str:
        return f"ge_le_p({self.lower!r}, {self.upper!r})"

    @override
    def explain_failure(self, x: T) -> dict:
        return {"reason": f"{x!r} is not greater equal {self.lower!r} and less equal {self.upper!r}"}


@dataclass
class GeLtPredicate[T](RangePredicate[T]):
    """A predicate class that models the 'lower <= x < upper' predicate."""

    def __call__(self, x: T) -> bool:
        return self.lower <= x < self.upper

    def __repr__(self) -> str:
        return f"ge_lt_p({self.lower!r}, {self.upper!r})"

    @override
    def explain_failure(self, x: T) -> dict:
        return {"reason": f"{x!r} is not greater equal {self.lower!r} and less than {self.upper!r}"}


@dataclass
class GtLePredicate[T](RangePredicate[T]):
    """A predicate class that models the 'lower < x <= upper' predicate."""

    def __call__(self, x: T) -> bool:
        return self.lower < x <= self.upper

    def __repr__(self) -> str:
        return f"gt_le_p({self.lower!r}, {self.upper!r})"

    @override
    def explain_failure(self, x: T) -> dict:
        return {
            "reason": f"{x!r} is not greater than {self.lower!r} and less than or equal to {self.upper!r}",
        }


@dataclass
class GtLtPredicate[T](RangePredicate[T]):
    """A predicate class that models the 'lower < x < upper' predicate."""

    def __call__(self, x: T) -> bool:
        return self.lower < x < self.upper

    def __repr__(self) -> str:
        return f"gt_lt_p({self.lower!r}, {self.upper!r})"

    @override
    def explain_failure(self, x: T) -> dict:
        return {"reason": f"{x!r} is not greater than {self.lower!r} and less than {self.upper!r}"}


def ge_le_p(lower: ConstrainedT, upper: ConstrainedT) -> GeLePredicate[ConstrainedT]:
    """Return True if the value is greater or equal than the constant, otherwise False."""
    return GeLePredicate(lower=lower, upper=upper)


def ge_lt_p(lower: ConstrainedT, upper: ConstrainedT) -> GeLtPredicate[ConstrainedT]:
    """Return True if the value is greater or equal than the constant, otherwise False."""
    return GeLtPredicate(lower=lower, upper=upper)


def gt_le_p(lower: ConstrainedT, upper: ConstrainedT) -> GtLePredicate[ConstrainedT]:
    """Return True if the value is greater or equal than the constant, otherwise False."""
    return GtLePredicate(lower=lower, upper=upper)


def gt_lt_p(lower: ConstrainedT, upper: ConstrainedT) -> GtLtPredicate[ConstrainedT]:
    """Return True if the value is greater or equal than the constant, otherwise False."""
    return GtLtPredicate(lower=lower, upper=upper)
