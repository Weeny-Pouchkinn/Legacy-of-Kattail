"""Regression checks for state-history validation without loading map assets."""
import unittest

import numpy as np

from validate_map import state_history_count, x_crossing_coordinates


class ProvinceCrossingTests(unittest.TestCase):
    def test_horizontal_wrap_is_checked(self):
        pixels = np.array([[1, 1, 2], [3, 3, 4]], dtype=np.uint32)
        self.assertIn((2, 0), x_crossing_coordinates(pixels))
        self.assertIn((1, 0), x_crossing_coordinates(pixels))

    def test_three_colors_and_vertical_edges_are_valid(self):
        pixels = np.array([[1, 2, 2], [1, 3, 3]], dtype=np.uint32)
        self.assertEqual(x_crossing_coordinates(pixels), [])

    def test_no_vertical_wrap(self):
        pixels = np.array([[1, 1, 2], [1, 1, 1], [3, 3, 4]], dtype=np.uint32)
        self.assertEqual(x_crossing_coordinates(pixels), [])


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
