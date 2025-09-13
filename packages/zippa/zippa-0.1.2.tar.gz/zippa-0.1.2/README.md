<h1 align="center">Automate dir zipping⚡️</h1>
<p align="center">Project Description</p>
        CLI for flexibly zipping items.

## Features
* compress files and dirs as required
    - run command for zipping dirs/files of choice
    - run command for defining where compressed files should live

## Prerequisites
* Python 3.12+
* Git
* uv (recommended) or pip

## Usage
### Command Line Interface

#### Case 1: Compress items from current working directory (cwd)

```bash
# Basic compression in cwd
$ uv run zippa pack foo.txt bar.py
$ uv run zippa pack foo.txt dir1/ bar.py
$ uv run zippa pack .

# Specify output location (can be anywhere)
$ uv run zippa pack . --output /path/to/backup.zip
$ uv run zippa pack *.py --output ../python_files.zip
$ uv run zippa pack . --output ~/backups/project.zip
```

#### Case 2: Compress items from external directory, output in that directory

```bash
# Compress everything in external directory, output there
$ uv run zippa pack . --chdir ~/path/to/dir --output backup.zip

# Compress specific files in external directory, output there
$ uv run zippa pack file1.txt file2.py --chdir ~/path/to/dir --output backup.zip
```

#### Case 3: Compress items from external directory, output in different directory

```bash
# Compress everything in external directory, output elsewhere
$ uv run zippa pack . --chdir ~/path/to/source --output ~/path/to/output/backup.zip

# Compress specific files in external directory, output elsewhere
$ uv run zippa pack file1.txt file2.py --chdir ~/path/to/source --output ~/path/to/output/backup.zip
```

#### Exclude Patterns

```bash
# Exclude specific patterns via command line
$ uv run zippa pack . --exclude "*.pyc" --exclude "__pycache__" --exclude "*.log"

# Use custom .zipignore file
$ uv run zippa pack . --exclude-file .myignore

# Combine .zipignore with additional exclusions
$ uv run zippa pack . --exclude-file .zipignore --exclude "*.tmp"

# Exclude patterns with external directory
$ uv run zippa pack . --chdir ~/path/to/project --exclude "*.pyc" --exclude "__pycache__"
```

#### .zipignore File

Create a `.zipignore` file in your project root to define default exclusions:

```bash
# .zipignore example
*.pyc
__pycache__/
*.log
*.tmp
.git/
node_modules/
.env
*.DS_Store
build/
dist/
*.egg-info/
```

#### Additional Options

```bash
# Verbose output
$ uv run zippa pack . --output backup.zip --verbose

# Custom compression level
$ uv run zippa pack . --compress-level 6 --output backup.zip

# Show help
$ uv run zippa --help
$ uv run zippa pack --help
```

#### Important Notes

- **Case 1**: Items are relative to your current working directory
- **Case 2 & 3**: Items are relative to the directory specified by `--chdir`
- **Output location**: Can be anywhere (absolute or relative path)
- **Current limitation**: `--chdir` must come after the items to compress


## Future Updates
* [ ] make syntax for running commands more intuitive
* [ ] implement extraction of compressed items
* [ ] implement compression summary after each compression
* [ ] listen to events and compress correspondently


## Author

**Carlos Pumar-Frohberg**

* [Profile](https://github.com/cpumarfrohberg)
* [Email](mailto:cpumarfrohberg@gmail.com?subject=Hi "Hi!")


## 🤝 Support

Comments, questions and/or feedback are welcome!
