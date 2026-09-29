# State Machine

A small finite state machine that rejects transitions you did not declare. Raise an error on an impossible move instead of silently staying put.

```python
from state_machine import StateMachine, TransitionError

sm = StateMachine(
    states=["draft", "submitted", "approved"],
    transitions=[
        ("draft", "submit", "submitted"),
        ("submitted", "approve", "approved"),
        ("submitted", "withdraw", "draft"),
    ],
    initial="draft",
)

sm.fire("submit")          # -> "submitted"
try:
    sm.fire("approve")     # works: submitted -> approved
except TransitionError:
    pass

sm.can_fire("approve")     # True or False depending on current state
sm.reset("draft")          # bypass the table, for tests/persistence
```

## Why

Most FSM libraries let transitions fall through silently or layer on callbacks, wildcards, and entry/exit hooks. The specific problem here is the opposite: you want every illegal transition to be a loud, catchable error so a bug in the caller cannot nudge the machine into a state it was never supposed to reach. That means no wildcard `*` source, no implicit self-loops, and no callbacks that mutate state behind your back. If you need side effects, run them at the call site after `fire` returns.

## Edge you will hit

A `(source, event)` pair may only have one target. Declaring two targets for the same pair is a construction error (`InvalidStateError`), not a silent overwrite. If you genuinely need non-determinism, this is the wrong library.

## Exports

- `StateMachine(states, transitions, initial)` — construct the machine.
- `StateMachine.state` — current state.
- `StateMachine.fire(event)` — apply an event, return the new state, raise `TransitionError` if undefined.
- `StateMachine.can_fire(event)` — `True` if `fire` would succeed from the current state.
- `StateMachine.reset(state)` — jump to a declared state without a transition.
- `TransitionError` — raised on an undeclared transition.
- `InvalidStateError` — raised at construction or `reset` for states not in the declared set.

## Running the tests

```
PYTHONPATH=src python -m unittest discover -s tests
```
