import unittest

from state_machine import StateMachine, TransitionError, InvalidStateError


class ConstructionTests(unittest.TestCase):
    def test_initial_state_is_set(self):
        sm = StateMachine(["idle", "busy"], [("idle", "start", "busy")], "idle")
        self.assertEqual(sm.state, "idle")

    def test_unknown_initial_state_rejected(self):
        with self.assertRaises(InvalidStateError):
            StateMachine(["idle"], [], "missing")

    def test_empty_states_rejected(self):
        with self.assertRaises(ValueError):
            StateMachine([], [], "idle")

    def test_transition_source_must_be_declared(self):
        with self.assertRaises(InvalidStateError):
            StateMachine(["idle"], [("ghost", "go", "idle")], "idle")

    def test_transition_target_must_be_declared(self):
        with self.assertRaises(InvalidStateError):
            StateMachine(["idle"], [("idle", "go", "ghost")], "idle")

    def test_duplicate_transition_pair_rejected(self):
        with self.assertRaises(InvalidStateError):
            StateMachine(
                ["a", "b", "c"],
                [("a", "x", "b"), ("a", "x", "c")],
                "a",
            )


class TransitionTests(unittest.TestCase):
    def _door(self):
        return StateMachine(
            ["closed", "opened"],
            [("closed", "open", "opened"), ("opened", "close", "closed")],
            "closed",
        )

    def test_fire_returns_new_state(self):
        sm = self._door()
        self.assertEqual(sm.fire("open"), "opened")
        self.assertEqual(sm.state, "opened")

    def test_round_trip(self):
        sm = self._door()
        sm.fire("open")
        sm.fire("close")
        self.assertEqual(sm.state, "closed")

    def test_impossible_transition_raises_and_leaves_state(self):
        sm = self._door()
        with self.assertRaises(TransitionError):
            sm.fire("close")  # closed + close is undefined
        # State must be untouched by the failed fire.
        self.assertEqual(sm.state, "closed")

    def test_can_fire(self):
        sm = self._door()
        self.assertTrue(sm.can_fire("open"))
        self.assertFalse(sm.can_fire("close"))
        sm.fire("open")
        self.assertTrue(sm.can_fire("close"))
        self.assertFalse(sm.can_fire("open"))

    def test_undeclared_event_has_no_implicit_self_loop(self):
        sm = self._door()
        with self.assertRaises(TransitionError):
            sm.fire("rename")
        self.assertEqual(sm.state, "closed")

    def test_tuple_events_supported(self):
        # Events are any hashable, so structured keys work without subclassing.
        sm = StateMachine(
            ["idle", "running"],
            [("idle", ("start", 1), "running")],
            "idle",
        )
        self.assertFalse(sm.can_fire(("start", 2)))
        self.assertEqual(sm.fire(("start", 1)), "running")


class ResetTests(unittest.TestCase):
    def test_reset_to_declared_state(self):
        sm = StateMachine(
            ["a", "b"], [("a", "go", "b")], "a"
        )
        sm.fire("go")
        sm.reset("a")
        self.assertEqual(sm.state, "a")

    def test_reset_to_undeclared_state_rejected(self):
        sm = StateMachine(["a"], [], "a")
        with self.assertRaises(InvalidStateError):
            sm.reset("z")
        self.assertEqual(sm.state, "a")


if __name__ == "__main__":
    unittest.main()
