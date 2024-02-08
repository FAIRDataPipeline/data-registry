from hashlib import sha1
import hmac
import time

from django.conf import settings

def create_url(path, method, filename=None):
    bucket = settings.BUCKETS['default']
    expiry_time = int(time.time() + int(bucket['duration']))
    path = bucket['bucket_name'] + '/' + path
    if method == 'GET':
        hmac_body = '%s\n%s\n%s' % ('GET', expiry_time, path)
    elif method == 'PUT':
        hmac_body = '%s\n%s\n%s' % ('PUT', expiry_time, path)
    sig = hmac.new(bucket['secret_key'].encode('utf-8'), hmac_body.encode('utf-8'), sha1).hexdigest()
    url = '%s%s?temp_url_sig=%s&temp_url_expires=%d' % (bucket['url'], path, sig, expiry_time)
    if filename:
        url = '%s&filename=%s' % (url, filename)
    return url

def create_legacy_url(path, method, filename=None):
    bucket = settings.BUCKETS['default']
    expiry_time = int(time.time() + int(bucket['duration']))
    path = bucket['bucket_name'] + '/' + path
    if method == 'GET':
        hmac_body = '%s\n%s\n%s' % ('GET', expiry_time, path)
    elif method == 'PUT':
        hmac_body = '%s\n%s\n%s' % ('PUT', expiry_time, path)
    sig = hmac.new(bucket['secret_key'].encode('utf-8'), hmac_body.encode('utf-8'), sha1).hexdigest()
    url = '%s%s?temp_url_sig=%s&temp_url_expires=%d' % (bucket['url'], path, sig, expiry_time)
    if filename:
        url = '%s&filename=%s' % (url, filename)
    return url