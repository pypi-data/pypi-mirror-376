# cli.py
import typer

from .main import extract_items, pack_items_with_chdir
from .utils import read_zipignore

VERBOSE_OPTION = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
DEFAULT_ZIP_NAME = "output.zip"

app = typer.Typer()


@app.command()
def pack(
    items: list[str] = typer.Argument(..., help="Files or directories to zip"),
    output: str = typer.Option(
        DEFAULT_ZIP_NAME, "--output", "-o", help="Output zip file"
    ),
    chdir_path: str | None = typer.Option(
        None, "--chdir", "-d", help="Directory to work from"
    ),
    exclude: list[str] = typer.Option(
        [], "--exclude", "-x", help="Additional file patterns to exclude"
    ),
    exclude_file: str = typer.Option(
        ".zipignore", "--exclude-file", help="Path to .zipignore file"
    ),
    compress_level: int = typer.Option(
        3, "--compress-level", "-c", help="Compression level (0-9)", min=0, max=9
    ),
    verbose: bool = VERBOSE_OPTION,
):
    """Zip directories and files with exclusion support"""

    if verbose:
        typer.echo("Warning: Using verbose mode.")
        if chdir_path:
            typer.echo(f"Would work from: {chdir_path}")

    zipignore_patterns = read_zipignore(exclude_file)

    # Combine with command-line exclusions
    all_exclude_patterns = zipignore_patterns + exclude

    # Use pack_items_with_chdir for all cases (current dir or specific dir)
    chdir_path = chdir_path or "."  # Default to current directory

    if verbose:
        if chdir_path == ".":
            typer.echo("Working from current directory")
        else:
            typer.echo(f"Changing to directory: {chdir_path}")

    # Consume the generator to execute the packing
    for message in pack_items_with_chdir(
        chdir_path,
        items,
        output,
        all_exclude_patterns,
        compress_level,
    ):
        if verbose:
            typer.echo(f"  {message}")


@app.command()
def extract(
    source: str = typer.Argument(..., help="Zip file to extract"),
    output: str = typer.Option(None, "--output", "-o", help="Output directory"),
    item_name: str = typer.Option(
        None, "--item-name", "-i", help="Item name to extract"
    ),
    verbose: bool = VERBOSE_OPTION,
):
    """Extract items from a zip file"""

    if verbose:
        typer.echo("Warning: Both --verbose and --quiet specified. Using verbose mode.")

    extract_items(
        zip_file=source,
        target_path=output,
        item_name=item_name,
    )


@app.command()
def list(
    source: str = typer.Argument(..., help="Zip file to list contents"),
    verbose: bool = VERBOSE_OPTION,
):
    """List contents of a zip file"""

    if verbose:
        typer.echo(f"Listing contents of {source}")

    # TODO: Implement list functionality using ZipArchiveManager
    # This would show the contents without extracting
    typer.echo(f"Contents of {source}:")
    typer.echo("(List functionality not yet implemented)")


if __name__ == "__main__":
    app()
