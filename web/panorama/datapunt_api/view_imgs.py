from math import pi, radians, atan2, degrees, log, tan

# Packages
from django.http import HttpResponse, QueryDict, HttpResponseRedirect
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.shortcuts import get_object_or_404
from scipy import misc

from .queryparam_utils import get_float_value, get_int_value, get_request_coord
from datapunt_api.views import PanoramaViewSet
from datasets.panoramas.models import Panorama
from datasets.panoramas.transform.thumbnail import Thumbnail
from datasets.panoramas.serializers import ThumbnailSerializer


class ImgRenderer(renderers.BaseRenderer):
    """
    Doesn't need to do anything, but makes ThumbnailViewSet accept 'image/*'
    """
    media_type = 'image/*'
    format = 'jpg'


class ThumbnailViewSet(PanoramaViewSet):

    """
    View to retrieve thumbs of a panorama

    Parameters:

        pano_id of Panorama

        or:

        lat/lon for wgs84 coords
        x/y for RD coords,

        in the later case, optional Parameters for finding a panorama:

        radius: (int) denoting search radius in meters (default = 20m)

        when providing a Accept: image/* header, you will be redirected to the specific thumbnail

    Optional Parameters for the thumbnail:

        width: in pixels (max 1600) (default 750)
        fov: field of view in degrees horizontal (max 80, default 80), max 20px width per degree
        horizon: fraction of image that is below horizon (default 0.3)
        heading: direction to look at in degrees (default 0)
        aspect: aspect ratio of thumbnail (width/height, min 1) (default 1.5 (3/2)

    """

    lookup_field = 'pano_id'
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer, ImgRenderer)

    def list(self, request):
        """
        Overloading the list view to enable in finding
        the thumb looking at the given point
        """
        coords = get_request_coord(request.query_params)
        if not coords:
            return Response({'error': 'pano_id'})

        _, queryset = self._get_filter_and_queryset(coords, request)

        try:
            pano = queryset[0]
        except IndexError:
            # No results were found
            return Response([])

        heading = round(self._get_heading(pano.geolocation, coords))
        url = self._get_thumb_url(pano.pano_id, heading, request)

        if 'image/' in request.accepted_renderer.media_type:
            return HttpResponseRedirect(url)
        else:
            resp = ThumbnailSerializer({'url': url,
                                        'heading': heading,
                                        'pano_id': pano.pano_id},
                                       context={'request': request})
            return Response(resp.data)

    def _get_thumb_url(self, pano_id, heading, request):
        path = reverse('thumbnail-detail', args=[pano_id], request=request)

        parameters = QueryDict('', mutable=True)
        parameters.update({k: v for k, v in request.query_params.items()
                           if k != 'radius' and k != 'lat' and k != 'lon'})
        parameters['heading'] = heading

        url = '%s?%s' % (path, parameters.urlencode())
        return url

    def _get_heading(self, from_coords, to_coords):
        # http://gis.stackexchange.com/questions/29239/calculate-bearing-between-two-decimal-gps-coordinates
        from_lon = radians(from_coords[0])
        to_lon = radians(to_coords[0])
        d_lon = to_lon - from_lon

        from_lat = radians(from_coords[1])
        to_lat =radians(to_coords[1])
        d_phi = log(tan(to_lat/2.0+pi/4.0)/tan(from_lat/2.0+pi/4.0))

        return degrees(atan2(d_lon, d_phi)) % 360.0

    def retrieve(self, request, pano_id=None, heading=0):
        target_heading = get_int_value(request, 'heading', default=heading, upper=360, strategy='modulo')

        target_width = get_int_value(request, 'width', default=750, lower=1, upper=1600, strategy='cutoff')
        target_fov = get_int_value(request, 'fov', default=80, upper=80, strategy='cutoff')
        target_width, target_fov = self._max_fov_per_width(target_width, target_fov)

        target_horizon = get_float_value(request, 'horizon', default=0.3, lower=0.0, upper=1.0)
        target_aspect = get_float_value(request, 'aspect', default=1.5, lower=1.0)

        pano = get_object_or_404(Panorama, pano_id=pano_id)
        thumb = Thumbnail(pano)
        thumb_img =  thumb.get_image(target_width=target_width,
                                            target_fov=target_fov,
                                            target_horizon=target_horizon,
                                            target_heading=target_heading,
                                            target_aspect=target_aspect)

        response = HttpResponse(content_type="image/jpeg")
        misc.toimage(thumb_img).save(response, "JPEG")
        return response

    def _max_fov_per_width(self, width, fov):
        """
        source resolution is a little over 22 px / degree field of view
        for thumbnails we cap this at 20 px /  degree field of view
        """
        if width/fov > 20:
            return width, round(width/20)
        return width, fov
