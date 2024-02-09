import boto3

from django.conf import settings

def create_url(name, method, filename = None):
    bucket = settings.BUCKETS['default']
    session = boto3.session.Session()
    s3_client = session.client(
        service_name= 's3',
        aws_access_key_id= bucket['access_key'],
        aws_secret_access_key= bucket['secret_key'],
        endpoint_url= bucket['url'],
    )
    if method == "GET":
        response = s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': bucket['bucket_name'],
                                                                'Key': name,
                                                                'ResponseContentDisposition': f'attachment; filename = {filename}',},
                                                        ExpiresIn=bucket['duration'])
    else:
        response = s3_client.generate_presigned_url('put_object',
                                                        Params={'Bucket': bucket['bucket_name'],
                                                                'Key': name},
                                                        ExpiresIn=bucket['duration'])
    
    return response