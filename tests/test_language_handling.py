from json import load
from unittest import TestCase

from pandas import read_csv

from statistics_server.language_handling import handle_categorical_labels_and_order

SIMPLE_DATAFRAME = read_csv("./tests/test_data/categorical/chronill/chronill_year.csv")
TWO_LABELED_COLUMNS_DATAFRAME = read_csv(
    "./tests/test_data/categorical/chronill/chronill_year_age_gr.csv"
)
with open(
    "./tests/test_data/categorical/chronill/meta.json", "r", encoding="utf-8"
) as config_file:
    VARIABLE_CONFIG = load(config_file)

with open("./tests/test_data/group_metadata.json", "r", encoding="utf-8") as config_file:
    GROUPING_CONFIG = load(config_file)


class TestLabelLanguageSwitching(TestCase):

    def test_one_column_switch(self):
        old_values = set(SIMPLE_DATAFRAME["chronill"])
        self.assertIn("Yes", old_values)
        self.assertIn("No", old_values)
        result = handle_categorical_labels_and_order(
            data=SIMPLE_DATAFRAME, metadata=[VARIABLE_CONFIG]
        )
        new_values = set(result["chronill"])
        self.assertEqual({"Ja", "Nein"}, new_values)

    def test_several_column_switch(self):
        main_old_values = set(TWO_LABELED_COLUMNS_DATAFRAME["chronill"])
        secondary_old_values = set(TWO_LABELED_COLUMNS_DATAFRAME["age_gr"])

        self.assertIn("Yes", main_old_values)
        self.assertIn("No", main_old_values)
        self.assertIn("18-29 y.", secondary_old_values)
        self.assertIn("30-45 y.", secondary_old_values)
        result = handle_categorical_labels_and_order(
            data=TWO_LABELED_COLUMNS_DATAFRAME,
            metadata=[VARIABLE_CONFIG, GROUPING_CONFIG["age_gr"]],
        )
        new_main_values = set(result["chronill"])
        self.assertEqual({"Ja", "Nein"}, new_main_values)
        self.assertEqual({"Ja", "Nein"}, new_main_values)
        new_secondary_values = set(result["age_gr"])
        self.assertEqual(
            {"18-29 J.", "30-45 J.", "46-65 J.", "66 und älter"},
            new_secondary_values,
        )

    def test_several_column_no_language_switch(self):
        main_old_values = set(TWO_LABELED_COLUMNS_DATAFRAME["chronill"])
        secondary_old_values = set(TWO_LABELED_COLUMNS_DATAFRAME["age_gr"])

        self.assertIn("Yes", main_old_values)
        self.assertIn("No", main_old_values)
        self.assertIn("18-29 y.", secondary_old_values)
        self.assertIn("30-45 y.", secondary_old_values)
        result = handle_categorical_labels_and_order(
            data=TWO_LABELED_COLUMNS_DATAFRAME,
            metadata=[VARIABLE_CONFIG, GROUPING_CONFIG["age_gr"]],
            language="en",
        )
        new_main_values = set(result["chronill"])
        self.assertEqual({"Yes", "No"}, new_main_values)
        new_secondary_values = set(result["age_gr"])
        self.assertEqual(
            {"18-29 y.", "30-45 y.", "46-65 y.", "66 and older"},
            new_secondary_values,
        )
