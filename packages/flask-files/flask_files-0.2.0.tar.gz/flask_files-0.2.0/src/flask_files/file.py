from werkzeug.utils import secure_filename as wz_secure_filename, cached_property
from flask import current_app, url_for
from tempfile import NamedTemporaryFile, gettempdir
import os
import uuid
import mimetypes
import urllib.parse


class File:
    @classmethod
    def from_uri(cls, uri, default_protocol=None):
        protocol, path = split_uri(uri, default_protocol)
        filename = None
        if "#" in path:
            path, filename = path.rsplit("#", 1)
        params = {}
        if "?" in path:
            path, qs = path.split("?", 1)
            params = urllib.parse.parse_qs(qs, keep_blank_values=True, strict_parsing=True)
            if not filename and params.get("filename"):
                filename = params.pop("filename")
        return cls(path, protocol, filename, params.get("mimetype"), params.get("size"), params.get("uuid"))
    
    @classmethod
    def from_json(cls, data, default_protocol=None):
        protocol, path = split_uri(data["uri"], default_protocol)
        return cls(path, protocol, data.get("filename"), data.get("mimetype"), data.get("size"), data.get("uuid"))

    def __init__(self, path, protocol=None, filename=None, mimetype=None, size=None, uuid=None):
        self.path = path
        self.protocol = protocol
        self.filename = os.path.basename(path) if not filename else filename
        self.uuid = uuid
        if mimetype:
            self.__dict__['mimetype'] = mimetype
        if size is not None:
            self.__dict__['size'] = size

    @property
    def filesystem(self):
        return current_app.extensions["files"].instance.filesystem(self.protocol)
    
    @cached_property
    def mimetype(self):
        return mimetypes.guess_type(self.filename)[0]

    @cached_property
    def size(self):
        return self.filesystem.du(self.path)
    
    def open(self, mode="rb"):
        return self.filesystem.open(self.path, mode)
    
    def save(self, fp):
        with self.open() as f:
            fp.write(f.read())
    
    def to_json(self, read_size=False):
        o = {
            "filename": self.filename,
            "uri": self.uri,
            "mimetype": self.mimetype
        }
        if self._size is not None:
            o["size"] = self._size
        elif read_size:
            o["size"] = self.size
        if self.uuid:
            o["uuid"] = self.uuid
        return o
    
    def to_uri(self, with_qs=True, read_size=False):
        params = self.to_json(read_size)
        uri = params.pop("uri")
        filename = params.pop("filename")
        if with_qs:
            qs = urllib.parse.urlencode({k: v for k, v in params.items() if v})
            if qs:
                uri += f"?{qs}"
        return f"{uri}#{filename}"
    
    @property
    def uri(self):
        return f"{self.protocol}://{self.path}" if self.protocol else self.path
    
    def url(self, **kwargs):
        state = current_app.extensions["files"]
        if self.protocol in state.instance.url_generators:
            return state.url_generators[self.protocol](self, **kwargs)
        if hasattr(self.filesystem, "url"):
            return self.filesystem.url(self.path, **kwargs)
        if state.upload_url:
            return url_for("static_upload", filename=self.path, **kwargs)
        return self.path
    
    def __str__(self):
        return self.url()
    
    def __repr__(self):
        return self.to_uri()
    
    def __getstate__(self):
        return {
            "path": self.path,
            "protocol": self.protocol,
            "filename": self.filename,
            "uuid": self.uuid,
            "mimetype": self.__dict__.get("mimetype"),
            "size": self.__dict__.get("size")
        }


def generate_filename(filename, uuid_prefix=False, uuid_prefix_path_separator=False, keep_filename=True,
                      subfolders=False, base_path=None, secure_filename=True, protocol=None):
    if uuid_prefix is True:
        uuid_prefix = str(uuid.uuid4())
    if uuid_prefix and not keep_filename:
        _, ext = os.path.splitext(filename)
        filename = str(uuid_prefix) + ext
    else:
        if secure_filename:
            filename = wz_secure_filename(filename)
        if uuid_prefix:
            filename = str(uuid_prefix) + ("/" if uuid_prefix_path_separator else "-") + filename

    if subfolders:
        if uuid_prefix:
            parts = filename.split("-", 4)
            filename = os.path.join(os.path.join(*parts[:4]), filename)
        else:
            filename = os.path.join(os.path.join(*filename[:4]), filename)

    if base_path:
        filename = f"{base_path.rtrim('/')}/{filename}"

    if protocol:
        filename = f"{protocol}://{filename}"

    if uuid_prefix:
        return filename, uuid_prefix
    return filename


def save_uploaded_file_temporarly(file, filename=None, tmp_dir=None):
    if not tmp_dir:
        tmp_dir = current_app.config.get('FILES_UPLOAD_TMP_DIR')
    if filename:
        tmpfilename = os.path.join(tmp_dir or gettempdir(), wz_secure_filename(filename))
    else:
        _, ext = os.path.splitext(file.filename)
        tmp = NamedTemporaryFile(delete=False, suffix=ext, dir=tmp_dir)
        tmp.close()
        tmpfilename = tmp.name
    file.save(tmpfilename)
    return tmpfilename


def file_size(file):
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size


def format_file_size(size, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(size) < 1024.0:
            return "%3.1f%s%s" % (size, unit, suffix)
        size /= 1024.0
    return "%.1f%s%s" % (size, 'Y', suffix)


def split_uri(uri, default_protocol=None):
    if "://" in uri:
        return uri.split("://", 1)
    return default_protocol, uri