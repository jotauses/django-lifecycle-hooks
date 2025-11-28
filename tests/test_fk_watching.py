from django.db import models

from django_lifecycle_hooks import HookType, LifecycleModelMixin, hook


class Author(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "tests"


class Book(LifecycleModelMixin, models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    author_name_changed = models.BooleanField(default=False)

    class Meta:
        app_label = "tests"

    @hook(HookType.BEFORE_UPDATE, when="author.name", has_changed=True)
    def on_author_name_change(self) -> None:
        self.author_name_changed = True


def test_fk_watching(db) -> None:
    author = Author.objects.create(name="Old Name")
    book = Book.objects.create(title="My Book", author=author)

    # Change author name
    author.name = "New Name"
    author.save()

    # Book save should trigger hook if it watches author.name
    # Note: In standard django-lifecycle, this only works if the instance is refreshed or if we set the value on the instance.
    # If we modify the related object separately, the book instance might not know unless we reload or access it.
    # But let's see if the mechanism works when we access it.

    book.save()
    # This might fail because book.author.name is "New Name" but initial state might not have captured "Old Name" correctly if it didn't traverse.

    assert book.author_name_changed is True
