import zipfile
from pathlib import Path

import pytest

from zippa.main import pack_items_with_chdir
from zippa.utils import read_zipignore


def _assert_zip_contents(zip_path, expected_files, excluded_files):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        file_list = zip_ref.namelist()

        assert all(
            expected_file in file_list for expected_file in expected_files
        ), f"Missing expected files: {[f for f in expected_files if f not in file_list]}"

        assert all(
            excluded_file not in file_list for excluded_file in excluded_files
        ), f"Unexpected files found: {[f for f in excluded_files if f in file_list]}"


@pytest.fixture
def test_files(tmp_path):
    (tmp_path / "lorem.md").write_text("Lorem ipsum dolor sit amet...")
    (tmp_path / "leo.md").write_text("Test content")
    (tmp_path / "dummy_dir").mkdir()
    (tmp_path / "dummy_dir" / "notes.txt").write_text("Test notes")
    # Add nested directory to test directory handling code path
    (tmp_path / "dummy_dir" / "subdir").mkdir()
    (tmp_path / "dummy_dir" / "subdir" / "nested_file.txt").write_text("nested content")
    return tmp_path


@pytest.mark.parametrize(
    "compress_level,include_dirs,expected_files,excluded_files",
    [
        (
            3,
            True,
            [
                "lorem.md",
                "leo.md",
                "dummy_dir/notes.txt",
                "dummy_dir/subdir/nested_file.txt",
                "dummy_dir/subdir/",
                "dummy_dir/",
            ],
            ["test_zippa.py", "__init__.py", "test_output.zip", "__pycache__"],
        ),
        (
            0,
            True,
            [
                "lorem.md",
                "leo.md",
                "dummy_dir/notes.txt",
                "dummy_dir/subdir/nested_file.txt",
                "dummy_dir/subdir/",
                "dummy_dir/",
            ],
            ["test_zippa.py", "__init__.py", "test_output.zip", "__pycache__"],
        ),
        (
            9,
            True,
            [
                "lorem.md",
                "leo.md",
                "dummy_dir/notes.txt",
                "dummy_dir/subdir/nested_file.txt",
                "dummy_dir/subdir/",
                "dummy_dir/",
            ],
            ["test_zippa.py", "__init__.py", "test_output.zip", "__pycache__"],
        ),
        (
            3,
            False,
            [
                "lorem.md",
                "leo.md",
                "dummy_dir/notes.txt",
                "dummy_dir/subdir/nested_file.txt",
            ],
            [
                "test_zippa.py",
                "__init__.py",
                "test_output.zip",
                "__pycache__",
                "dummy_dir/",
                "dummy_dir/subdir/",
            ],
        ),
    ],
    ids=[
        "Default compression with directories",
        "No compression with directories",
        "Maximum compression with directories",
        "Default compression without directories",
    ],
)
def test_pack_items_with_chdir(
    compress_level, include_dirs, expected_files, excluded_files, test_files
):
    """Test pack_items_with_chdir with different compression and directory options."""

    output_zip = test_files / f"test_output_{compress_level}_{include_dirs}.zip"

    zipignore_path = Path(__file__).parent.parent / ".zipignore"
    exclude_patterns = (
        read_zipignore(str(zipignore_path)) if zipignore_path.exists() else []
    )

    print(f"Exclude patterns: {exclude_patterns}")
    print(f"Zipignore path: {zipignore_path}")
    print(f"Zipignore exists: {zipignore_path.exists()}")

    list(
        pack_items_with_chdir(
            chdir_path=str(test_files),
            items=["lorem.md", "leo.md", "dummy_dir"],
            output_zip=str(output_zip),
            exclude_patterns=exclude_patterns,
            compress_level=compress_level,
            include_dirs=include_dirs,
        )
    )

    assert output_zip.exists()
    assert output_zip.stat().st_size > 0
    _assert_zip_contents(output_zip, expected_files, excluded_files)


