# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-01 11:19
from __future__ import unicode_literals

from django.db import migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('panoramas', '0014_add_regions'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX from_pano_idx ON public.panoramas_adjacencies (from_pano_id) ",
            "DROP INDEX from_pano_distance_idx ",
        ),
    ]