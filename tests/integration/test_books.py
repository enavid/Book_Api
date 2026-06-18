"""
Integration tests for all book endpoints.

Tests marked with # BUG are expected to FAIL because of known bugs in the code.
These tests exist specifically to expose those bugs.
"""
import pytest
import requests
from tests.conftest import (
    BASE_URL,
    unique_user,
    unique_book_id,
    register_and_login,
    auth_headers,
    make_book,
)


class TestGetAllBook:

    def test_requires_authentication(self):
        r = requests.get(f"{BASE_URL}/get_all_book")
        assert r.status_code in (401, 422)

    def test_invalid_token_returns_401(self):
        r = requests.get(f"{BASE_URL}/get_all_book", headers={"Authorization": "Bearer totally.invalid.token"})
        assert r.status_code in (401, 422)

    def test_missing_bearer_prefix_returns_401(self):
        tokens = register_and_login(unique_user())
        r = requests.get(f"{BASE_URL}/get_all_book", headers={"Authorization": tokens["token"]})
        assert r.status_code in (401, 422)

    def test_returns_list_under_book_key(self):
        tokens = register_and_login(unique_user())
        r = requests.get(f"{BASE_URL}/get_all_book", headers=auth_headers(tokens["token"]))
        assert r.status_code == 200
        body = r.json()
        assert "book" in body
        assert isinstance(body["book"], list)

    def test_pagination_per_page_1_returns_exactly_1_item(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id()), headers=h)
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id()), headers=h)
        r = requests.get(f"{BASE_URL}/get_all_book?page=1&per_page=1", headers=h)
        assert r.status_code == 200
        assert len(r.json()["book"]) == 1

    def test_pagination_page_2_returns_different_item_than_page_1(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        bid1, bid2 = unique_book_id(), unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid1), headers=h)
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid2), headers=h)
        page1 = requests.get(f"{BASE_URL}/get_all_book?page=1&per_page=1", headers=h).json()["book"]
        page2 = requests.get(f"{BASE_URL}/get_all_book?page=2&per_page=1", headers=h).json()["book"]
        assert page1[0]["book_id"] != page2[0]["book_id"]

    def test_page_beyond_total_returns_empty_list(self):
        tokens = register_and_login(unique_user())
        r = requests.get(f"{BASE_URL}/get_all_book?page=99999&per_page=100", headers=auth_headers(tokens["token"]))
        assert r.status_code == 200
        assert r.json()["book"] == []

    def test_negative_page_returns_empty_or_valid_response(self):
        tokens = register_and_login(unique_user())
        r = requests.get(f"{BASE_URL}/get_all_book?page=-1&per_page=10", headers=auth_headers(tokens["token"]))
        assert r.status_code == 200


