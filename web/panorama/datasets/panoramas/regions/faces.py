import logging

# This dependency is available in the docker container, which has the binaries and bindings installed
import cv2

from datasets.shared.object_store import ObjectStore
from datasets.panoramas.transform import utils_img_file as Img

log = logging.getLogger(__name__)
object_store = ObjectStore()

JUST_ABOVE_HORIZON = 1975
LOWEST_EXPECTED_FACE = 2400
SAMPLE_DISTANCE_H = 355
SAMPLE_DISTANCE_V = 200

ZOOM = [1.41, 1.18, 1.09]

NORMAL = 1
FLIPPED = -1

CASCADE_SETS = [
    ("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_default.xml",
        1.29, 7, NORMAL, 'default'),
    ("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml",
        1.22, 5, NORMAL, 'alt'),
    ("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt2.xml",
        1.22, 5, NORMAL, 'alt2'),
    ("/usr/local/share/OpenCV/haarcascades/haarcascade_profileface.xml",
        1.118, 5, NORMAL, 'profile'),
    ("/usr/local/share/OpenCV/haarcascades/haarcascade_profileface.xml",
        1.118, 5, FLIPPED, 'profile_flip'),
    ("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt_tree.xml",
        1.025, 2, NORMAL, 'alt_tree')
]


def derive(faces, x, y, zoom, cascade, scale_factor, neighbours):
    derived = []
    detected_by = "cascade={}, scaleFactor={}, neighbours={}, zoom={}".format(cascade, scale_factor, neighbours, zoom)
    for (x0, y0, width, height) in faces:
        x1 = int(x0/zoom) + x
        y1 = int(y0/zoom) + y
        w1 = int(width/zoom)
        h1 = int(height/zoom)
        derived.append([(x1, y1), (x1+w1, y1), (x1+w1, y1+h1), (x1, y1+h1), detected_by])
    return derived


class FaceDetector:
    def __init__(self, panorama_path: str):
        """
        :param panorama_path: path of type
                              "2016/08/18/TMX7316010203-000079/pano_0006_000054/equirectangular/panorama_8000.jpg"
        """
        self.panorama_path = panorama_path
        self.panorama_img = None

    def get_face_regions(self):
        self.panorama_img = Img.get_panorama_image(self.panorama_path)
        face_regions = []
        for x in range(0, Img.PANORAMA_WIDTH, SAMPLE_DISTANCE_H):
            for idx, y in enumerate(range(JUST_ABOVE_HORIZON, LOWEST_EXPECTED_FACE, SAMPLE_DISTANCE_V)):
                zoom = ZOOM[idx]
                snippet = Img.sample_image(self.panorama_img, x, y)
                zoomed_snippet = Img.prepare_img(snippet, zoom)
                for cascade_set in CASCADE_SETS:
                    regions = self._detect_regions(zoomed_snippet, cascade_set)
                    derived = derive(regions, x, y, zoom, cascade_set[-1], cascade_set[1], cascade_set[2])
                    face_regions.extend(derived)

        return face_regions

    def _detect_regions(self, snippet, cascade_set):
        regions = []

        face_cascade = cv2.CascadeClassifier(cascade_set[0])
        if cascade_set[3] is FLIPPED:
            detect = cv2.flip(snippet, 0)
        else:
            detect = snippet

        detected_faces = face_cascade.detectMultiScale(
            detect, scaleFactor=cascade_set[1], minNeighbors=cascade_set[2], flags=cv2.CASCADE_DO_CANNY_PRUNING
        )

        if cascade_set[3] is FLIPPED:
            for detected_face in detected_faces:
                detected_face[0] = Img.PANORAMA_WIDTH - detected_face[0] - detected_face[2]

        if len(detected_faces) > 0:
            log.warning('Cascade {}-{} detected: {}.'.format(
                cascade_set[1], cascade_set[0], detected_faces)
            )
            regions.extend(detected_faces)

        return regions
