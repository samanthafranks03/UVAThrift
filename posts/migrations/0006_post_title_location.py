from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0005_remove_post_id_hash"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="location",
            field=models.CharField(
                blank=True,
                default="Location not provided",
                max_length=120,
            ),
        ),
        migrations.AddField(
            model_name="post",
            name="title",
            field=models.CharField(
                blank=True,
                default="Unnamed Item",
                max_length=120,
            ),
        ),
    ]