class TestAddBook:

    def test_requires_authentication(self):
        r = requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id()))
        assert r.status_code in (401, 422)

    def test_valid_book_returns_201(self):
        tokens = register_and_login(unique_user())
        r = requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id()), headers=auth_headers(tokens["token"]))
        assert r.status_code == 201

    def test_added_by_is_set_to_logged_in_user(self):
        username = unique_user()
        tokens = register_and_login(username)
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=auth_headers(tokens["token"]))
        r = requests.get(f"{BASE_URL}/get_book/{bid}", headers=auth_headers(tokens["token"]))
        assert r.json()["added_by"] == username

    def test_duplicate_book_id_returns_400(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        r = requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        assert r.status_code == 400

    def test_missing_book_name_returns_400(self):
        tokens = register_and_login(unique_user())
        book = make_book(unique_book_id())
        del book["book_name"]
        r = requests.post(f"{BASE_URL}/add_book", json=book, headers=auth_headers(tokens["token"]))
        assert r.status_code == 400

    def test_missing_book_id_returns_400(self):
        tokens = register_and_login(unique_user())
        book = make_book(unique_book_id())
        del book["book_id"]
        r = requests.post(f"{BASE_URL}/add_book", json=book, headers=auth_headers(tokens["token"]))
        assert r.status_code == 400

    def test_missing_writer_returns_400(self):
        tokens = register_and_login(unique_user())
        book = make_book(unique_book_id())
        del book["writer"]
        r = requests.post(f"{BASE_URL}/add_book", json=book, headers=auth_headers(tokens["token"]))
        assert r.status_code == 400

    def test_book_id_as_string_returns_400(self):
        tokens = register_and_login(unique_user())
        book = make_book(unique_book_id())
        book["book_id"] = "not-an-integer"
        r = requests.post(f"{BASE_URL}/add_book", json=book, headers=auth_headers(tokens["token"]))
        assert r.status_code == 400

    def test_published_year_as_string_returns_400(self):
        tokens = register_and_login(unique_user())
        book = make_book(unique_book_id())
        book["published_year"] = "2024"
        r = requests.post(f"{BASE_URL}/add_book", json=book, headers=auth_headers(tokens["token"]))
        assert r.status_code == 400

    def test_rating_as_string_returns_400(self):
        tokens = register_and_login(unique_user())
        book = make_book(unique_book_id())
        book["rating"] = "five"
        r = requests.post(f"{BASE_URL}/add_book", json=book, headers=auth_headers(tokens["token"]))
        assert r.status_code == 400

    def test_no_body_returns_400_or_415(self):
        tokens = register_and_login(unique_user())
        r = requests.post(f"{BASE_URL}/add_book", headers=auth_headers(tokens["token"]))
        assert r.status_code in (400, 415)

    def test_empty_body_returns_400(self):
        tokens = register_and_login(unique_user())
        r = requests.post(f"{BASE_URL}/add_book", json={}, headers=auth_headers(tokens["token"]))
        assert r.status_code == 400

    def test_book_appears_in_get_all_after_add(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        r = requests.get(f"{BASE_URL}/get_all_book?per_page=10000", headers=h)
        book_ids = [b["book_id"] for b in r.json()["book"]]
        assert bid in book_ids

    def test_two_users_can_add_books_with_different_ids(self):
        tokens1 = register_and_login(unique_user())
        tokens2 = register_and_login(unique_user())
        bid1, bid2 = unique_book_id(), unique_book_id()
        r1 = requests.post(f"{BASE_URL}/add_book", json=make_book(bid1), headers=auth_headers(tokens1["token"]))
        r2 = requests.post(f"{BASE_URL}/add_book", json=make_book(bid2), headers=auth_headers(tokens2["token"]))
        assert r1.status_code == 201
        assert r2.status_code == 201


class TestGetBook:

    def test_requires_authentication(self):
        r = requests.get(f"{BASE_URL}/get_book/1")
        assert r.status_code in (401, 422)

    def test_existing_book_returns_200_with_correct_data(self):
        tokens = register_and_login(unique_user())
        bid = unique_book_id()
        book = make_book(bid, book_name="My Specific Title")
        requests.post(f"{BASE_URL}/add_book", json=book, headers=auth_headers(tokens["token"]))
        r = requests.get(f"{BASE_URL}/get_book/{bid}", headers=auth_headers(tokens["token"]))
        assert r.status_code == 200
        assert r.json()["book_id"] == bid
        assert r.json()["book_name"] == "My Specific Title"

    def test_nonexistent_book_returns_404(self):
        tokens = register_and_login(unique_user())
        r = requests.get(f"{BASE_URL}/get_book/9999999", headers=auth_headers(tokens["token"]))
        assert r.status_code == 404

    def test_response_contains_all_expected_fields(self):
        tokens = register_and_login(unique_user())
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=auth_headers(tokens["token"]))
        r = requests.get(f"{BASE_URL}/get_book/{bid}", headers=auth_headers(tokens["token"]))
        body = r.json()
        for field in ["book_id", "book_name", "book_content", "writer", "published_year", "rating", "genre", "created_at", "added_at", "added_by"]:
            assert field in body, f"Missing field: {field}"

    def test_any_authenticated_user_can_get_any_book(self):
        tokens1 = register_and_login(unique_user())
        tokens2 = register_and_login(unique_user())
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=auth_headers(tokens1["token"]))
        r = requests.get(f"{BASE_URL}/get_book/{bid}", headers=auth_headers(tokens2["token"]))
        assert r.status_code == 200


