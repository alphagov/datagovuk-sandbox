import os


class Config:
    APP_ROOT = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, os.pardir))
    SECRET_KEY = os.environ["SECRET_KEY"]

    CONTENT_DIR = os.path.join(APP_ROOT, "content")
    COLLECTIONS_DIR = os.path.join(CONTENT_DIR, "collections")

    # No default: until the OpenSearch domain is provisioned and OPENSEARCH_URL is set on
    # the task definition, this stays None and the search endpoints report themselves as
    # unconfigured rather than failing against an unreachable host. Setting the env var is
    # all that is needed to turn search on - there is no second switch.
    OPENSEARCH_URL = os.getenv("OPENSEARCH_URL")

    # Two separate indices, deliberately not merged: the collections are curated
    # markdown topics, the datasets are CKAN records, and their fields and facets
    # don't line up. Each has its own mapping, routes and API endpoint.
    OPENSEARCH_COLLECTIONS_INDEX = os.getenv(
        "OPENSEARCH_COLLECTIONS_INDEX", "collections"
    )
    OPENSEARCH_DATASETS_INDEX = os.getenv("OPENSEARCH_DATASETS_INDEX", "datasets")

    # All OpenSearch requests are SigV4 signed, so this is always
    # required. Also used to generate RDS IAM auth tokens when DB_IAM_AUTH is on.
    AWS_REGION = os.getenv("AWS_REGION")

    # Terraform outputs the RDS endpoint as "host:port" - no scheme, user or
    # password. When set, database connections use RDS IAM auth: a short-lived
    # token as the password for DB_USER, a role provisioned in SQL with
    # GRANT rds_iam (see application/db.py).
    RDS_ENDPOINT = os.getenv("RDS_ENDPOINT")
    DB_USER = os.getenv("DB_USER", "datagovuk-index")
    DB_NAME = os.getenv("DB_NAME", "ckan")

    # Local fallback, used only when RDS_ENDPOINT is not set: a plain password
    # URL for the compose postgres container (set in .flaskenv).
    DATABASE_URL = os.getenv("DATABASE_URL")


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False
    # compose sets this; the fallback keeps `flask run` outside docker working.
    OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://opensearch:9200")


class TestConfig(Config):
    TESTING = True
