"""Central configuration for the FaceNet stress tests.

Every tunable setting of the experiments lives in this file, so the scripts
themselves contain no magic numbers. All paths are absolute and derived from
the location of this file, so the scripts can be started from any folder.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
EXPERIMENTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENTS_DIR.parent

PICTURES_DIR = REPO_ROOT / "pictures"
PERSONAL_DIR = PICTURES_DIR / "personal"        # actors outside their role (baseline appearance)
IN_CHARACTER_DIR = PICTURES_DIR / "inCharacter"  # film stills (stress, dirt, beards, dark)
MOVIES_DIR = REPO_ROOT / "movies"

DATA_DIR = EXPERIMENTS_DIR / "data"
FACES_DIR = DATA_DIR / "faces"       # generated face crops (not in git, re-creatable)
LABELS_CSV = DATA_DIR / "labels.csv"  # one row per detected face, incl. manual labels

RESULTS_DIR = EXPERIMENTS_DIR / "results"
FIGURES_DIR = RESULTS_DIR / "figures"            # figures for the paper
INTERMEDIATE_DIR = RESULTS_DIR / "intermediate"  # images of every processing step

# ---------------------------------------------------------------------------
# Identities
# ---------------------------------------------------------------------------
# The four crew members of Das Boot that are studied. The names equal the
# sub-folder names in pictures/personal and pictures/inCharacter.
IDENTITIES = ("DerAlte", "FritzGrade", "Johann", "Werner")

# Words in a picture's file name that tell who is in the picture,
# e.g. "alte_and_werner2.png" -> {DerAlte, Werner}.
NAME_TOKENS = {
    "alte": "DerAlte",
    "deralte": "DerAlte",
    "fritz": "FritzGrade",
    "johann": "Johann",
    "werner": "Werner",
}

# Value to put in the "label" column of labels.csv for a detected face that is
# none of the four identities (an extra, or a false detection).
OTHER_LABEL = "other"

# ---------------------------------------------------------------------------
# Face detection and recognition model (via the deepface library)
# ---------------------------------------------------------------------------
MODEL_NAME = "Facenet"            # FaceNet with a 128-dimensional embedding
DETECTOR_BACKEND = "retinaface"   # robust detector for small and dark faces
MIN_FACE_CONFIDENCE = 0.90        # detections below this score are ignored
FACE_SIZE = 160                   # FaceNet input size: 160 x 160 pixels

# Embeddings are L2-normalised, so the Euclidean distance lies in [0, 2].
# 0.80 is deepface's verified threshold for Facenet with "euclidean_l2":
# a distance below it counts as "same person".
DISTANCE_THRESHOLD = 0.80

# Two face crops whose difference hash differs in at most this many of the 64
# bits are treated as copies of the same face (e.g. the same film still saved
# twice at different sizes). Copies are never compared with each other.
DUPLICATE_HASH_DISTANCE = 6

# ---------------------------------------------------------------------------
# Movie clips
# ---------------------------------------------------------------------------
MOVIE_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mov")
MOVIE_SAMPLE_SECONDS = 1.0   # take one frame per second of footage

# A detected face and a labelled face are the same face when their boxes
# overlap at least this much (intersection over union).
MIN_BOX_OVERLAP = 0.3

# Prediction for a face whose closest reference is further away than
# DISTANCE_THRESHOLD (open-set recognition: an extra should get this).
UNKNOWN = "unknown"

# ---------------------------------------------------------------------------
# Stress Test 1: low resolution
# ---------------------------------------------------------------------------
# The whole still is shrunk by these factors (1/4 = a quarter of the width
# and height), as if the camera were further away or had a lower resolution.
IMAGE_SCALES = (1, 1 / 2, 1 / 4, 1 / 8, 1 / 16)
# Ways to scale the small still back up to its original size. "nearest" only
# repeats pixels (no interpolation) and is the baseline; the others interpolate.
UPSCALE_METHODS = ("nearest", "bicubic", "lanczos")

# ---------------------------------------------------------------------------
# Stress Test 3: poor lighting
# ---------------------------------------------------------------------------
LIGHTING_TYPES = ("dark", "red_alarm")
LIGHTING_SEVERITIES = (0.0, 0.25, 0.5, 0.75, 0.9)  # 0 = untouched, 1 = extreme
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID = (8, 8)
# Apply CLAHE to the reference (gallery) images as well, so that probe and
# gallery go through the same pre-processing.
CLAHE_ON_GALLERY = True

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED = 42