@pytest.mark.parametrize(
    "output_location",
    [
        "backup1.zip",  # Same directory
        "subdir/backup2.zip",  # Subdirectory
        "../backup3.zip",  # Parent directory
    ],
)
def test_pack_to_various_output_locations(test_files, output_location):
    """Test packing to various output locations."""
    source_files = ["lorem.md", "leo.md"]

    # Create subdirectory if needed
    if "subdir" in output_location:
        (test_files / "subdir").mkdir(exist_ok=True)

    # For parent directory test, we need to work from a subdirectory
    if output_location.startswith("../"):
        work_dir = test_files / "work_subdir"
        work_dir.mkdir()
        chdir_path = str(work_dir)
        # Adjust source files to be relative to the work directory
        items = ["../lorem.md", "../leo.md"]
    else:
        chdir_path = str(test_files)
        items = source_files

    list(
        pack_items_with_chdir(
            chdir_path=chdir_path,
            items=items,
            output_zip=output_location,
            exclude_patterns=[],
            compress_level=3,
            include_dirs=False,
        )
    )

    # Verify zip was created in expected location
    if output_location.startswith("../"):
        expected_path = test_files / output_location[3:]  # Remove "../"
    else:
        expected_path = test_files / output_location

    assert expected_path.exists()
    assert expected_path.stat().st_size > 0

    # Verify contents
    expected_files = ["lorem.md", "leo.md"]
    _assert_zip_contents(expected_path, expected_files, [])


@pytest.mark.parametrize(
    "item_path,expected_files,expected_dirs",
    [
        # Test 1: Single file from external directory
        ("../external_dir/file1.txt", ["file1.txt"], []),
        # Test 2: Single directory from external directory
        ("../external_dir/subdir", ["subdir/file2.txt"], ["subdir/"]),
        # Test 3: File in subdirectory of external directory
        ("../external_dir/subdir/file2.txt", ["file2.txt"], []),
    ],
)
def test_compress_items_from_external_directory(
    test_files, tmp_path, item_path, expected_files, expected_dirs
):
    """Test compressing items from a directory outside of cwd."""
    # Create external directory structure
    external_dir = tmp_path / "external_dir"
    external_dir.mkdir()
    (external_dir / "file1.txt").write_text("External file content")

    subdir = external_dir / "subdir"
    subdir.mkdir()
    (subdir / "file2.txt").write_text("External subdir file content")

    # Create a working directory (different from external_dir)
    work_dir = test_files / "work_dir"
    work_dir.mkdir()

    output_zip = work_dir / "external_items.zip"

    list(
        pack_items_with_chdir(
            chdir_path=str(work_dir),  # Work from work_dir
            items=[item_path],  # But compress items from external_dir
            output_zip=str(output_zip),
            exclude_patterns=[],
            compress_level=3,
            include_dirs=True,
        )
    )

    assert output_zip.exists()
    assert output_zip.stat().st_size > 0

    # Combine expected files and directories
    all_expected = expected_files + expected_dirs
    _assert_zip_contents(output_zip, all_expected, [])


@pytest.mark.parametrize(
    "item_path,expected_files,expected_dirs",
    [
        # Test 1: Single file from external source to external output
        ("../source_dir/file1.txt", ["file1.txt"], []),
        # Test 2: Single directory from external source to external output
        ("../source_dir/subdir", ["subdir/file2.txt"], ["subdir/"]),
        # Test 3: File in subdirectory from external source to external output
        ("../source_dir/subdir/file2.txt", ["file2.txt"], []),
    ],
)
def test_compress_from_external_to_external_directory(
    test_files, tmp_path, item_path, expected_files, expected_dirs
):
    """Test compressing items from external directory to external output location."""
    # Create source directory structure (external to working directory)
    source_dir = tmp_path / "source_dir"
    source_dir.mkdir()
    (source_dir / "file1.txt").write_text("Source file content")

    subdir = source_dir / "subdir"
    subdir.mkdir()
    (subdir / "file2.txt").write_text("Source subdir file content")

    # Create output directory structure (external to working directory)
    output_dir = tmp_path / "output_dir"
    output_dir.mkdir()

    # Create a working directory (different from both source and output)
    work_dir = test_files / "work_dir"
    work_dir.mkdir()

    output_zip = output_dir / "compressed_items.zip"

    list(
        pack_items_with_chdir(
            chdir_path=str(work_dir),  # Work from work_dir
            items=[item_path],  # Compress items from source_dir
            output_zip=str(output_zip),  # Output to output_dir
            exclude_patterns=[],
            compress_level=3,
            include_dirs=True,
        )
    )

    assert output_zip.exists()
    assert output_zip.stat().st_size > 0

    # Combine expected files and directories
    all_expected = expected_files + expected_dirs
    _assert_zip_contents(output_zip, all_expected, [])
