# Flask-Files

Uploaded files management based on [fsspec](https://filesystem-spec.readthedocs.io/en/latest/).

## Installation

    pip install flask-files

## Store uploaded files

Use `save_file()` to store a Flask file object from `request.files`. This function returns a [`File` object](#file-object).
Store the value of the `File.uri` property to later access the file.

```python
from flask import Flask
from flask_files import Files, save_file

app = Flask(__name__)
Files(app)

@app.post("/")
def index():
    file = save_file(request.files["file"])
    print(file.uri)
```

By default, files are saved to disk prefixed with a UUID.

## Validate files from forms

You should validate uploaded files using `validate_file()`. It will raised a `BadRequest` error on validation failure.

```python
from flask_files import validate_file

@app.post("/")
def index():
    validate_file(request.files["file"], allowed_exts=[".pdf"], max_size=1024**10)
```

Use the `flask_files.images.IMAGE_EXTS` constant for a list of common image extensions.

## Serve uploaded files

Use `url_for_upload()` in combination with the URI stored after saving the file to obtain a public URL for your file.

```html
<img src="{{ url_for_upload(file_or_uri) }}">
```

You can also re-build a `File` object from a URI using `File.from_uri(uri)`.

## Storage file systems

Flask-Files is built on top of fsspec, allowing it to use any fssspec file system. Compatible file systems must allow write operations.

File systems can allow custom url generation if they provide a `url()` method (like s3fs).

The default backend can be modified using the `FILES_DEFAULT_FILESYSTEM` option.

Multiple backends can be used at once by providing the protocol parameter to `save_file()`.

Per filesystem options can be provided in the configuration

```py
FILES_FILESYSTEMS={
    "local": {
        "subfolders": True
    },
    "s3": {
        "endpoint_url": "https://alternative-service.com"
    }
}
```

You can also use the same filesystem multiple times with different configurations:

```py
FILES_FILESYSTEMS={
    "bucket1": {
        "protocol": "s3",
        "base_path": "bucket1"
    },
    "bucket2": {
        "protocol": "s3",
        "base_path": "bucket2"
    }
}

save_file(file, protocol="bucket1")
save_file(file, protocol="bucket2")
```

## Using S3

To store files on S3 (or compatible services), setup your AWS credentials as env variables and configure your app as follow:

```
FILES_DEFAULT_FILESYSTEM="s3"
FILES_BASE_PATH="bucket_name"
```

## Manipulate images

Flask-Files provides functions to manipulate images. They can be chained. The returned image must be stored using `save_file()`.


| Function | Description |
| --- | --- |
| `resize_img(file, width, height)` | Resize an image (only one of width of height is mandatory, ratio is maintained) |
| `create_thumbnail(file, width, height)` | Create a thumbnail (only one of width of height is mandatory, ratio is maintained) |
| `watermark_img(file, watermark_path, x, y)` | Add a watermark to an image (x, y are optional, default to lower right corner) |

```python
from flask_files.images import IMAGE_EXTS, create_thumbnail

@app.post("/")
def index():
    validate_file(request.files["file"], IMAGE_EXTS)
    file = save_file(request.files["file"])
    thumb = save_file(create_thumbail(file, 100))
```

## File object

The file object is a serializable object that holds information about a file.

It is serializable as string (uri) or JSON.

The stringified representation of a file object is its URL.

| Object attribute | Description |
| --- | --- |
| path | The path on the storage |
| filename | The filename as it was uploaded |
| mimetype | Mimetype |
| uuid | When using uuid prefixes, the uuid prefix |
| size | File size in bytes |
| url() | Generate a url for the file |
| full_uri() | Serialize the object as an URI |
| to_json() | Serializa the object as JSON |
| open() | Open as a file-like object |

## Configuration

| Config Key | Extension argument | Description | Default |
| --- | --- | --- | --- |
| FILES_UPLOAD_DIR | upload_dir | Where uploaded files are stored on disk | uploads |
| FILES_UPLOAD_URL | upload_url | URL from while uploaded files are served | /uploads |
| FILES_DEFAULT_FILESYSTEM | default_filesystem | Default fsspec file system to use | None (local disk) |
| FILES_FILESYSTEMS | filesystems | A dict with options for different filesystems | |

Configuration for file systems:

| As default value from app config | Key in filesystem config | Description | Default |
| --- | --- | --- | --- |
| FILES_UUID_PREFIXES | uuid_prefixes | Whether to prefix filenames with UUIDs | True |
| FILES_KEEP_FILENAME | keep_filename | Whether to keep the original filename | True |
| FILES_SUBFOLDERS | subfolders | Whether to split the first 4 letters are subdirectories | False |
| FILES_UUID_PREFIX_PATH_SEPARATOR | uuid_prefix_path_separator | Whether to use the UUID prefix as a folder instead of filename prefix | False |
| FILES_BASE_PATH | base_path | Base path for uploaded files, relative to the upload root | |
