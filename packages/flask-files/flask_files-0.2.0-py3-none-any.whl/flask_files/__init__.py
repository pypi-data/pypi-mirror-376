from dataclasses import dataclass
import typing as t
from flask import send_from_directory, current_app
import fsspec
import os

from .file import File, generate_filename, file_size, save_uploaded_file_temporarly, format_file_size
from .form import validate_file, FileTooBigError, FileNotAllowedExtError


@dataclass
class FilesystemConfig:
    uuid_prefix: bool = True
    keep_filename: bool = True
    subfolders: bool = False
    uuid_prefix_path_separator: bool = False
    base_path : t.Optional[str] = None
    protocol: t.Optional[str] = None


@dataclass
class FilesState:
    upload_dir: str
    instance: "Files"
    filesystems: t.Mapping[str, FilesystemConfig]
    default_filesystem: str = "local"
    upload_url: t.Optional[str] = None


class Files:
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app, default_filesystem="local", upload_dir="uploads", upload_url="/uploads", uuid_prefix=True, keep_filename=True,
                 subfolders=False, uuid_prefix_path_separator=False, base_path=None, filesystems=None):
        
        self.app = app
        self.url_generators = {}
        self.state = state = FilesState(
            upload_dir=app.config.get("FILES_UPLOAD_DIR", upload_dir),
            upload_url=app.config.get("FILES_UPLOAD_URL", upload_url),
            default_filesystem=app.config.get("FILES_DEFAULT_FILESYSTEM", default_filesystem),
            filesystems={},
            instance=self
        )

        self.default_fs_config = {
            "uuid_prefix": app.config.get("FILES_UUID_PREFIXES", uuid_prefix),
            "keep_filename": app.config.get("FILES_KEEP_FILENAME", keep_filename),
            "subfolders": app.config.get("FILES_SUBFOLDERS", subfolders),
            "uuid_prefix_path_separator": app.config.get("FILES_UUID_PREFIX_PATH_SEPARATOR", uuid_prefix_path_separator),
            "base_path": app.config.get("FILES_BASE_PATH", base_path),
        }
        filesystems = app.config.get("FILES_FILESYSTEMS", filesystems or {})
        for name, config in filesystems.items():
            state.filesystems[name] = FilesystemConfig(**{**self.default_fs_config, **config})

        app.extensions["files"] = state
        app.jinja_env.globals["url_for_upload"] = url_for_upload

        if state.upload_dir:
            if not os.path.isabs(state.upload_dir):
                state.upload_dir = os.path.join(app.root_path, state.upload_dir)
            self.local_fs = fsspec.filesystem("dir", path=state.upload_dir, fs=fsspec.filesystem("local", auto_mkdir=True))

            if state.upload_url:
                def send_uploaded_file(filename):
                    return send_from_directory(state.upload_dir, filename)
                app.add_url_rule(f"{state.upload_url}/<path:filename>",
                                endpoint="static_upload",
                                view_func=send_uploaded_file)
            
    def filesystem(self, protocol=None, return_config=False):
        if not protocol:
            protocol = self.state.default_filesystem or "local"
        config = self.state.filesystems.get(protocol, FilesystemConfig(self.default_fs_config))
        protocol = config.protocol or protocol
        if protocol == "local":
            fs = self.local_fs
            os.makedirs(self.state.upload_dir, exist_ok=True)
        else:
            ignore_config_keys = [f.name for f in dataclass.fields(FilesystemConfig)]
            fs_kwargs = {k: v for k, v in config.items() if k not in ignore_config_keys}
            fs = fsspec.filesystem(protocol, **fs_kwargs)
        return (fs, config) if return_config else fs
    
    def register_url_generator(self, protocol, func):
        self.url_generators[protocol] = func

    def url_generator(self, protocol):
        def decorator(func):
            self.register_url_generator(protocol, func)
            return func
        return decorator


def save_file(file, name=None, protocol=None, uuid_prefix=None, **kwargs):
    state = current_app.extensions["files"]
    if not protocol:
        protocol = state.default_filesystem or "local"
    filesystem, config = state.instance.filesystem(protocol, return_config=True)

    if uuid_prefix is None:
        uuid_prefix = config.uuid_prefix
        
    path = generate_filename(file.filename, uuid_prefix=uuid_prefix, keep_filename=config.keep_filename,
                                    uuid_prefix_path_separator=config.uuid_prefix_path_separator,
                                    subfolders=config.subfolders, base_path=config.base_path)
    
    if uuid_prefix:
        path, uuid_prefix = path

    with filesystem.open(path, "wb", **kwargs) as f:
        file.save(f)

    return File(path, protocol, filename=name or file.filename,
                mimetype=file.mimetype, size=file_size(file), uuid=uuid_prefix)


def url_for_upload(file, **kwargs):
    if isinstance(file, str):
        file = File.from_uri(file)
    return file.url(**kwargs)
