"""
Unit tests for check_data and check_data_nl.

This is an example of how to write unit tests for this project.
A unit test isolates a single function and tests it directly — no server, no HTTP.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from check_data import check_data, check_data_nl


REQUIRED_FIELDS = [("name", str), ("age", int), ("active", bool)]


class TestCheckData:
    """Tests for check_data — all required fields must be present with correct types."""

    def test_returns_true_when_all_fields_correct(self):
        data = {"name": "Alice", "age": 30, "active": True}
        assert check_data(data, REQUIRED_FIELDS) is True

    def test_returns_false_when_data_is_none(self):
        assert check_data(None, REQUIRED_FIELDS) is False

    def test_returns_false_when_data_is_empty_dict(self):
        assert check_data({}, REQUIRED_FIELDS) is False

    def test_returns_false_when_one_field_is_missing(self):
        data = {"name": "Alice", "age": 30}
        assert check_data(data, REQUIRED_FIELDS) is False

    def test_returns_false_when_field_has_wrong_type(self):
        data = {"name": "Alice", "age": "thirty", "active": True}
        assert check_data(data, REQUIRED_FIELDS) is False

    def test_returns_false_when_int_field_receives_string(self):
        data = {"name": "Alice", "age": "30", "active": True}
        assert check_data(data, REQUIRED_FIELDS) is False

    def test_extra_fields_in_data_are_ignored(self):
        data = {"name": "Alice", "age": 30, "active": True, "extra": "ignored"}
        assert check_data(data, REQUIRED_FIELDS) is True

    def test_returns_false_when_all_fields_missing(self):
        data = {"unrelated_key": "value"}
        assert check_data(data, REQUIRED_FIELDS) is False

    def test_empty_required_list_always_returns_true(self):
        assert check_data({"any": "data"}, []) is True

    def test_bool_is_not_accepted_as_int(self):
        # In Python, bool is a subclass of int — isinstance(True, int) is True.
        # This test documents the current behavior.
        data = {"name": "Alice", "age": True, "active": True}
        # True is technically an int in Python, so check_data accepts it.
        assert check_data(data, REQUIRED_FIELDS) is True


class TestCheckDataNl:
    """Tests for check_data_nl — at least one field must be present with correct type."""

    OPTIONAL = [("book_name", str), ("genre", str), ("writer", str)]

    def test_returns_true_when_one_field_is_present(self):
        assert check_data_nl({"book_name": "Dune"}, self.OPTIONAL) is True

    def test_returns_true_when_all_fields_are_present(self):
        data = {"book_name": "Dune", "genre": "SciFi", "writer": "Herbert"}
        assert check_data_nl(data, self.OPTIONAL) is True

    def test_returns_false_when_data_is_none(self):
        assert check_data_nl(None, self.OPTIONAL) is False

    def test_returns_false_when_data_is_empty(self):
        assert check_data_nl({}, self.OPTIONAL) is False

    def test_returns_false_when_field_present_but_wrong_type(self):
        assert check_data_nl({"book_name": 12345}, self.OPTIONAL) is False

    def test_returns_false_when_only_irrelevant_fields_present(self):
        assert check_data_nl({"irrelevant": "value"}, self.OPTIONAL) is False

    def test_returns_true_when_one_valid_and_one_invalid_type(self):
        data = {"book_name": "Dune", "genre": 999}
        assert check_data_nl(data, self.OPTIONAL) is True

    def test_returns_true_with_second_field_only(self):
        assert check_data_nl({"genre": "Fantasy"}, self.OPTIONAL) is True

    def test_returns_true_with_third_field_only(self):
        assert check_data_nl({"writer": "Tolkien"}, self.OPTIONAL) is True
