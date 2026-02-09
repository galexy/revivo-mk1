"""Tests for prefixed entity identifiers.

Verifies that TypeID-based entity IDs:
- Generate correct prefixes for each entity type
- Parse and validate ID strings
- Maintain equality and immutability
- Generate unique, time-sortable identifiers
"""

import time

import pytest
from typeid.errors import InvalidTypeIDStringException, SuffixValidationException

from domain.model.entity_id import (
    AccountId,
    BudgetId,
    CategoryId,
    SplitId,
    TransactionId,
    UserId,
)


class TestAccountId:
    """Tests for AccountId."""

    def test_generate_creates_valid_id(self):
        """Generated ID has correct prefix."""
        aid = AccountId.generate()
        assert aid.value.startswith("acct_")
        assert len(aid.value) > 5  # prefix + UUID portion

    def test_from_string_parses_valid_id(self):
        """Can parse a valid account ID string."""
        aid = AccountId.generate()
        parsed = AccountId.from_string(aid.value)
        assert parsed.value == aid.value

    def test_from_string_rejects_wrong_prefix(self):
        """Cannot parse transaction ID as account ID."""
        tid = TransactionId.generate()
        with pytest.raises(ValueError, match="Expected 'acct' prefix"):
            AccountId.from_string(tid.value)

    def test_prefix_property(self):
        """Can extract prefix from ID."""
        aid = AccountId.generate()
        assert aid.prefix == "acct"

    def test_str_returns_value(self):
        """String representation is the ID value."""
        aid = AccountId.generate()
        assert str(aid) == aid.value

    def test_equality(self):
        """Same value means equal IDs."""
        aid1 = AccountId.generate()
        aid2 = AccountId.from_string(aid1.value)
        assert aid1 == aid2

    def test_different_ids_not_equal(self):
        """Different IDs are not equal."""
        aid1 = AccountId.generate()
        aid2 = AccountId.generate()
        assert aid1 != aid2

    def test_immutable(self):
        """Cannot modify ID after creation."""
        aid = AccountId.generate()
        with pytest.raises(AttributeError):
            aid.value = "acct_modified"


class TestTransactionId:
    """Tests for TransactionId."""

    def test_generate_creates_valid_id(self):
        """Generated ID has correct prefix."""
        tid = TransactionId.generate()
        assert tid.value.startswith("txn_")

    def test_prefix_property(self):
        """Prefix is always 'txn'."""
        tid = TransactionId.generate()
        assert tid.prefix == "txn"

    def test_from_string_parses_valid_id(self):
        """Can parse a valid transaction ID string."""
        tid = TransactionId.generate()
        parsed = TransactionId.from_string(tid.value)
        assert parsed.value == tid.value

    def test_from_string_rejects_wrong_prefix(self):
        """Cannot parse account ID as transaction ID."""
        aid = AccountId.generate()
        with pytest.raises(ValueError, match="Expected 'txn' prefix"):
            TransactionId.from_string(aid.value)


class TestUserId:
    """Tests for UserId."""

    def test_generate_creates_valid_id(self):
        """Generated ID has correct prefix."""
        uid = UserId.generate()
        assert uid.value.startswith("user_")

    def test_prefix_property(self):
        """Prefix is always 'user'."""
        uid = UserId.generate()
        assert uid.prefix == "user"

    def test_from_string_parses_valid_id(self):
        """Can parse a valid user ID string."""
        uid = UserId.generate()
        parsed = UserId.from_string(uid.value)
        assert parsed.value == uid.value

    def test_from_string_rejects_wrong_prefix(self):
        """Cannot parse account ID as user ID."""
        aid = AccountId.generate()
        with pytest.raises(ValueError, match="Expected 'user' prefix"):
            UserId.from_string(aid.value)


class TestCategoryId:
    """Tests for CategoryId."""

    def test_generate_creates_valid_id(self):
        """Generated ID has correct prefix."""
        cid = CategoryId.generate()
        assert cid.value.startswith("cat_")

    def test_prefix_property(self):
        """Prefix is always 'cat'."""
        cid = CategoryId.generate()
        assert cid.prefix == "cat"

    def test_from_string_parses_valid_id(self):
        """Can parse a valid category ID string."""
        cid = CategoryId.generate()
        parsed = CategoryId.from_string(cid.value)
        assert parsed.value == cid.value


