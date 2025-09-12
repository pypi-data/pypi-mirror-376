"""
Monadic Patterns - Maybe, Either, Result

Provides monadic types for handling optional values, errors, and
transformations in a functional way.
"""

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Generic, List, Optional, TypeVar, Union, cast

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")
L = TypeVar("L")  # Left type for Either
R = TypeVar("R")  # Right type for Either


class Monad(ABC, Generic[T]):
    """Abstract base class for monadic types."""

    @abstractmethod
    def map(self, func: Callable[[T], U]) -> "Monad[U]":
        """Apply a function to the wrapped value."""
        pass

    @abstractmethod
    def bind(self, func: Callable[[T], "Monad[U]"]) -> "Monad[U]":
        """Monadic bind (flatMap)."""
        pass

    @abstractmethod
    def unwrap(self) -> T:
        """Extract the value (may raise exception)."""
        pass


# Maybe Monad
class Maybe(Monad[T]):
    """
    Maybe monad for handling optional values.

    Represents a value that might be present (Just) or absent (Nothing).
    """

    def __init__(self, value: Optional[T] = None) -> None:
        self._value = value

    @staticmethod
    def just(value: T) -> "Maybe[T]":
        """Create a Maybe with a value."""
        if value is None:
            return Maybe.nothing()
        return Maybe(value)

    @staticmethod
    def nothing() -> "Maybe[T]":
        """Create an empty Maybe."""
        return Maybe(None)

    @staticmethod
    def from_optional(value: Optional[T]) -> "Maybe[T]":
        """Create Maybe from an optional value."""
        return Maybe(value)

    def is_just(self) -> bool:
        """Check if this is Just (has value)."""
        return self._value is not None

    def is_nothing(self) -> bool:
        """Check if this is Nothing (no value)."""
        return self._value is None

    def map(self, func: Callable[[T], U]) -> "Maybe[U]":
        """
        Apply function if value exists.

        Example:
            >>> Maybe.just(5).map(lambda x: x * 2)
            Maybe(10)
            >>> Maybe.nothing().map(lambda x: x * 2)
            Maybe(None)
        """
        if self.is_nothing():
            return Maybe.nothing()
        try:
            return Maybe.just(func(cast(T, self._value)))
        except:
            return Maybe.nothing()

    def bind(self, func: Callable[[T], "Maybe[U]"]) -> "Maybe[U]":
        """
        Monadic bind (flatMap).

        Example:
            >>> def safe_div(x): return Maybe.just(10 / x) if x != 0 else Maybe.nothing()
            >>> Maybe.just(2).bind(safe_div)
            Maybe(5.0)
        """
        if self.is_nothing():
            return Maybe.nothing()
        return func(cast(T, self._value))

    def unwrap(self) -> T:
        """Get value or raise exception."""
        if self.is_nothing():
            raise ValueError("Cannot unwrap Nothing")
        return cast(T, self._value)

    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return cast(T, self._value) if self.is_just() else default

    def unwrap_or_else(self, func: Callable[[], T]) -> T:
        """Get value or compute default."""
        return cast(T, self._value) if self.is_just() else func()

    def filter(self, predicate: Callable[[T], bool]) -> "Maybe[T]":
        """Keep value only if predicate is true."""
        if self.is_just() and predicate(cast(T, self._value)):
            return self
        return Maybe.nothing()

    def __repr__(self) -> str:
        if self.is_just():
            return f"Maybe({self._value!r})"
        return "Maybe(None)"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Maybe):
            return False
        return self._value == other._value


