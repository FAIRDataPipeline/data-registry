import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from django.conf import settings

# the SHA-1 of no bytes: the one file a 0-byte object can be
EMPTY_FILE_SHA1 = "da39a3ee5e6b4b0d3255bfef95601890afd80709"


# An S3 client for the default bucket
def _client():
    bucket = settings.BUCKETS["default"]
    session = boto3.session.Session()
    return session.client(
        service_name="s3",
        aws_access_key_id=bucket["access_key"],
        aws_secret_access_key=bucket["secret_key"],
        endpoint_url=bucket["url"],
        # boto3 presigns S3 URLs with the legacy SigV2 unless told otherwise,
        # and SigV2 URLs fail behind a proxy that rewrites the path
        config=Config(signature_version="s3v4"),
    )


def holds(name):
    """
    Return whether the store holds the file named by the given hash.

    The store is asked, not the registry's records: a storage location may be
    registered before its file is uploaded. An object of 0 bytes under any key but
    the empty file's hash is what a failed upload leaves behind, not the file.
    """
    bucket = settings.BUCKETS["default"]
    try:
        head = _client().head_object(Bucket=bucket["bucket_name"], Key=name)
    except ClientError as error:
        if error.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
            return False
        raise
    return head["ContentLength"] > 0 or name == EMPTY_FILE_SHA1


def create_url(name, method, filename=None):
    bucket = settings.BUCKETS["default"]
    s3_client = _client()
    if method == "GET":
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket["bucket_name"],
                "Key": name,
                "ResponseContentDisposition": f"attachment; filename = {filename}",
            },
            ExpiresIn=bucket["duration"],
        )
    else:
        response = s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket["bucket_name"], "Key": name},
            ExpiresIn=bucket["duration"],
        )

    return response
