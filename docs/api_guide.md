## API Usage Guide

Programmatic access to the data registry is available via a RESTful API.
This allows access using standard HTML requests (GET, POST, etc.).

Non-authorised users can perform GET requests on all tables (except Users and Groups).
In order to GET Users and Groups and to perform POST requests on the other tables you
will need to authenticate using a Token (see below).

### Authentication Tokens

Once you have created an account on the website, using GitHub based authentication,
you can generate an API token using the link available in the `Links` dropdown at
the top of the webpages.

You only ever have one token per user account and you cannot request your current token
detail so if you lose your token you will need to generate a new one. If you no longer 
require your token you can revoke it using the link in the `Links` dropdown.

### API details

**GET Requests**

All endpoints accept GET requests. Apart from `users/` and `groups/` these can
be accessed without authentications.

Requesting an object endpoint will return all
the available objects of that type (e.g. `code_run/` will return all code runs).
Appending an id integer to an API path with return the object for that particular
id (e.g. `code_run/25/` will return the code run with id=25).

GET requests also accept filter arguments when not requesting an individual object
(e.g. `data_product/?name=fixed-parameters/*` will return all the data products with
name starting with `fixed-parameters/`).  The query arguments that can be used can be
seen by clicking on the filters button on the web-page for the API endpoint.

**OPTIONS requests**

All endpoints accept OPTIONS requests. If you make an OPTIONS request without
authentication you will not receive the `actions` element which details the fields
for the POST request.

**POST Requests**

All endpoints (except `users/` and `groups/`) accept POST requests. These requests
require authentication. To see what data needs to be sent with the POST request you can
either view the form on the web-page for the endpoint (when logged in) or see the fields
returned in the `actions` elemenet of the metadata returned from an OPTIONS request to
the endpoint. 

### Example Requests

Below we show some examples of interacting with the API. The examples are in Python
using the `requests` library but any language and library can be used that is able to make HTML
requests.

**Getting a list of objects**

```python
import requests
r = requests.get('https://data.fairdatapipeline.org/api/object/')

# 200 is successful request
assert(r.status_code == 200)

# The returned data is in JSON format
data = r.json()

# The data is paginated, with the total number of objects given in count
print(data["count"])

# The next page can be obtained by using the link give in next
if data["next"]:
    r = requests.get(data["next"])

# The returned objects are given in results
objects = data["results"]

# Objects are returned a list of dictionaries
print(objects[0]["url"])
print(objects[0]["description"])
```

**Getting an individual object**

```python
import requests
r = requests.get('https://data.fairdatapipeline.org/api/object/31946/')

# 200 is successful request
assert(r.status_code == 200)

# The returned data is in JSON format
data = r.json()

# The returned JSON is a dictionary of the object requested
print(data.keys())
print(data["description"])
```

**Querying an API endpoint**

```python
import requests

# To get full options we need to authenticate.
# This is done by sending our API token in the request header (<TOKEN> should be repleaced
# with the API token generated from the web page).
headers = {
    'Authorization': 'token <TOKEN>'
}
r = requests.options('https://data.fairdatapipeline.org/api/object/31946/', headers=headers)

# 200 is successful request
assert(r.status_code == 200)

# The returned data is in JSON format
data = r.json()

# Documentation for the endpoint is given in the description element:
print(data['description'])

# Details about how to construct a POST request is given in the actions element.
for el in data['actions']['POST'].items():
    # Each element has the name of the field and details about its type, whether
    # it is required, etc.
    print(el)
```

**Putting an object**

```python
import requests

# To PUT and object you need to be authenticated.
# This is done by sending our API token in the request header (<TOKEN> should be repleaced
# with the API token generated from the web page).
headers = {
    'Authorization': 'token <TOKEN>'
}

# You also need a dictionary of the data you want to put. To see what needs to go into this
# dictionary you can visit the API endpoint web-page by viewing the API endpoint in a browser
# or query the API endpoint using an OPTIONS request (see above).
data = {
    "path": "path/to/file",
    "hash": "dae8dd8b2837e2f33979da109109244f0f9e273f",
    "storage_root": "https://data.fairdatapipeline.org/api/storage_root/1/"
}
r = requests.put('https://data.fairdatapipeline.org/api/object/31946/', data, headers=headers)

# 201 is successful create
assert(r.status_code == 201)

# You will also receive back the object you just created, like if you had done a GET for
# an individual object (see above)
data = r.json()
# The url entry contains the url of the new object
print(data['url'])
```