class TestBudgetId:
    """Tests for BudgetId."""

    def test_generate_creates_valid_id(self):
        """Generated ID has correct prefix."""
        bid = BudgetId.generate()
        assert bid.value.startswith("budg_")

    def test_prefix_property(self):
        """Prefix is always 'budg'."""
        bid = BudgetId.generate()
        assert bid.prefix == "budg"

    def test_from_string_parses_valid_id(self):
        """Can parse a valid budget ID string."""
        bid = BudgetId.generate()
        parsed = BudgetId.from_string(bid.value)
        assert parsed.value == bid.value


class TestSplitId:
    """Tests for SplitId."""

    def test_generate_creates_valid_id(self):
        """Generated ID has correct prefix."""
        sid = SplitId.generate()
        assert sid.value.startswith("split_")
        assert len(sid.value) > 6  # prefix + UUID portion

    def test_from_string_parses_valid_id(self):
        """Can parse a valid split ID string."""
        sid = SplitId.generate()
        parsed = SplitId.from_string(sid.value)
        assert parsed.value == sid.value

    def test_from_string_rejects_wrong_prefix(self):
        """Cannot parse transaction ID as split ID."""
        tid = TransactionId.generate()
        with pytest.raises(ValueError, match="Expected 'split' prefix"):
            SplitId.from_string(tid.value)

    def test_prefix_property(self):
        """Prefix is always 'split'."""
        sid = SplitId.generate()
        assert sid.prefix == "split"

    def test_str_returns_value(self):
        """String representation is the ID value."""
        sid = SplitId.generate()
        assert str(sid) == sid.value

    def test_equality(self):
        """Same value means equal IDs."""
        sid1 = SplitId.generate()
        sid2 = SplitId.from_string(sid1.value)
        assert sid1 == sid2

    def test_immutable(self):
        """Cannot modify ID after creation."""
        sid = SplitId.generate()
        with pytest.raises(AttributeError):
            sid.value = "split_modified"


class TestEntityIdUniqueness:
    """Tests verifying ID uniqueness."""

    def test_generated_ids_are_unique(self):
        """Each generate() call produces unique ID."""
        ids = [AccountId.generate() for _ in range(100)]
        values = [id.value for id in ids]
        assert len(set(values)) == 100  # All unique

    def test_different_entity_types_have_different_prefixes(self):
        """Each entity type has distinct prefix."""
        prefixes = {
            AccountId.generate().prefix,
            TransactionId.generate().prefix,
            UserId.generate().prefix,
            CategoryId.generate().prefix,
            BudgetId.generate().prefix,
            SplitId.generate().prefix,
        }
        assert prefixes == {"acct", "txn", "user", "cat", "budg", "split"}

    def test_ids_are_sortable_by_creation_time(self):
        """TypeID uses UUID7 which is time-sortable."""
        id1 = AccountId.generate()
        time.sleep(0.01)  # Small delay to ensure different timestamps
        id2 = AccountId.generate()
        # Lexicographic sort should match creation order
        assert id1.value < id2.value


class TestEntityIdEdgeCases:
    """Tests for edge cases and error handling."""

    def test_invalid_format_rejected(self):
        """Completely invalid format is rejected."""
        with pytest.raises(
            (
                ValueError,
                TypeError,
                InvalidTypeIDStringException,
                SuffixValidationException,
            )
        ):
            AccountId.from_string("not_a_valid_id")

    def test_empty_string_rejected(self):
        """Empty string is rejected."""
        with pytest.raises((ValueError, TypeError, InvalidTypeIDStringException)):
            AccountId.from_string("")

    def test_underscore_only_rejected(self):
        """Just underscore is rejected."""
        with pytest.raises((ValueError, TypeError, InvalidTypeIDStringException)):
            AccountId.from_string("_")

    def test_hash_for_dict_key(self):
        """EntityId can be used as dictionary key."""
        aid1 = AccountId.generate()
        aid2 = AccountId.from_string(aid1.value)
        d = {aid1: "test"}
        assert d[aid2] == "test"

    def test_hash_consistency(self):
        """Same value produces same hash."""
        aid1 = AccountId.generate()
        aid2 = AccountId.from_string(aid1.value)
        assert hash(aid1) == hash(aid2)
