# Publishing Guide for InvoiceAgent

This guide explains how to publish InvoiceAgent to PyPI (Python Package Index), making it available for installation using `pip install invoiceagent`.

## Prerequisites

1. A PyPI account. Register at [PyPI](https://pypi.org/account/register/)
2. A TestPyPI account (recommended). Register at [TestPyPI](https://test.pypi.org/account/register/)
3. Configured PyPI credentials using one of these methods:
   - Environment variables: `TWINE_USERNAME` and `TWINE_PASSWORD`
   - A `.pypirc` file in your home directory:
     ```
     [distutils]
     index-servers =
         pypi
         testpypi

     [pypi]
     username = your_username
     password = your_password

     [testpypi]
     repository = https://test.pypi.org/legacy/
     username = your_username
     password = your_password
     ```
   - Or using environment variables for each upload

## Automatic Publishing with GitHub Actions

The easiest way to publish is using GitHub Actions:

1. Add your PyPI credentials as secrets in your GitHub repository:
   - Go to your repository → Settings → Secrets → Actions
   - Add `PYPI_USERNAME` and `PYPI_PASSWORD` secrets

2. Create a new release:
   - Go to your repository → Releases → Create a new release
   - Add a tag (e.g., `v0.1.0`) matching the version in `pyproject.toml`
   - Publish the release

3. The GitHub Actions workflow will automatically build and publish the package

## Manual Publishing

If you prefer to publish manually, use the provided build script:

### Testing with TestPyPI

```bash
# Build and upload to TestPyPI
python build_package.py test
```

Once uploaded, test the installation:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ invoiceagent
```

### Publishing to PyPI

After testing on TestPyPI:

```bash
# Build and upload to PyPI
python build_package.py prod
```

## Version Updates

When releasing a new version:

1. Update the version number in:
   - `pyproject.toml`
   - `setup.py`
   - `invoiceagent/__init__.py`

2. Update the CHANGELOG.md file with the new version's changes

3. Commit changes and tag the release:
   ```bash
   git add .
   git commit -m "Bump version to X.Y.Z"
   git tag -a vX.Y.Z -m "Version X.Y.Z"
   git push origin main --tags
   ```

4. Create a new release on GitHub or publish manually as described above

## End User Installation

After publishing, users can install InvoiceAgent using:

```bash
pip install invoiceagent
```

## Troubleshooting

### Package Name Already Exists

If the name "invoiceagent" is already taken on PyPI, you'll need to choose a different name like:
- `invoice-agent`
- `invoiceagent-cli`
- `invoice-agent-tool`

Update the name in both `pyproject.toml` and `setup.py`, then update all import and usage documentation.

### Version Conflicts

If you've already published a version to PyPI, you cannot reuse that version or upload a package with the same version. Always increment the version number before uploading.

### Package Content Issues

If files are missing in the published package, review your `MANIFEST.in` file and ensure all needed files are included. Build the package locally and inspect it:

```bash
# After building
tar -tzf dist/*.tar.gz | less
```
