# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-20 11:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('panoramas', '0005_autogenerated')
    ]

    operations = [
        migrations.RunSQL(
            "SELECT AddGeometryColumn ('public','panoramas_panorama','geopoint',4326,'POINT',2)",
            "ALTER TABLE public.panoramas_panorama DROP COLUMN geolocation"
        ),
        migrations.RunSQL(
            "update public.panoramas_panorama set geopoint = ST_PointFromText('POINT('||st_x(geolocation)||' '||st_y(geolocation)||')', 4326)",
            "update public.panoramas_panorama set geopoint = null"
        ),
        migrations.RunSQL(
            "CREATE INDEX panoramas_panorama_geopoint_id ON public.panoramas_panorama USING GIST (geopoint)",
            "DROP INDEX public.panoramas_panorama_geopoint_id"
        ),
    ]
