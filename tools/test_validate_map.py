"""Regression checks for state-history validation without loading map assets."""
import unittest

from validate_map import state_history_count


class StateHistoryTests(unittest.TestCase):
    def test_duplicate_zzz_after_country_history(self):
        self.assertEqual(state_history_count(
            'state = { history = { owner = FRU } manpower = 1 '
            'history = { owner = ZZZ } }'), 2)

    def test_comments_and_quoted_braces_are_not_history_blocks(self):
        self.assertEqual(state_history_count(
            'state = { name = "history = { # }"\n'
            '# history = { owner = ZZZ }\n'
            'history = { owner = FRU } }'), 1)

    def test_dated_effect_does_not_count_as_second_state_history(self):
        self.assertEqual(state_history_count(
            'state = { history = { owner = FRU '
            '100.1.1 = { set_state_flag = history } } }'), 1)

    def test_missing_history(self):
        self.assertEqual(state_history_count('state = { id = 1 }'), 0)


if __name__ == "__main__":
    unittest.main()
