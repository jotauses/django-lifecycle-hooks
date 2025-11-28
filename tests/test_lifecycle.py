import django
import pytest
from django.db import models, transaction
from django.test import TransactionTestCase

from django_lifecycle_hooks import HookType, LifecycleModelMixin, hook
from tests.models import Item


@pytest.mark.django_db
class TestLifecycle:
    def test_creation_flow(self) -> None:
        item = Item()
        item.save()

        assert "before_save" in item.hooks_called
        assert "before_create" in item.hooks_called
        assert "after_create" in item.hooks_called
        assert "after_save" in item.hooks_called
        assert "before_update" not in item.hooks_called

    def test_update_flow(self) -> None:
        item = Item.objects.create()
        # Reset manual porque create() dispara hooks
        item.hooks_called = []

        item.count = 5
        item.save()

        assert "before_save" in item.hooks_called
        assert "before_update" in item.hooks_called
        assert "after_update" in item.hooks_called
        assert "after_save" in item.hooks_called
        assert "before_create" not in item.hooks_called

    def test_conditions_specific(self) -> None:
        # Case 1: Failure path (new -> wip)
        item = Item.objects.create(status="new")
        item.hooks_called = []

        item.status = "wip"
        item.save()
        # Condition (was="new", is_now="done") NOT met
        assert "condition_met" not in item.hooks_called

        # Case 2: Success path (new -> done)
        # We create a FRESH item to ensure 'was' state is 'new'
        item2 = Item.objects.create(status="new")
        item2.hooks_called = []

        item2.status = "done"
        item2.save()
        # Condition (was="new", is_now="done") MET
        assert "condition_met" in item2.hooks_called

    def test_has_changed(self) -> None:
        item = Item.objects.create(count=10)
        item.hooks_called = []

        # No change
        item.save()
        assert "count_changed" not in item.hooks_called

        # Change
        item.count = 20
        item.save()
        assert "count_changed" in item.hooks_called


class TestOnCommit(TransactionTestCase):
    # Needs TransactionTestCase to emulate real DB commit behavior

    def test_on_commit_hook(self) -> None:
        class CommitModel(LifecycleModelMixin, models.Model):
            triggered = False

            @hook(HookType.AFTER_SAVE, on_commit=True)
            def set_flag(self) -> None:
                CommitModel.triggered = True

            class Meta:
                app_label = "tests"

        # 1. Create Schema (OUTSIDE atomic block for SQLite compatibility)
        with django.db.connection.schema_editor() as schema_editor:
            schema_editor.create_model(CommitModel)

        try:
            # 2. Run Transaction Logic
            with transaction.atomic():
                instance = CommitModel()
                instance.save()
                # Should not be triggered yet (inside atomic)
                assert CommitModel.triggered is False

            # 3. Verify (After atomic block exits, on_commit fires)
            assert CommitModel.triggered is True

        finally:
            # Cleanup
            with django.db.connection.schema_editor() as schema_editor:
                schema_editor.delete_model(CommitModel)