# Either Monad
class Either(Monad[R], Generic[L, R]):
    """
    Either monad for handling two possible types.

    Represents a value that is either Left (typically error) or Right (success).
    """

    def __init__(self, left: Optional[L] = None, right: Optional[R] = None) -> None:
        if (left is None) == (right is None):
            raise ValueError("Either must have exactly one value (left or right)")
        self._left = left
        self._right = right

    @staticmethod
    def left(value: L) -> "Either[L, R]":
        """Create a Left Either."""
        return Either(left=value, right=None)

    @staticmethod
    def right(value: R) -> "Either[L, R]":
        """Create a Right Either."""
        return Either(left=None, right=value)

    def is_left(self) -> bool:
        """Check if this is Left."""
        return self._left is not None

    def is_right(self) -> bool:
        """Check if this is Right."""
        return self._right is not None

    def map(self, func: Callable[[R], U]) -> "Either[L, U]":
        """
        Apply function to Right value.

        Example:
            >>> Either.right(5).map(lambda x: x * 2)
            Either(right=10)
            >>> Either.left("error").map(lambda x: x * 2)
            Either(left='error')
        """
        if self.is_left():
            return Either.left(cast(L, self._left))
        try:
            return Either.right(func(cast(R, self._right)))
        except Exception as e:
            return Either.left(e)

    def map_left(self, func: Callable[[L], U]) -> "Either[U, R]":
        """Apply function to Left value."""
        if self.is_right():
            return Either.right(cast(R, self._right))
        return Either.left(func(cast(L, self._left)))

    def bind(self, func: Callable[[R], "Either[L, U]"]) -> "Either[L, U]":
        """
        Monadic bind for Right value.

        Example:
            >>> def safe_div(x): return Either.right(10 / x) if x != 0 else Either.left("Division by zero")
            >>> Either.right(2).bind(safe_div)
            Either(right=5.0)
        """
        if self.is_left():
            return Either.left(cast(L, self._left))
        return func(cast(R, self._right))

    def unwrap(self) -> R:
        """Get Right value or raise exception."""
        if self.is_left():
            if isinstance(self._left, Exception):
                raise self._left
            raise ValueError(f"Cannot unwrap Left: {self._left}")
        return cast(R, self._right)

    def unwrap_left(self) -> L:
        """Get Left value or raise exception."""
        if self.is_right():
            raise ValueError(f"Cannot unwrap Right as Left: {self._right}")
        return cast(L, self._left)

    def unwrap_or(self, default: R) -> R:
        """Get Right value or return default."""
        return cast(R, self._right) if self.is_right() else default

    def unwrap_or_else(self, func: Callable[[L], R]) -> R:
        """Get Right value or compute from Left."""
        return cast(R, self._right) if self.is_right() else func(cast(L, self._left))

    def __repr__(self) -> str:
        if self.is_left():
            return f"Either(left={self._left!r})"
        return f"Either(right={self._right!r})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Either):
            return False
        return self._left == other._left and self._right == other._right


