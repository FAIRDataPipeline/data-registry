from hashlib import sha1
import hmac
import time

from . import settings

def create_url(path, method, filename=None):
    expiry_time = int(time.time() + int(settings.CONFIG.get('storage', 'duration')))
    path = settings.CONFIG.get('storage', 'bucket') + '/' + path
    if method == 'GET':
        hmac_body = '%s\n%s\n%s' % ('GET', expiry_time, path)
    elif method == 'PUT':
        hmac_body = '%s\n%s\n%s' % ('PUT', expiry_time, path)
    sig = hmac.new(settings.CONFIG.get('storage', 'key').encode('utf-8'), hmac_body.encode('utf-8'), sha1).hexdigest()
    url = '%s%s?temp_url_sig=%s&temp_url_expires=%d' % (settings.CONFIG.get('storage', 'url'), path, sig, expiry_time)
    if filename:
        url = '%s&filename=%s' % (url, filename)
    return url
