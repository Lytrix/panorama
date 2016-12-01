# Python
import os, logging
from unittest import mock, skipIf
# Project
from datasets.panoramas.transform.cubic import CubicTransformer
from datasets.panoramas.transform.utils_img_file_cubic import save_as_file_set
from . test_transformer import TestTransformer
from . test_img_file import mock_get_raw_pano

log = logging.getLogger(__name__)

MAX_WIDTH=2048


@skipIf(not os.path.exists('/app/panoramas_test'),
        'Render test skipped: no mounted directory found, run in docker container')
class TestTransformImgCubic(TestTransformer):
    """
    This is more like an integration test than a unit test
    Because it expects a mounted /app/panoramas_test folder, run these in the Docker container

        docker exec -it panorama_web_1 ./manage.py test datasets.panoramas.transform.tests.test_cubic

    look into the .gitignore-ed directory PROJECT/panoramas_test/output for a visual check on the transformations
    """
    @mock.patch('datasets.panoramas.transform.utils_img_file.get_raw_panorama_as_rgb_array',
                side_effect=mock_get_raw_pano)
    def test_transform_cubic_runs_without_errors(self, mock):
        for img in self.images:
            image_tranformer = CubicTransformer(img.path+img.filename, img.heading, img.pitch, img.roll)
            output_path = "/app/test_output/"+img.filename[:-4]
            img_set = image_tranformer.get_projection(target_width=MAX_WIDTH)
            # save_as_file_set(output_path, img_set)