class TestDeleteBook:

    def test_requires_authentication(self):
        r = requests.delete(f"{BASE_URL}/delete_book/1")
        assert r.status_code in (401, 422)

    def test_owner_can_delete_book(self):
        # BUG: Expected to FAIL with 500 — delete_book does book[book_id] with int key
        # but the dict stores books with string keys (e.g. book['123'] not book[123])
        tokens = register_and_login(unique_user())
        bid = unique_book_id()
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        r = requests.delete(f"{BASE_URL}/delete_book/{bid}", headers=h)
        assert r.status_code == 200  # BUG: returns 500

    def test_deleted_book_is_no_longer_accessible(self):
        # BUG: Depends on delete working — expected to FAIL
        tokens = register_and_login(unique_user())
        bid = unique_book_id()
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        requests.delete(f"{BASE_URL}/delete_book/{bid}", headers=h)
        r = requests.get(f"{BASE_URL}/get_book/{bid}", headers=h)
        assert r.status_code == 404  # BUG: delete doesn't work so book still exists

    def test_nonexistent_book_returns_404_not_500(self):
        # BUG: Expected to FAIL with 500 — line 66 tries book[book_id] (int key)
        # before checking if the book exists, causing KeyError
        tokens = register_and_login(unique_user())
        r = requests.delete(f"{BASE_URL}/delete_book/9999999", headers=auth_headers(tokens["token"]))
        assert r.status_code == 404  # BUG: returns 500

    def test_non_owner_cannot_delete_book(self):
        # BUG: This also crashes with 500 before reaching the authorization check
        user1, user2 = unique_user(), unique_user()
        tokens1 = register_and_login(user1)
        tokens2 = register_and_login(user2)
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=auth_headers(tokens1["token"]))
        r = requests.delete(f"{BASE_URL}/delete_book/{bid}", headers=auth_headers(tokens2["token"]))
        assert r.status_code in (403, 404)  # BUG: returns 500

    def test_delete_returns_correct_http_method(self):
        # Verify DELETE method is required — GET should not work
        tokens = register_and_login(unique_user())
        bid = unique_book_id()
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        r = requests.get(f"{BASE_URL}/delete_book/{bid}", headers=h)
        assert r.status_code == 405  # Method Not Allowed


