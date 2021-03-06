from __future__ import unicode_literals

from django.db import migrations

from geo_views import migrate


class Migration(migrations.Migration):

    dependencies = [
        ('panoramas', '0012_add_index_to_mv')
    ]

    operations = [
        migrate.ManageMaterializedView(
            view_name="panoramas_adjacencies",
            sql="""
SELECT row_number() OVER (ORDER BY pp.id, pp1.id) AS id,
  pp.id AS from_pano_id,
  pp1.id AS to_pano_id,
  degrees(st_azimuth(geography(pp.geolocation), geography(pp1.geolocation))) AS heading,
  st_distance(geography(pp.geolocation), geography(pp1.geolocation)) AS distance,
  st_z(pp1.geolocation) - st_z(pp.geolocation) AS elevation
FROM panoramas_panorama pp,
    panoramas_panorama pp1
WHERE st_dwithin(pp._geolocation_2d, pp1._geolocation_2d, 0.00036000036::double precision) AND pp1.id <> pp.id
ORDER BY pp.id, pp1.id"""
        ),
    ]
