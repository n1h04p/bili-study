"""Private state. Windows credentials are bound to the current user by DPAPI."""
import ctypes
import json
import os
import uuid
from ctypes import wintypes
from pathlib import Path


def state_dir():
    root = Path(os.environ.get("BILI_STUDY_DATA", str(Path(os.environ.get("LOCALAPPDATA", Path.home())) / "BiliStudy")))
    root.mkdir(parents=True, exist_ok=True)
    return root


def atomic_write(path, data):
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with open(temp, "xb") as f:
            os.chmod(temp, 0o600)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _crypt(data, decrypt=False):
    if os.name != "nt":
        raise RuntimeError("This build requires Windows DPAPI")
    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    fn = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    fn.restype = wintypes.BOOL
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(target.data)


def save_private(name, value):
    atomic_write(state_dir() / name, _crypt(json.dumps(value).encode("utf-8")))


def load_private(name):
    p = state_dir() / name
    if not p.exists():
        return None
    return json.loads(_crypt(p.read_bytes(), decrypt=True))
