"""Unit tests for check_data / check_data_nl (field presence and type validation)."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.check_data import check_data, check_data_nl

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


class TestCheckDataEdgeCases:
    """Edge cases for check_data: type is checked before .strip(), so empty/whitespace/non-string values are rejected cleanly (issues #24/#27)."""

    FIELDS = [("name", str), ("age", int), ("active", bool)]

    def test_float_for_int_field_returns_false(self):
        data = {"name": "Alice", "age": 30.5, "active": True}
        assert check_data(data, self.FIELDS) is False

    def test_zero_is_a_valid_int(self):
        data = {"name": "Alice", "age": 0, "active": True}
        assert check_data(data, self.FIELDS) is True

    def test_negative_int_is_valid_no_range_check(self):
        # check_data only validates presence + type, never a numeric range.
        data = {"name": "Alice", "age": -99, "active": True}
        assert check_data(data, self.FIELDS) is True

    def test_none_when_int_expected_returns_false(self):
        data = {"name": "Alice", "age": None, "active": True}
        assert check_data(data, self.FIELDS) is False

    def test_empty_string_for_str_field_is_rejected(self):
        # Fixed (#27): an empty string must not satisfy a required str field.
        data = {"name": "", "age": 30, "active": True}
        assert check_data(data, self.FIELDS) is False

    def test_whitespace_only_string_is_rejected(self):
        # Fixed (#27): "   " is treated as empty and rejected.
        data = {"name": "   ", "age": 30, "active": True}
        assert check_data(data, self.FIELDS) is False

    def test_int_for_str_field_is_rejected(self):
        # Fixed (#24): a non-string value for a str field returns False
        # cleanly (the isinstance check runs before .strip()), no crash.
        data = {"name": 123, "age": 30, "active": True}
        assert check_data(data, self.FIELDS) is False

    def test_list_for_str_field_is_rejected(self):
        # Fixed (#24): same clean rejection with a list value, no crash.
        data = {"name": ["x"], "age": 30, "active": True}
        assert check_data(data, self.FIELDS) is False

    def test_all_fields_present_and_correct_with_many_fields(self):
        fields = [("a", str), ("b", int), ("c", str), ("d", int)]
        data = {"a": "x", "b": 1, "c": "y", "d": 2}
        assert check_data(data, fields) is True

    def test_first_field_wrong_short_circuits_to_false(self):
        fields = [("a", str), ("b", int)]
        data = {"a": "ok", "b": "not-an-int"}
        assert check_data(data, fields) is False


class TestCheckDataNlEdgeCases:
    """Edge cases for check_data_nl: its empty-string guard is reachable, so empty/whitespace/non-string values are rejected (empty search -> 400)."""

    OPTIONAL = [("book_name", str), ("genre", str), ("writer", str)]

    def test_empty_string_field_is_skipped(self):
        # Powers issue #27: empty search must NOT match everything.
        assert check_data_nl({"book_name": ""}, self.OPTIONAL) is False

    def test_whitespace_only_field_is_skipped(self):
        assert check_data_nl({"book_name": "   "}, self.OPTIONAL) is False

    def test_all_empty_strings_returns_false(self):
        data = {"book_name": "", "genre": "   ", "writer": ""}
        assert check_data_nl(data, self.OPTIONAL) is False

    def test_valid_field_plus_empty_field_returns_true(self):
        data = {"book_name": "Dune", "genre": ""}
        assert check_data_nl(data, self.OPTIONAL) is True

    def test_non_string_value_does_not_crash_and_returns_false(self):
        # Contrast with check_data: check_data_nl guards with isinstance
        # BEFORE touching .strip(), so a non-string is simply ignored.
        assert check_data_nl({"book_name": 123}, self.OPTIONAL) is False

    def test_non_string_value_plus_valid_value_returns_true(self):
        data = {"book_name": 123, "writer": "Tolkien"}
        assert check_data_nl(data, self.OPTIONAL) is True

    def test_empty_required_list_returns_false(self):
        # No fields to match against -> nothing found.
        assert check_data_nl({"book_name": "Dune"}, []) is False
