import unittest

from core.hormone_body import (
    DEFAULT_ADRENALINE,
    DEFAULT_CORTISOL,
    DEFAULT_DOPAMINE,
    DEFAULT_ENDORPHIN,
    DEFAULT_NORADRENALINE,
    DEFAULT_OXYTOCIN,
    DEFAULT_SEROTONIN,
    HORMONE_ADRENALINE,
    HORMONE_CORTISOL,
    HORMONE_DOPAMINE,
    HORMONE_ENDORPHIN,
    HORMONE_NORADRENALINE,
    HORMONE_OXYTOCIN,
    HORMONE_SEROTONIN,
    HORMONES,
    HormoneBody,
)


class HormoneBodyTest(unittest.TestCase):
    def test_defaults_include_all_hormones(self):
        body = HormoneBody()

        self.assertEqual(set(HORMONES), set(body.snapshot()))
        self.assertEqual(DEFAULT_DOPAMINE, body.levels[HORMONE_DOPAMINE])
        self.assertEqual(DEFAULT_SEROTONIN, body.levels[HORMONE_SEROTONIN])
        self.assertEqual(DEFAULT_OXYTOCIN, body.levels[HORMONE_OXYTOCIN])
        self.assertEqual(DEFAULT_ENDORPHIN, body.levels[HORMONE_ENDORPHIN])
        self.assertEqual(DEFAULT_CORTISOL, body.levels[HORMONE_CORTISOL])
        self.assertEqual(DEFAULT_ADRENALINE, body.levels[HORMONE_ADRENALINE])
        self.assertEqual(
            DEFAULT_NORADRENALINE, body.levels[HORMONE_NORADRENALINE]
        )

    def test_apply_delta_changes_and_clamps_levels(self):
        body = HormoneBody()

        body.apply_delta(dopamine=0.20, cortisol=-0.10)
        self.assertAlmostEqual(0.70, body.levels[HORMONE_DOPAMINE])
        self.assertAlmostEqual(0.15, body.levels[HORMONE_CORTISOL])

        body.apply_delta(dopamine=10.0, cortisol=-10.0)
        self.assertEqual(1.0, body.levels[HORMONE_DOPAMINE])
        self.assertEqual(0.0, body.levels[HORMONE_CORTISOL])

    def test_apply_delta_rejects_unknown_hormone(self):
        body = HormoneBody()

        with self.assertRaises(ValueError):
            body.apply_delta(histamine=0.1)

    def test_tick_recovers_toward_baseline(self):
        body = HormoneBody(interaction_rate=0.0)
        body.apply_delta(dopamine=0.40)

        before = body.levels[HORMONE_DOPAMINE]
        body.tick()

        after = body.levels[HORMONE_DOPAMINE]
        self.assertLess(after, before)
        self.assertGreater(after, DEFAULT_DOPAMINE)

    def test_zero_time_scale_freezes_tick(self):
        body = HormoneBody()
        body.apply_delta(cortisol=0.50, dopamine=-0.20)
        before = body.snapshot()

        body.set_time_scale(0.0)
        body.tick()

        self.assertEqual(before, body.snapshot())

    def test_time_scale_speeds_up_tick(self):
        normal = HormoneBody(interaction_rate=0.0)
        fast = HormoneBody(interaction_rate=0.0)
        normal.apply_delta(dopamine=0.40)
        fast.apply_delta(dopamine=0.40)

        normal.tick(dt=1.0)
        fast.set_time_scale(2.0)
        fast.tick(dt=1.0)

        normal_change = 0.90 - normal.levels[HORMONE_DOPAMINE]
        fast_change = 0.90 - fast.levels[HORMONE_DOPAMINE]
        self.assertGreater(fast_change, normal_change)

    def test_set_time_scale_rejects_negative_values(self):
        body = HormoneBody()

        with self.assertRaises(ValueError):
            body.set_time_scale(-1.0)

    def test_cortisol_pushes_reward_bonding_and_comfort_down(self):
        body = HormoneBody(recovery_rate=0.0)
        body.apply_delta(cortisol=0.50)

        body.tick()

        self.assertLess(body.levels[HORMONE_DOPAMINE], DEFAULT_DOPAMINE)
        self.assertLess(body.levels[HORMONE_SEROTONIN], DEFAULT_SEROTONIN)
        self.assertLess(body.levels[HORMONE_OXYTOCIN], DEFAULT_OXYTOCIN)
        self.assertLess(body.levels[HORMONE_ENDORPHIN], DEFAULT_ENDORPHIN)
        self.assertGreater(body.levels[HORMONE_ADRENALINE], DEFAULT_ADRENALINE)
        self.assertGreater(
            body.levels[HORMONE_NORADRENALINE], DEFAULT_NORADRENALINE
        )

    def test_serotonin_reduces_stress_and_arousal(self):
        body = HormoneBody(recovery_rate=0.0)
        body.apply_delta(serotonin=0.30)

        body.tick()

        self.assertLess(body.levels[HORMONE_CORTISOL], DEFAULT_CORTISOL)
        self.assertLess(body.levels[HORMONE_ADRENALINE], DEFAULT_ADRENALINE)

    def test_oxytocin_reduces_stress_and_arousal(self):
        body = HormoneBody(recovery_rate=0.0)
        body.apply_delta(oxytocin=0.30)

        body.tick()

        self.assertLess(body.levels[HORMONE_CORTISOL], DEFAULT_CORTISOL)
        self.assertLess(body.levels[HORMONE_ADRENALINE], DEFAULT_ADRENALINE)

    def test_reset_restores_baseline_and_keeps_time_scale(self):
        body = HormoneBody()
        body.set_time_scale(3.0)
        body.apply_delta(dopamine=0.25, cortisol=0.25)

        body.reset()

        self.assertEqual(body.baseline, body.snapshot())
        self.assertEqual(3.0, body.time_scale)


if __name__ == "__main__":
    unittest.main()
