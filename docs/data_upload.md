# How to upload data to the integrated object storage
There are two steps required to upload data. Firstly you need to request an upload URL. For example:
```
curl -i -X POST -H "Content-Type: application/json" \
     -H "Authorization: token <token>" \
     --data '{"checksum": "<checksum>"}' https://data.scrc.uk/api/data
```
where `<token>` should be replaced with a valid access token and `<checksum>` should be replaced by the SHA-1 checksum of the file you want to upload. The Linux command `sha1sum` can be used to calculate the SHA-1 checksum.

If there are no
existing registered files with the specified checksum you will get a 200 OK response with a JSON body containing a `url`, e.g.
```
{
  "url":"https://..."
}
```
If there is an existing file with the same checksum you will get a 409 CONFLICT response.

The URL can be used to upload the file with a HTTP PUT, e.g.:
```
curl -i --upload-file <filename> "<url>"
```
where `<filename>` should be replaced with the name of the file you want to upload and `<url>` should be replaced with the URL obtained in the previous step. The status code will be 201 if the file was uploaded successfully.
     
The `StorageLocation` should be created in the usual way, using https://data.scrc.uk/api/storage_root/4472/ as the `StorageRoot`, e.g. POST the following JSON to https://data.scrc.uk/api/storage_location/:
```
{
  "path": "<checksum>",
  "hash": "<checksum>",
  "storage_root": "https://data.scrc.uk/api/storage_root/4472/"
}
```
where for the checksum should be used for both the `path` and `hash`.

Next the `Object` can be created. When creating an `Object` you should specify a `FileType`, e.g. POST the following JSON to https://data.scrc.uk/api/object/:
```
{
  "description": "...",
  "storage_location": "https://data.scrc.uk/api/storage_location/<ID>/",
  "file_type": "https://data.scrc.uk/api/file_type/<ID>/"
}
```
Existing file types are listed here: https://data.scrc.uk/api/file_type/. New file types can be added by anyone if needed.

# How to download data
Firstly note that data can only be downloaded from the object store once the `StorageLocation` and `Object` have been created.

Files can be downloaded from `https://data.scrc.uk/data/<checksum>`. This will redirect directly to the object storage.

Aliases can also be used to download data. For data products use:
```
https://data.scrc.uk/data_product/<namespace>:<data product name>@<version>
```
and for external objects use:
```
https://data.scrc.uk/external_object/<doi_or_unique_name>:<title>@<version>
```
For external objects query parameters can be used to return different URLs:
* **source**: returns the `Source` associated with the external object
* **original**: returns the original store associated with the external object
* **root**: returns the `StorageRoot` only
