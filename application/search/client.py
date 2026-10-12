import boto3
from flask import current_app
from opensearchpy import OpenSearch, Urllib3AWSV4SignerAuth


class SearchNotConfigured(RuntimeError):
    """AWS Opensearch domain is provisioned yet"""


def get_client():
    url = current_app.config.get("OPENSEARCH_URL", None)
    if url is None:
        raise SearchNotConfigured(
            "Search is not configured. Set OPENSEARCH_URL to enable it."
        )

    # Requests are always SigV4 signed, whatever the host, compose container has
    # security disabled and ignores the Authorization header so the single code path
    # works there with the dummy credentials set in compose.yaml
    credentials = boto3.Session().get_credentials()
    region = current_app.config["AWS_REGION"]
    if credentials is None or region is None:
        raise SearchNotConfigured(
            "AWS credentials and AWS_REGION are required to sign OpenSearch "
            "requests. Locally any dummy values work (see compose.yaml)."
        )
    auth = Urllib3AWSV4SignerAuth(credentials, region, "es")  # es means managed Opensearch

    use_ssl = url.startswith("https://")
    return OpenSearch(
        hosts=[url],
        http_auth=auth,
        use_ssl=use_ssl,
        verify_certs=use_ssl,
    )


def search(search_index, body):
    return get_client().search(
        index=current_app.config[search_index.index_key], body=body
    )
