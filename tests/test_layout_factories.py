from unittest import TestCase

from statistics_server.layout import grouping_dropdown, year_range_slider


METADATA = {
    "some-grouping-variable": {
        "variable": "some-grouping-variable",
        "label": "SOMETHING",
        "label_de": "ETWAS",
    },
    "some-other-grouping-variable": {
        "variable": "some-other-grouping-variable",
        "label": "SOMETHING ELSE",
        "label_de": "ETWAS ANDERES",
    },
}


class TestLayoutFabrics(TestCase):

    def test_year_range_slider(self):
        min = 1999
        max = 2000
        slider = year_range_slider(min, max)
        self.assertEqual(min, slider.min)  # type: ignore
        self.assertEqual(max, slider.max)  # type: ignore
        self.assertEqual(1, slider.step)  # type: ignore

    def test_grouping_dropdown_default(self):
        expected_unselected = {"label": "No Grouping", "value": None}
        expected_first_group = {"label": "SOMETHING", "value": "some-grouping-variable"}
        expected_second_group = {
            "label": "SOMETHING ELSE",
            "value": "some-other-grouping-variable",
        }
        _id = "first-dropdown"

        dropdown = grouping_dropdown(METADATA, _id)
        self.assertEqual(_id, dropdown.id)
        self.assertIn(expected_unselected, dropdown.options)
        self.assertIn(expected_first_group, dropdown.options)
        self.assertIn(expected_second_group, dropdown.options)

    def test_grouping_dropdown_german(self):
        expected_unselected = {"label": "Keine Gruppierung", "value": None}
        expected_first_group = {"label": "ETWAS", "value": "some-grouping-variable"}
        expected_second_group = {
            "label": "ETWAS ANDERES",
            "value": "some-other-grouping-variable",
        }
        _id = "first-dropdown"

        dropdown = grouping_dropdown(METADATA, _id, language="de")
        self.assertEqual(_id, dropdown.id)
        self.assertIn(expected_unselected, dropdown.options)
        self.assertIn(expected_first_group, dropdown.options)
        self.assertIn(expected_second_group, dropdown.options)

    def test_grouping_dropdown_exclude_element(self):
        expected_unselected = {"label": "No Grouping", "value": None}
        expected_not_in_groups = {"label": "SOMETHING", "value": "some-grouping-variable"}
        expected_second_group = {
            "label": "SOMETHING ELSE",
            "value": "some-other-grouping-variable",
        }
        _id = "first-dropdown"

        dropdown = grouping_dropdown(
            METADATA, _id, exclude_value=expected_not_in_groups["value"]
        )
        self.assertEqual(_id, dropdown.id)
        self.assertIn(expected_unselected, dropdown.options)
        self.assertNotIn(expected_not_in_groups, dropdown.options)
        self.assertIn(expected_second_group, dropdown.options)
