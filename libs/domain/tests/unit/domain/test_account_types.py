"""Unit tests for account type enumerations.

Verifies that account enums:
- Have all expected values
- Are StrEnum and usable as strings directly
- Serialize correctly to JSON
"""

import json

import pytest

from domain.model.account_types import AccountStatus, AccountSubtype, AccountType


class TestAccountType:
    """Tests for AccountType enumeration."""

    def test_has_seven_account_types(self):
        """AccountType should have exactly 7 values."""
        assert len(AccountType) == 7

    def test_all_expected_values_exist(self):
        """All 7 supported account types should exist."""
        expected = [
            "CHECKING",
            "SAVINGS",
            "CREDIT_CARD",
            "LOAN",
            "BROKERAGE",
            "IRA",
            "REWARDS",
        ]
        actual = [t.name for t in AccountType]
        assert sorted(actual) == sorted(expected)

    def test_enum_values_are_strings(self):
        """Enum values should be lowercase strings via auto()."""
        assert AccountType.CHECKING == "checking"
        assert AccountType.SAVINGS == "savings"
        assert AccountType.CREDIT_CARD == "credit_card"
        assert AccountType.LOAN == "loan"
        assert AccountType.BROKERAGE == "brokerage"
        assert AccountType.IRA == "ira"
        assert AccountType.REWARDS == "rewards"

    def test_usable_as_string_directly(self):
        """AccountType should be usable as a string without .value."""
        account_type = AccountType.CHECKING
        # String operations work directly
        assert account_type.upper() == "CHECKING"
        assert account_type.startswith("check")
        # Equality with string works
        assert account_type == "checking"

    def test_json_serialization(self):
        """AccountType should serialize to JSON as string."""
        data = {"type": AccountType.CREDIT_CARD}
        json_str = json.dumps(data)
        assert json_str == '{"type": "credit_card"}'

    def test_is_instance_of_str(self):
        """AccountType members should be instances of str."""
        assert isinstance(AccountType.CHECKING, str)

    def test_can_create_from_string(self):
        """AccountType can be created from string value."""
        assert AccountType("checking") == AccountType.CHECKING
        assert AccountType("credit_card") == AccountType.CREDIT_CARD


class TestAccountStatus:
    """Tests for AccountStatus enumeration."""

    def test_has_two_statuses(self):
        """AccountStatus should have exactly 2 values."""
        assert len(AccountStatus) == 2

    def test_all_expected_values_exist(self):
        """ACTIVE and CLOSED statuses should exist."""
        expected = ["ACTIVE", "CLOSED"]
        actual = [s.name for s in AccountStatus]
        assert sorted(actual) == sorted(expected)

    def test_enum_values_are_strings(self):
        """Enum values should be lowercase strings via auto()."""
        assert AccountStatus.ACTIVE == "active"
        assert AccountStatus.CLOSED == "closed"

    def test_usable_as_string_directly(self):
        """AccountStatus should be usable as a string without .value."""
        status = AccountStatus.ACTIVE
        assert status == "active"
        assert status.upper() == "ACTIVE"

    def test_json_serialization(self):
        """AccountStatus should serialize to JSON as string."""
        data = {"status": AccountStatus.CLOSED}
        json_str = json.dumps(data)
        assert json_str == '{"status": "closed"}'


class TestAccountSubtype:
    """Tests for AccountSubtype enumeration."""

    def test_has_seven_subtypes(self):
        """AccountSubtype should have exactly 7 values."""
        assert len(AccountSubtype) == 7

    def test_has_three_ira_subtypes(self):
        """Should have Traditional, Roth, and SEP IRA subtypes."""
        ira_subtypes = [
            AccountSubtype.TRADITIONAL_IRA,
            AccountSubtype.ROTH_IRA,
            AccountSubtype.SEP_IRA,
        ]
        assert len(ira_subtypes) == 3
        # Verify values
        assert AccountSubtype.TRADITIONAL_IRA == "traditional_ira"
        assert AccountSubtype.ROTH_IRA == "roth_ira"
        assert AccountSubtype.SEP_IRA == "sep_ira"

    def test_has_four_loan_subtypes(self):
        """Should have Mortgage, Auto, Personal, and Line of Credit subtypes."""
        loan_subtypes = [
            AccountSubtype.MORTGAGE,
            AccountSubtype.AUTO_LOAN,
            AccountSubtype.PERSONAL_LOAN,
            AccountSubtype.LINE_OF_CREDIT,
        ]
        assert len(loan_subtypes) == 4
        # Verify values
        assert AccountSubtype.MORTGAGE == "mortgage"
        assert AccountSubtype.AUTO_LOAN == "auto_loan"
        assert AccountSubtype.PERSONAL_LOAN == "personal_loan"
        assert AccountSubtype.LINE_OF_CREDIT == "line_of_credit"

    def test_usable_as_string_directly(self):
        """AccountSubtype should be usable as a string without .value."""
        subtype = AccountSubtype.ROTH_IRA
        assert subtype == "roth_ira"
        assert subtype.replace("_", " ").title() == "Roth Ira"

    def test_json_serialization(self):
        """AccountSubtype should serialize to JSON as string."""
        data = {"subtype": AccountSubtype.MORTGAGE}
        json_str = json.dumps(data)
        assert json_str == '{"subtype": "mortgage"}'


class TestEnumInteroperability:
    """Tests for enum interoperability with common patterns."""

    def test_enums_work_in_dictionaries(self):
        """Enums should work as dictionary values for serialization."""
        account_data = {
            "name": "My Checking",
            "type": AccountType.CHECKING,
            "status": AccountStatus.ACTIVE,
            "subtype": None,
        }
        # Convert to JSON-serializable dict
        json_str = json.dumps(account_data)
        parsed = json.loads(json_str)
        assert parsed["type"] == "checking"
        assert parsed["status"] == "active"

    def test_enum_comparison_with_strings(self):
        """Enums should compare equal to their string values."""
        assert AccountType.CHECKING == "checking"
        assert "checking" == AccountType.CHECKING
        assert AccountStatus.ACTIVE == "active"
        assert AccountSubtype.MORTGAGE == "mortgage"

    def test_invalid_enum_value_raises_error(self):
        """Creating enum from invalid value should raise ValueError."""
        with pytest.raises(ValueError):
            AccountType("invalid_type")
        with pytest.raises(ValueError):
            AccountStatus("pending")
        with pytest.raises(ValueError):
            AccountSubtype("unknown")
