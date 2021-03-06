from django.conf import settings
from PIL.Image import BICUBIC

from datasets.panoramas.models import Panorama
from datasets.shared.object_store import ObjectStore
from . transformer import PANO_FOV, PANO_HORIZON, PANO_ASPECT
from . utils_img_file import get_panorama_image

object_store = ObjectStore()


def calculate_crop(source_width, target_fov, target_aspect, target_heading, target_horizon):
    target_center = source_width / 2 + target_heading * source_width / 360
    chunk_width = source_width * target_fov / PANO_FOV
    chunk_height = chunk_width / target_aspect
    chunk_above_horizon = chunk_height * (1 - target_horizon)

    left = target_center - chunk_width / 2
    top = (1 - PANO_HORIZON) * source_width / PANO_ASPECT - chunk_above_horizon
    right = left + chunk_width
    bottom = top + chunk_height

    return int(left), int(top), int(right), int(bottom)


def choose_source_image_and_width(target_fov, target_width):
    pixels_per_degree = target_width / target_fov
    if pixels_per_degree > 4000 / 360:
        return 'full', 8000
    elif pixels_per_degree > 2000 / 360:
        return 'medium', 4000
    return 'small', 2000


class Thumbnail:
    def __init__(self, panorama: Panorama):
        self.panorama = panorama

    def get_image(self, target_width=750, target_fov=80, target_horizon=0.3, target_heading=0, target_aspect=1.5):
        source_image, source_width = choose_source_image_and_width(target_fov, target_width)

        # calculate the crop as part of the source_image, meeting requested fov, aspect, heading and horizon
        left, top, right, bottom = calculate_crop(source_width, target_fov, target_aspect, target_heading, target_horizon)
        width, height = right-left, bottom-top

        image_path = self.panorama.equirectangular_img_urls[source_image].replace(settings.PANO_IMAGE_URL+'/', '')
        full_img = get_panorama_image(image_path)

        thumbnail = full_img.crop((left, top, right, bottom))
        # if crop is outside source image:
        if right > source_width:
            # calculate the crop of the part that is missing
            crop_wrapped = (0 if left <= source_width else left-source_width, top, right-source_width, bottom)
            wrap_img = full_img.crop(crop_wrapped)
            # add the extra part to the right of the thumbnail
            thumbnail.paste(wrap_img, (width-(crop_wrapped[2]-crop_wrapped[0]), 0, width, height))

        # resize thumbnail to requested width
        return thumbnail.resize((target_width, int(target_width/target_aspect)), BICUBIC)
