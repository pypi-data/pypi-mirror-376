from dataclasses import dataclass
from functools import singledispatch
from typing import Iterable, override

from predicate.always_false_predicate import AlwaysFalsePredicate
from predicate.always_true_predicate import AlwaysTruePredicate
from predicate.eq_predicate import EqPredicate
from predicate.ge_predicate import GePredicate
from predicate.gt_predicate import GtPredicate
from predicate.in_predicate import InPredicate
from predicate.is_instance_predicate import IsInstancePredicate
from predicate.le_predicate import LePredicate
from predicate.lt_predicate import LtPredicate
from predicate.ne_predicate import NePredicate
from predicate.not_in_predicate import NotInPredicate
from predicate.predicate import (
    AndPredicate,
    Predicate,
)
from predicate.set_predicates import (
    IsRealSubsetPredicate,
    IsRealSupersetPredicate,
    IsSubsetPredicate,
    IsSupersetPredicate,
)


@singledispatch
def implies(predicate: Predicate, other: Predicate) -> bool:
    """Return True if predicate implies another predicate, otherwise False."""
    return False


@implies.register
def _(_predicate: AlwaysFalsePredicate, _other: Predicate) -> bool:
    return True


@implies.register
def _(_predicate: AlwaysTruePredicate, other: Predicate) -> bool:
    return other == AlwaysTruePredicate()


@implies.register
def _(predicate: AndPredicate, other: Predicate) -> bool:
    return other == predicate.left or other == predicate.right


@implies.register
def _(predicate: GePredicate, other: Predicate) -> bool:
    match other:
        case GePredicate(v):
            return predicate.v >= v
        case GtPredicate(v):
            return predicate.v > v
        case _:
            return False


@implies.register
def _(predicate: GtPredicate, other: Predicate) -> bool:
    match other:
        case IsInstancePredicate(instance_klass):
            return predicate.klass == instance_klass[0]  # type: ignore
        case GePredicate(v):
            return predicate.v >= v
        case GtPredicate(v):
            return predicate.v >= v
        case _:
            return False


@implies.register
def _(predicate: EqPredicate, other: Predicate) -> bool:
    match other:
        case IsInstancePredicate(instance_klass):
            return predicate.klass == instance_klass[0]  # type: ignore
        case EqPredicate(v):
            return predicate.v == v
        case NePredicate(v):
            return predicate.v != v
        case GePredicate(v):
            return predicate.v >= v
        case GtPredicate(v):
            return predicate.v > v
        case LePredicate(v):
            return predicate.v <= v
        case LtPredicate(v):
            return predicate.v < v
        case InPredicate(v):
            return predicate.v in v
        case NotInPredicate(v):
            return predicate.v not in v
        case _:
            return False


@implies.register
def _(predicate: IsRealSubsetPredicate, other: Predicate) -> bool:
    match other:
        case IsSubsetPredicate(v):
            return predicate.v == v
        case _:
            return False


@implies.register
def _(predicate: IsRealSupersetPredicate, other: Predicate) -> bool:
    match other:
        case IsSupersetPredicate(v):
            return predicate.v == v
        case _:
            return False


@implies.register
def _(predicate: InPredicate, other: Predicate) -> bool:
    match other:
        case InPredicate(v) if isinstance(v, Iterable) and isinstance(predicate.v, Iterable):
            return set(predicate.v).issubset(v)
        case _:
            return False


@implies.register
def _(predicate: IsInstancePredicate, other: Predicate) -> bool:
    match other:
        case IsInstancePredicate(instance_klass):
            return predicate.instance_klass == instance_klass
        case _:
            return False


@dataclass
class Implies[T](Predicate[T]):
    """A predicate class that models the 'implies' (=>) predicate."""

    left: Predicate
    right: Predicate

    def __call__(self, x) -> bool:
        return not self.left(x) or self.right(x)

    def __repr__(self) -> str:
        return f"{self.left} => {self.right}"

    @override
    def explain_failure(self, x) -> dict:
        return {"reason": f"{self.left} doesn't imply {self.right}"}


def implies_p_p(left: Predicate, right: Predicate) -> Predicate:
    return Implies(left=left, right=right)
