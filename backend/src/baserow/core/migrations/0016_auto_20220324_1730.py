# Generated by Django 3.2.12 on 2022-03-24 17:30

import baserow.core.undo.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0015_alter_userprofile_language'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('type', models.TextField()),
                ('params', models.JSONField(encoder=baserow.core.undo.models.JSONEncoderSupportingDataClasses)),
                ('scope', models.TextField()),
                ('log_type', models.TextField()),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_on',),
            },
        ),
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('type', models.TextField()),
                ('params', models.JSONField(encoder=baserow.core.undo.models.JSONEncoderSupportingDataClasses)),
                ('scope', models.TextField()),
                ('undone_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_on',),
            },
        ),
        migrations.AddIndex(
            model_name='actionlog',
            index=models.Index(fields=['user', '-created_on', 'scope'], name='core_action_user_id_071ab3_idx'),
        ),
        migrations.AddIndex(
            model_name='action',
            index=models.Index(fields=['user', '-created_on', 'scope'], name='core_action_user_id_ee5cdd_idx'),
        ),
    ]
