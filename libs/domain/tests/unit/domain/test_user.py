"""Tests for User domain model."""


class TestUserCreate:
    """Tests for User.create() factory method."""

    def test_create_generates_id(self) -> None:
        """User.create() generates a new UserId."""
        from domain.model.entity_id import HouseholdId
        from domain.model.user import User

        hh_id = HouseholdId.generate()
        user = User.create(
            email="test@example.com",
            display_name="Test User",
            password_hash="hashed_password",
            household_id=hh_id,
        )

        assert user.id is not None
        assert str(user.id).startswith("user_")

    def test_create_normalizes_email_to_lowercase(self) -> None:
        """User.create() lowercases and strips email."""
        from domain.model.entity_id import HouseholdId
        from domain.model.user import User

        hh_id = HouseholdId.generate()
        user = User.create(
            email="  Test@Example.COM  ",
            display_name="Test",
            password_hash="hash",
            household_id=hh_id,
        )

        assert user.email == "test@example.com"

    def test_create_strips_display_name(self) -> None:
        """User.create() strips whitespace from display_name."""
        from domain.model.entity_id import HouseholdId
        from domain.model.user import User

        hh_id = HouseholdId.generate()
        user = User.create(
            email="test@example.com",
            display_name="  Test User  ",
            password_hash="hash",
            household_id=hh_id,
        )

        assert user.display_name == "Test User"

    def test_create_sets_email_verified_false(self) -> None:
        """User.create() sets email_verified to False."""
        from domain.model.entity_id import HouseholdId
        from domain.model.user import User

        hh_id = HouseholdId.generate()
        user = User.create(
            email="test@example.com",
            display_name="Test",
            password_hash="hash",
            household_id=hh_id,
        )

        assert user.email_verified is False
        assert user.email_verified_at is None

    def test_create_emits_user_registered_event(self) -> None:
        """User.create() emits UserRegistered domain event."""
        from domain.events.user_events import UserRegistered
        from domain.model.entity_id import HouseholdId
        from domain.model.user import User

        hh_id = HouseholdId.generate()
        user = User.create(
            email="test@example.com",
            display_name="Test",
            password_hash="hash",
            household_id=hh_id,
        )

        events = user.collect_events()

        assert len(events) == 1
        assert isinstance(events[0], UserRegistered)
        assert events[0].email == "test@example.com"
        assert events[0].user_id == str(user.id)


class TestUserVerifyEmail:
    """Tests for User.verify_email() method."""

    def test_verify_email_sets_verified_true(self) -> None:
        """verify_email() sets email_verified to True."""
        from domain.model.entity_id import HouseholdId
        from domain.model.user import User

        hh_id = HouseholdId.generate()
        user = User.create("test@example.com", "Test", "hash", hh_id)
        user.collect_events()  # Clear registration event

        user.verify_email()

        assert user.email_verified is True
        assert user.email_verified_at is not None

    def test_verify_email_emits_email_verified_event(self) -> None:
        """verify_email() emits EmailVerified domain event."""
        from domain.events.user_events import EmailVerified
        from domain.model.entity_id import HouseholdId
        from domain.model.user import User

        hh_id = HouseholdId.generate()
        user = User.create("test@example.com", "Test", "hash", hh_id)
        user.collect_events()  # Clear registration event

        user.verify_email()
        events = user.collect_events()

        assert len(events) == 1
        assert isinstance(events[0], EmailVerified)
        assert events[0].email == "test@example.com"

    def test_verify_email_is_idempotent(self) -> None:
        """verify_email() on already verified user is a no-op."""
        from domain.model.entity_id import HouseholdId
        from domain.model.user import User

        hh_id = HouseholdId.generate()
        user = User.create("test@example.com", "Test", "hash", hh_id)
        user.collect_events()

        user.verify_email()
        first_verified_at = user.email_verified_at
        user.collect_events()  # Clear first event

        user.verify_email()  # Second call
        events = user.collect_events()

        assert len(events) == 0  # No new event
        assert user.email_verified_at == first_verified_at  # Timestamp unchanged


class TestUserCollectEvents:
    """Tests for User.collect_events() method."""

    def test_collect_events_clears_after_collection(self) -> None:
        """collect_events() clears the event list."""
        from domain.model.entity_id import HouseholdId
        from domain.model.user import User

        hh_id = HouseholdId.generate()
        user = User.create("test@example.com", "Test", "hash", hh_id)

        first = user.collect_events()
        second = user.collect_events()

        assert len(first) == 1
        assert len(second) == 0
