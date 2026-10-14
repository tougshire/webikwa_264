from django.db import migrations

def articlepage_placement(apps, schema_editor):
    ArticlePagePlacement = apps.get_model("webikwa_264", "ArticlePagePlacement")
    for placement in ArticlePagePlacement.objects.all():
        if (
            placement.zone_break == 1 or
            placement.zone_break == 3
        ):
            placement.break_before = True
        if (
            placement.zone_break == 2 or
            placement.zone_break == 3
        ):
            placement.break_after == True

        placement.save()


class Migration(migrations.Migration):

    dependencies = [
        ('webikwa_264', '0022_articlepageplacement_break_after_and_more'),
    ]

    operations = [
        migrations.RunPython(articlepage_placement)
    ]
