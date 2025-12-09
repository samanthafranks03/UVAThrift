from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
        ("posts", "0007_post_tags"),
    ]

    operations = [
        migrations.CreateModel(
            name="Bookmark",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="posts.post")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="users.user")),
            ],
            options={
                "ordering": ["-created_at"],
                "unique_together": {("user", "post")},
            },
        ),
    ]
