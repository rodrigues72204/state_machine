"""Finite state machine with explicit, rejectable transitions.

Design decisions
-----------------
- Transitions are declared up-front as a set of ``(source, event, target)``
  triples. Any event fired from a state that has no matching triple raises
  ``TransitionError``. There is no implicit self-loop and no wildcard.
  This is the whole point of the library: an impossible transition must be
  observable as an error, not silently ignored.
- ``event`` is an arbitrary hashable, so callers can use strings or tuples
  (e.g. ``("click", button_id)``) without subclassing.
- Entry/exit callbacks are intentionally omitted. They encourage hidden state
  mutations that defeat the "reject impossible transitions" guarantee the
  caller asked for. If you need side effects, do them at the call site where
  ``fire`` returns the new state.
"""

from __future__ import annotations


class InvalidStateError(ValueError):
    """Raised when a state referenced in setup is not in the declared states."""


class TransitionError(ValueError):
    """Raised when no transition is defined for ``(current_state, event)``."""


class StateMachine:
    """A finite state machine that rejects undeclared transitions.

    Parameters
    ----------
    states:
        Iterable of the states the machine may occupy.
    transitions:
        Iterable of ``(source, event, target)`` triples. Each triple must
        reference states present in ``states``; otherwise ``InvalidStateError``
        is raised at construction time.
    initial:
        The starting state. Must be a member of ``states``.

    Notes
    -----
    Only one target is allowed per ``(source, event)`` pair. Declaring two
    targets for the same pair is a construction error: a state machine that
    can non-deterministically pick a target is exactly the kind of surprise
    this library exists to prevent.
    """

    def __init__(self, states, transitions, initial):
        self._states = set(states)
        if not self._states:
            raise ValueError("states must contain at least one state")
        if initial not in self._states:
            raise InvalidStateError(
                f"initial state {initial!r} is not in states {sorted(self._states)!r}"
            )

        # Keyed by (source, event) -> target. Duplicate keys mean the caller
        # tried to wire non-determinism; we refuse rather than silently
        # overwriting, because overwriting would hide a real bug in their
        # transition table.
        self._table = {}
        for source, event, target in transitions:
            if source not in self._states:
                raise InvalidStateError(
                    f"transition source {source!r} is not a declared state"
                )
            if target not in self._states:
                raise InvalidStateError(
                    f"transition target {target!r} is not a declared state"
                )
            key = (source, event)
            if key in self._table:
                raise InvalidStateError(
                    f"duplicate transition for {key!r}: "
                    f"already targets {self._table[key]!r}, now {target!r}"
                )
            self._table[key] = target

        self._state = initial

    @property
    def state(self):
        """The current state."""
        return self._state

    def can_fire(self, event):
        """Return True if ``event`` would cause a transition from the current state."""
        return (self._state, event) in self._table

    def fire(self, event):
        """Apply ``event`` and return the new state.

        Raises ``TransitionError`` if no transition is defined for the
        current state and event. The machine is left unchanged on error.
        """
        key = (self._state, event)
        try:
            target = self._table[key]
        except KeyError:
            raise TransitionError(
                f"no transition from {self._state!r} on event {event!r}"
            ) from None
        self._state = target
        return target

    def reset(self, state):
        """Force the machine into ``state`` without running a transition.

        ``state`` must be a declared state. Useful for tests and for
        restoring persisted state. It deliberately bypasses the transition
        table; if you want a guarded change, use ``fire``.
        """
        if state not in self._states:
            raise InvalidStateError(
                f"cannot reset to {state!r}: not a declared state"
            )
        self._state = state
