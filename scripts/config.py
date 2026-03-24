from pathlib import Path

COLLECTION_CSV_FIELDS = ["collection", "topic", "url", "link-text", "type"]
RESULTS_CSV = COLLECTION_CSV_FIELDS + ["status-code", "notes"]


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
COLLECTIONS_CSV = DATA_DIR / "collections" / "collection-urls.csv"
RESULTS_DIR = DATA_DIR / "results"