class TestUpdateBook:

    def test_requires_authentication(self):
        r = requests.post(f"{BASE_URL}/update_book/1", json=make_book(1))
        assert r.status_code in (401, 422)

    def test_owner_can_update_book(self):
        tokens = register_and_login(unique_user())
        bid = unique_book_id()
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        updated = make_book(bid, book_name="Updated Title")
        r = requests.post(f"{BASE_URL}/update_book/{bid}", json=updated, headers=h)
        assert r.status_code == 200

    def test_update_does_not_create_duplicate_entries(self):
        # BUG: Expected to FAIL — update_book stores the updated book with an int key
        # (book[book_id] where book_id is int from URL) but the original was stored
        # with a string key. This creates two entries for the same book.
        tokens = register_and_login(unique_user())
        bid = unique_book_id()
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        requests.post(f"{BASE_URL}/update_book/{bid}", json=make_book(bid, book_name="Updated"), headers=h)

        all_books = requests.get(f"{BASE_URL}/get_all_book?per_page=10000", headers=h).json()["book"]
        count = sum(1 for b in all_books if b["book_id"] == bid)
        assert count == 1  # BUG: count is 2

    def test_updated_title_is_reflected_in_get_book(self):
        tokens = register_and_login(unique_user())
        bid = unique_book_id()
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid, book_name="Old Title"), headers=h)
        requests.post(f"{BASE_URL}/update_book/{bid}", json=make_book(bid, book_name="New Title"), headers=h)
        r = requests.get(f"{BASE_URL}/get_book/{bid}", headers=h)
        assert r.status_code == 200
        assert r.json()["book_name"] == "New Title"

    def test_added_by_is_still_username_after_update_not_jwt_token(self):
        username = unique_user()
        tokens = register_and_login(username)
        bid = unique_book_id()
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        requests.post(f"{BASE_URL}/update_book/{bid}", json=make_book(bid, book_name="Updated"), headers=h)
        r = requests.get(f"{BASE_URL}/get_book/{bid}", headers=h)
        added_by = r.json().get("added_by", "")
        assert added_by == username
        assert not added_by.startswith("Bearer")
        assert len(added_by) < 50

    def test_non_owner_cannot_update_book(self):
        user1, user2 = unique_user(), unique_user()
        tokens1 = register_and_login(user1)
        tokens2 = register_and_login(user2)
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=auth_headers(tokens1["token"]))
        r = requests.post(
            f"{BASE_URL}/update_book/{bid}",
            json=make_book(bid, book_name="Hijacked"),
            headers=auth_headers(tokens2["token"]),
        )
        assert r.status_code == 404

    def test_non_owner_update_does_not_change_book_name(self):
        user1, user2 = unique_user(), unique_user()
        tokens1 = register_and_login(user1)
        tokens2 = register_and_login(user2)
        bid = unique_book_id()
        h1 = auth_headers(tokens1["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid, book_name="Original Title"), headers=h1)
        requests.post(
            f"{BASE_URL}/update_book/{bid}",
            json=make_book(bid, book_name="Hijacked Title"),
            headers=auth_headers(tokens2["token"]),
        )
        r = requests.get(f"{BASE_URL}/get_book/{bid}", headers=h1)
        assert r.json()["book_name"] == "Original Title"

    def test_update_nonexistent_book_returns_404(self):
        tokens = register_and_login(unique_user())
        r = requests.post(
            f"{BASE_URL}/update_book/9999999",
            json=make_book(9999999),
            headers=auth_headers(tokens["token"]),
        )
        assert r.status_code == 404

    def test_missing_required_field_returns_400(self):
        tokens = register_and_login(unique_user())
        bid = unique_book_id()
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        book = make_book(bid)
        del book["book_name"]
        r = requests.post(f"{BASE_URL}/update_book/{bid}", json=book, headers=h)
        assert r.status_code == 400

    def test_update_uses_post_method_not_put(self):
        tokens = register_and_login(unique_user())
        bid = unique_book_id()
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        r = requests.put(f"{BASE_URL}/update_book/{bid}", json=make_book(bid), headers=h)
        assert r.status_code == 405


class TestSearch:

    def test_requires_authentication(self):
        r = requests.post(f"{BASE_URL}/search", json={"book_name": "test"})
        assert r.status_code in (401, 422)

    def test_search_by_book_name_returns_matching_book(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid, book_name="The Crimson Dragon"), headers=h)
        r = requests.post(f"{BASE_URL}/search", json={"book_name": "Crimson"}, headers=h)
        assert r.status_code == 200
        assert any(b["book_id"] == bid for b in r.json())

    def test_search_by_genre_returns_matching_book(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid, genre="UniqueGenreZZZ"), headers=h)
        r = requests.post(f"{BASE_URL}/search", json={"genre": "UniqueGenreZZZ"}, headers=h)
        assert r.status_code == 200
        assert any(b["book_id"] == bid for b in r.json())

    def test_search_by_writer_returns_matching_book(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid, writer="UniqueAuthorXXX"), headers=h)
        r = requests.post(f"{BASE_URL}/search", json={"writer": "UniqueAuthorXXX"}, headers=h)
        assert r.status_code == 200
        assert any(b["book_id"] == bid for b in r.json())

    def test_search_is_case_insensitive(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid, book_name="Great Expectations"), headers=h)
        r = requests.post(f"{BASE_URL}/search", json={"book_name": "great expectations"}, headers=h)
        assert r.status_code == 200
        assert any(b["book_id"] == bid for b in r.json())

    def test_search_with_partial_name_returns_match(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid, book_name="Harry Potter and the Chamber"), headers=h)
        r = requests.post(f"{BASE_URL}/search", json={"book_name": "Harry"}, headers=h)
        assert r.status_code == 200
        assert any(b["book_id"] == bid for b in r.json())

    def test_search_nonexistent_name_returns_empty_list(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        r = requests.post(f"{BASE_URL}/search", json={"book_name": "XYZNONEXISTENTBOOKNAME999"}, headers=h)
        assert r.status_code == 200
        assert r.json() == []

    def test_search_with_no_fields_returns_400(self):
        tokens = register_and_login(unique_user())
        r = requests.post(f"{BASE_URL}/search", json={}, headers=auth_headers(tokens["token"]))
        assert r.status_code == 400

    def test_search_with_no_body_returns_400_or_415(self):
        tokens = register_and_login(unique_user())
        r = requests.post(f"{BASE_URL}/search", headers=auth_headers(tokens["token"]))
        assert r.status_code in (400, 415)

    def test_search_does_not_return_unrelated_books(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        bid_target = unique_book_id()
        bid_other = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid_target, book_name="Target Book Alpha"), headers=h)
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid_other, book_name="Completely Different"), headers=h)
        r = requests.post(f"{BASE_URL}/search", json={"book_name": "Target Book Alpha"}, headers=h)
        results = r.json()
        assert all(b["book_id"] != bid_other for b in results)

    def test_search_result_is_a_list(self):
        tokens = register_and_login(unique_user())
        r = requests.post(f"{BASE_URL}/search", json={"book_name": "anything"}, headers=auth_headers(tokens["token"]))
        assert r.status_code == 200
        assert isinstance(r.json(), list)
