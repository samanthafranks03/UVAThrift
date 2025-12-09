from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0007_post_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="status",
            field=models.CharField(choices=[("active", "Active"), ("closed", "Closed")], default="active", max_length=12),
        ),
    ]