# Result Monad (specialized Either for success/failure)
class Result(Generic[T, E]):
    """
    Result monad for handling success/failure outcomes.

    A specialized Either where Right is Success and Left is Failure.
    """

    def __init__(self, value: Optional[T] = None, error: Optional[E] = None) -> None:
        if (value is None) == (error is None):
            raise ValueError("Result must have exactly one value (success or error)")
        self._value = value
        self._error = error

    @staticmethod
    def success(value: T) -> "Result[T, E]":
        """Create a successful Result."""
        return Result(value=value, error=None)

    @staticmethod
    def failure(error: E) -> "Result[T, E]":
        """Create a failed Result."""
        return Result(value=None, error=error)

    @staticmethod
    def from_try(func: Callable[[], T]) -> "Result[T, Exception]":
        """
        Create Result from a function that might raise exception.

        Example:
            >>> Result.from_try(lambda: 10 / 2)
            Result(success=5.0)
            >>> Result.from_try(lambda: 10 / 0)
            Result(error=ZeroDivisionError(...))
        """
        try:
            return Result.success(func())
        except Exception as e:
            return Result.failure(e)

    def is_success(self) -> bool:
        """Check if this is a success."""
        return self._value is not None

    def is_failure(self) -> bool:
        """Check if this is a failure."""
        return self._error is not None

    def map(self, func: Callable[[T], U]) -> "Result[U, E]":
        """
        Apply function to success value.

        Example:
            >>> Result.success(5).map(lambda x: x * 2)
            Result(success=10)
        """
        if self.is_failure():
            return Result.failure(cast(E, self._error))
        try:
            return Result.success(func(cast(T, self._value)))
        except Exception as e:
            return Result.failure(e)

    def map_error(self, func: Callable[[E], U]) -> "Result[T, U]":
        """Apply function to error value."""
        if self.is_success():
            return Result.success(cast(T, self._value))
        return Result.failure(func(cast(E, self._error)))

    def bind(self, func: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """
        Monadic bind (flatMap).

        Example:
            >>> def safe_div(x): return Result.success(10 / x) if x != 0 else Result.failure("Division by zero")
            >>> Result.success(2).bind(safe_div)
            Result(success=5.0)
        """
        if self.is_failure():
            return Result.failure(cast(E, self._error))
        return func(cast(T, self._value))

    def unwrap(self) -> T:
        """Get success value or raise exception."""
        if self.is_failure():
            if isinstance(self._error, Exception):
                raise self._error
            raise ValueError(f"Result is failure: {self._error}")
        return cast(T, self._value)

    def unwrap_error(self) -> E:
        """Get error value or raise exception."""
        if self.is_success():
            raise ValueError(f"Result is success: {self._value}")
        return cast(E, self._error)

    def unwrap_or(self, default: T) -> T:
        """Get success value or return default."""
        return cast(T, self._value) if self.is_success() else default

    def unwrap_or_else(self, func: Callable[[E], T]) -> T:
        """Get success value or compute from error."""
        return cast(T, self._value) if self.is_success() else func(cast(E, self._error))

    def __repr__(self) -> str:
        if self.is_success():
            return f"Result(success={self._value!r})"
        return f"Result(error={self._error!r})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Result):
            return False
        return self._value == other._value and self._error == other._error


# Monad utility functions
def bind(monad: Monad[T], func: Callable[[T], Monad[U]]) -> Monad[U]:
    """Generic bind operation for any monad."""
    return monad.bind(func)


def lift(func: Callable[[T], U]) -> Callable[[Monad[T]], Monad[U]]:
    """
    Lift a regular function to work with monads.

    Example:
        >>> add_one = lambda x: x + 1
        >>> lifted = lift(add_one)
        >>> lifted(Maybe.just(5))
        Maybe(6)
    """

    def lifted_func(monad: Monad[T]) -> Monad[U]:
        return monad.map(func)

    return lifted_func


def sequence(monads: List[Maybe[T]]) -> Maybe[List[T]]:
    """
    Convert list of Maybe to Maybe of list.
    Returns Nothing if any element is Nothing.

    Example:
        >>> sequence([Maybe.just(1), Maybe.just(2), Maybe.just(3)])
        Maybe([1, 2, 3])
        >>> sequence([Maybe.just(1), Maybe.nothing(), Maybe.just(3)])
        Maybe(None)
    """
    result = []
    for monad in monads:
        if monad.is_nothing():
            return Maybe.nothing()
        result.append(monad.unwrap())
    return Maybe.just(result)


def traverse(func: Callable[[T], Maybe[U]], items: List[T]) -> Maybe[List[U]]:
    """
    Map function returning Maybe over list and collect results.

    Example:
        >>> def safe_div(x): return Maybe.just(10 / x) if x != 0 else Maybe.nothing()
        >>> traverse(safe_div, [2, 5, 10])
        Maybe([5.0, 2.0, 1.0])
        >>> traverse(safe_div, [2, 0, 10])
        Maybe(None)
    """
    result = []
    for item in items:
        maybe_result = func(item)
        if maybe_result.is_nothing():
            return Maybe.nothing()
        result.append(maybe_result.unwrap())
    return Maybe.just(result)


# Decorator for monadic functions
def maybe_decorator(func: Callable[..., Optional[T]]) -> Callable[..., Maybe[T]]:
    """
    Decorator to convert functions returning Optional to Maybe.

    Example:
        >>> @maybe_decorator
        ... def find_user(id: int) -> Optional[str]:
        ...     return "Alice" if id == 1 else None
        >>> find_user(1)
        Maybe('Alice')
        >>> find_user(2)
        Maybe(None)
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Maybe[T]:
        result = func(*args, **kwargs)
        return Maybe.from_optional(result)

    return wrapper


def result_decorator(func: Callable[..., T]) -> Callable[..., Result[T, Exception]]:
    """
    Decorator to convert functions that might raise to Result.

    Example:
        >>> @result_decorator
        ... def divide(a, b):
        ...     return a / b
        >>> divide(10, 2)
        Result(success=5.0)
        >>> divide(10, 0)
        Result(error=ZeroDivisionError(...))
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Result[T, Exception]:
        try:
            return Result.success(func(*args, **kwargs))
        except Exception as e:
            return Result.failure(e)

    return wrapper
