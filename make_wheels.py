# /// script
# requires-python = "~=3.10"
# dependencies = [
#   "wheel~=0.45.1",
# ]
# ///

import io
import os
from typing import Any, Generator
import urllib.request
import hashlib
import tarfile
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from wheel.wheelfile import WheelFile  # type: ignore
from email.message import EmailMessage


X13_VERSION = "v1-1-b61"
X13_PYTHON_PLATFORMS = {
    "windows": "win_amd64",
    "unix-linux": "manylinux_2_12_x86_64.manylinux2010_x86_64",
}


class ReproducibleWheelFile(WheelFile):
    def writestr(self, zinfo_or_arcname: str, data: bytes, *args, **kwargs):  # type: ignore
        if isinstance(zinfo_or_arcname, ZipInfo):
            zinfo = zinfo_or_arcname
        else:
            assert isinstance(zinfo_or_arcname, str)
            zinfo = ZipInfo(zinfo_or_arcname)
            zinfo.file_size = len(data)
            zinfo.external_attr = 0o0644 << 16
            if zinfo_or_arcname.endswith(".dist-info/RECORD"):
                zinfo.external_attr = 0o0664 << 16

        zinfo.compress_type = ZIP_DEFLATED
        zinfo.date_time = (1980, 1, 1, 0, 0, 0)
        zinfo.create_system = 3
        super().writestr(zinfo, data, *args, **kwargs)  # type: ignore


def make_message(
    headers: list[tuple[str, str]], payload: bytes | None = None
) -> EmailMessage:
    msg = EmailMessage()
    for name, value in headers:
        if isinstance(value, list):
            for value_part in value:
                msg[name] = value_part
        else:
            msg[name] = value
    if payload:
        msg.set_payload(payload)
    return msg


def write_wheel_file(
    filename: str, contents: dict[str | ZipInfo, str | bytes | EmailMessage]
) -> str:
    with ReproducibleWheelFile(filename, "w") as wheel:
        for member_info, member_source in contents.items():
            wheel.writestr(member_info, bytes(member_source))  # type: ignore
    return filename


def write_wheel(
    outdir: str,
    *,
    name: str,
    version: str,
    tag: str,
    metadata: list[tuple[str, str]],
    description: bytes,
    contents: dict[str | ZipInfo, str | bytes],
) -> str:
    wheel_name = f"{name}-{version}-{tag}.whl"
    dist_info = f"{name}-{version}.dist-info"
    return write_wheel_file(
        os.path.join(outdir, wheel_name),
        {
            **contents,
            f"{dist_info}/METADATA": make_message(
                [
                    ("Metadata-Version", "2.4"),
                    ("Name", name),
                    ("Version", version),
                    *metadata,
                ],
                description,
            ),
            f"{dist_info}/WHEEL": make_message(
                [
                    ("Wheel-Version", "1.0"),
                    ("Generator", "x13binary make_wheels.py"),
                    ("Root-Is-Purelib", "false"),
                    ("Tag", tag),
                ]
            ),
        },
    )


def iter_archive_contents(
    archive: Any,  # type: ignore
) -> Generator[tuple[str, int, bytes], Any, None]:
    magic = archive[:4]
    if magic[:2] == b"\x1f\x8b":
        with tarfile.open(mode="r|gz", fileobj=io.BytesIO(archive)) as tar:
            for entry in tar:
                if entry.isreg():
                    yield (
                        entry.name,
                        entry.mode | (1 << 15),
                        tar.extractfile(entry).read(),  # type: ignore
                    )
    elif magic[:4] == b"PK\x03\x04":
        with ZipFile(io.BytesIO(archive)) as zip_file:
            for entry in zip_file.infolist():
                if not entry.is_dir():
                    yield (
                        entry.filename,
                        entry.external_attr >> 16,
                        zip_file.read(entry),
                    )
    else:
        raise RuntimeError("Unsupported archive format")


def fix_x13_version(version: str) -> str:
    """v1-1-b61 -> v1.1.61"""
    return version.replace("-", ".").replace("b", "")


def write_x13_wheel(
    outdir: str = "dist",
    *,
    version: str,
    platform: str,
    archive: Any,  # type: ignore
):
    contents: dict[str | ZipInfo, str | bytes] = {}
    with open(Path("src") / "x13binary" / "__init__.py", "r") as file:
        contents["x13binary/__init__.py"] = file.read().encode()
    with open(Path("src") / "x13binary" / "__main__.py", "r") as file:
        contents["x13binary/__main__.py"] = file.read().encode()

    dist_info = f"x13binary-{version}.dist-info"
    data = f"x13binary-{version}.data"

    with open(Path("LICENSE"), "r", encoding="utf8") as file:
        contents[f"{dist_info}/licenses/x13binary/LICENSE"] = file.read().encode()

    with open(Path("README.pypi.md"), "r", encoding="utf8") as f:
        description = f.read().encode()

    for entry_name, entry_mode, entry_data in iter_archive_contents(archive):
        entry_name = "/".join(entry_name.split("/")[1:])
        if not entry_name:
            continue
        if entry_name.startswith("docs/") or entry_name.endswith(".spc"):
            continue
        if entry_name.startswith("x13as_html"):
            zip_info = ZipInfo(f"{data}/scripts/{entry_name}")
            zip_info.external_attr = (entry_mode & 0xFFFF) << 16
            contents[zip_info] = entry_data

    return write_wheel(
        outdir,
        name="x13binary",
        version=version,
        tag=f"py3-none-{platform}",
        metadata=[
            ("Summary", "X13-ARIMA-SEATS installable binary through Python."),
            ("Description-Content-Type", "text/markdown"),
            ("License-Expression", "MIT"),
            ("License-File", "x13binary/LICENSE"),
            ("Classifier", "Development Status :: 4 - Beta"),
            ("Classifier", "Intended Audience :: Developers"),
            ("Classifier", "Programming Language :: Fortran"),
            ("Classifier", "Topic :: Scientific/Engineering :: Mathematics"),
            ("Classifier", "Topic :: Software Development :: Build Tools"),
            (
                "Project-URL",
                "Homepage, https://www.census.gov/data/software/x13as.X-13ARIMA-SEATS.html",
            ),
            (
                "Project-URL",
                "Source Code, https://github.com/bryceclaughton/x13binary-pypi",
            ),
            (
                "Project-URL",
                "Bug Tracker, https://github.com/bryceclaughton/x13binary-pypi/issues",
            ),
            ("Requires-Python", "~=3.5"),
        ],
        description=description,
        contents=contents,
    )


def fetch_and_write_x13binary_wheels(
    x13_version: str,
    outdir: str = "dist",
):
    Path(outdir).mkdir(exist_ok=True)
    for x13_platform, python_platform in X13_PYTHON_PLATFORMS.items():
        x13_url = (
            f"https://www2.census.gov/software/x-13arima-seats/x13as/{x13_platform}/program-archives/x13as_html-{x13_version}"
            + (".zip" if x13_platform.startswith("windows") else ".tar.gz")
        )
        with urllib.request.urlopen(x13_url) as request:
            x13_archive = request.read()
            print(f"{hashlib.sha256(x13_archive).hexdigest()} {x13_url}")

        wheel_path = write_x13_wheel(
            outdir,
            version=fix_x13_version(x13_version),
            platform=python_platform,
            archive=x13_archive,
        )
        with open(wheel_path, "rb") as wheel:
            print(f"  {hashlib.sha256(wheel.read()).hexdigest()} {wheel_path}")


if __name__ == "__main__":
    fetch_and_write_x13binary_wheels(X13_VERSION)
