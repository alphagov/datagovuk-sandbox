"""Postgres connections to the CKAN database.
In AWS, terraform outputs the RDS endpoint as host:port only, no scheme,
user or password
"""

import boto3
import psycopg
from flask import current_app


def _iam_token(host, port, user, region):
    return boto3.client("rds", region_name=region).generate_db_auth_token(
        DBHostname=host, Port=port, DBUsername=user
    )


def rds_connection_info(endpoint, user, dbname, region):
    host, _, port = endpoint.partition(":")
    port = int(port or 5432)
    return {
        "host": host,
        "port": port,
        "user": user,
        "dbname": dbname,
        "password": _iam_token(host, port, user, region),
        "sslmode": "require",
    }


def connect():
    endpoint = current_app.config.get("RDS_ENDPOINT")
    if endpoint:
        return psycopg.connect(
            **rds_connection_info(
                endpoint,
                current_app.config["DB_USER"],
                current_app.config["DB_NAME"],
                current_app.config["AWS_REGION"],
            )
        )
    url = current_app.config.get("DATABASE_URL")
    if url:
        return psycopg.connect(url)
    raise Exception(
        "Database is not configured. Set RDS_ENDPOINT (IAM auth) or "
        "DATABASE_URL (local) to enable it."
    )
