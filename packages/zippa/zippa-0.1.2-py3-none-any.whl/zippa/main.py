# main.py
import fnmatch
from pathlib import Path
from typing import Iterator

from .utils import (
    WorkingDirectory,
    ZipArchiveManager,
)


def _iter_zip_items(path, exclude_patterns, include_dirs):
    base = path.name
    if path.is_file():
        yield ("file", path, base)
        return

    for item_type, item_path in _traverse_files_and_dirs(
        path, exclude_patterns, include_dirs
    ):
        rel_path = item_path.relative_to(path)
        arcname = f"{base}/{rel_path}"

        if item_type == "dir":
            yield ("dir", item_path, f"{arcname}/")
        else:
            yield ("file", item_path, arcname)


def _traverse_files_and_dirs(
    source_path: Path, exclude_patterns: list[str], include_dirs: bool = True
) -> Iterator[tuple[str, Path]]:
    if source_path.is_file():
        print(f"Processing file: {source_path}")
        yield ("file", source_path)
    elif source_path.is_dir():
        print(f"Processing subdirectory: {source_path}")
        # get all files for dir recursively
        for item in source_path.rglob("*"):
            # Calculate relative path for pattern matching
            relative_path = item.relative_to(source_path)

            if any(
                fnmatch.fnmatch(item.name, p) or fnmatch.fnmatch(str(relative_path), p)
                for p in exclude_patterns
            ):
                continue

            if item.is_dir():
                if include_dirs:
                    print(f"  Adding directory: {item}")
                    yield ("dir", item)
            else:
                print(f"  Adding file: {item}")
                yield ("file", item)


def _validate_path(path_str: str) -> Path | None:
    path = Path(path_str)

    if not path.exists():
        print(f"Warning: Path {path} not found, skipping")
        return None

    if not path.is_file() and not path.is_dir():
        print(f"Warning: '{path_str}' is neither a file nor a directory, skipping")
        return None

    return path


def pack_item(
    item_path: str,
    output_zip: str,
    exclude_patterns: list[str],
    compress_level: int,
    include_dirs: bool = True,
) -> Iterator[str]:
    validated_path = _validate_path(item_path)

    with ZipArchiveManager.for_compression(output_zip, compress_level) as archive:
        files_added = 0
        dirs_added = 0

        for item_type, item_path in _traverse_files_and_dirs(
            validated_path, exclude_patterns, include_dirs
        ):
            if item_type == "file":
                archive.write(item_path, arcname=item_path.relative_to(validated_path))
                files_added += 1
                yield f"Added file: {item_path.name}"
            elif item_type == "dir":
                dir_path = item_path.relative_to(validated_path)
                archive.writestr(f"{dir_path}/", "")
                dirs_added += 1
                yield f"Added directory: {item_path.name}"

        yield f"Completed: {files_added} files, {dirs_added} directories"


def pack_items_with_chdir(
    chdir_path: str,
    items: list[str],
    output_zip: str,
    exclude_patterns: list[str],
    compress_level: int,
    include_dirs: bool = True,
) -> Iterator[str]:
    yield f"Starting to pack {len(items)} items from {chdir_path}"

    with WorkingDirectory(chdir_path):
        with ZipArchiveManager.for_compression(output_zip, compress_level) as archive:
            files_added = dirs_added = 0

            for item_str in items:
                validated_path = _validate_path(item_str)
                if not validated_path:
                    continue

                yield f"Processing item: {item_str}"

                for item_type, item_path, arcname in _iter_zip_items(
                    validated_path, exclude_patterns, include_dirs
                ):
                    if item_type == "dir":
                        archive.writestr(arcname, "")
                        dirs_added += 1
                        yield f"Added directory: {item_path.name}"
                    else:
                        archive.write(item_path, arcname=arcname)
                        files_added += 1
                        yield f"Added file: {item_path.name}"

                # Add the root directory itself if include_dirs is True
                if include_dirs and validated_path.is_dir():
                    archive.writestr(f"{validated_path.name}/", "")
                    dirs_added += 1
                    yield f"Added root directory: {validated_path.name}"

            archive.printdir()
            print(
                f"Added {files_added} files and {dirs_added} directories to {output_zip}"
            )

            yield f"Completed: {files_added} files, {dirs_added} directories"


def extract_items(
    zip_file: str,
    target_path: str | None = None,
    item_name: str | None = None,
) -> None:
    if target_path is None:
        target_path = "."

    validated_target_path = _validate_path(target_path)

    with ZipArchiveManager.for_extraction(zip_file) as archive:
        if item_name is None:
            archive.extractall(validated_target_path)
            print(f"Extracted all items from {zip_file} to {validated_target_path}")
        else:
            archive.extract(item_name, validated_target_path)
            print(f"Extracted {item_name} from {zip_file} to {validated_target_path}")
