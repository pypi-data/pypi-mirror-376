
# Prepare your library
```toml
[build-system]
requires = ["setuptools>=64", "wheel", "setuptools_scm"]
build-backend = "setuptools.build_meta"

[project]
name = "LibraryName"
version = "0.0.1"
description = "Description of library"
authors = [
    { name = "John Doe", email = "example@example.com" }
]
dependencies = ["pydash"]
```

*Make sure:*
- `name` is unique on pypi
- `version` follows semantic versioning (0.0.1, 0.1.0, etc.).
- All dependencies are listed in `dependencies`.


# Install build tools

```bash
pip install --upgrade build twine
```

# Build the distribution

```bash
python -m build
```

**This will create:**
```
dist/
  LibraryName-0.0.1-py3-none-any.whl
  LibraryName-0.0.1.tar.gz
```

# Create a PyPI account
- Go to [account register](https://pypi.org/account/register/)
- **Also create an API token for uploading:**
  - [Create a token](https://pypi.org/manage/account/token/) `<YOUR_API_TOKEN>`
  - Click Add API token -> name it `LibraryName-upload`
  - Copy the token (you’ll use it in `twine`)

# Upload to PyPI

```bash
twine upload dist/* -u __token__ -p <YOUR_API_TOKEN>
```
- `-u __token__` -> tells Twine you’re using a token instead of a username/password.
- `<YOUR_API_TOKEN>` -> the token you created.

*use env var `$PYPI_TOKEN` like this*
```bash
twine upload dist/* -u __token__ -p $PYPI_TOKEN
```


## If you want to test first without publishing publicly, use Test PyPI:

```bash
twine upload --repository testpypi dist/* -u __token__ -p <YOUR_TEST_API_TOKEN>
```
- URL: https://test.pypi.org/
- Use `pip install --index-url https://test.pypi.org/simple/ LibraryName==0.0.1` to test.


# Install your library

in `requirements.txt` file add the line:
```txt
devworksdjangolib==0.0.1
```
then:
```bash
pip install -r requirements.txt
```




