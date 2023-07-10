# Local registry

## Installation
To initialise a local registry, run the following command from your terminal:
```
/bin/bash -c "$(curl -fsSL https://data.fairdatapipeline.org/static/localregistry.sh)"
```
This will install the registry and all the related files will be stored in `~/.scrc`.

To run the server, run the `~/.fair/registry/scripts/start_fair_registry script. When the server is ready the following message will appear:
```
Local registry now accepting connections on http://localhost:8000
```

To stop the server, run the `~/.fair/registry/scripts/stop_fair_registry` script.

## Logging in
Go to http://localhost:8000/admin in your browser. Login with username `admin` and password `admin`. You can now click on **View site** to return to http://localhost:8000/.

After logging in you can go to http://localhost:8000/get-token to obtain an API access token.
