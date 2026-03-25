from pathlib import Path

COLLECTION_CSV_FIELDS = ["collection", "slug", "link-url", "link-text", "type"]
RESULTS_CSV = COLLECTION_CSV_FIELDS + ["on-page", "reachable"]

DATA_GOV_URL = "https://data.gov.uk"
COLLECTION_URL = DATA_GOV_URL + "/collections"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
COLLECTIONS_CSV = DATA_DIR / "collections" / "collection-urls.csv"
RESULTS_DIR = DATA_DIR / "results"
REPO_URL = "https://github.com/alphagov/datagovuk_find.git"
COLLECTIONS_SUBDIR = "app/content/collections"
