# xcube_jl_ext

[![Github Actions Status](https://github.com/dcs4cop/xcube-jl-ext/workflows/Build/badge.svg)](https://github.com/dcs4cop/xcube-jl-ext/actions/workflows/build.yml)
[xcube](https://github.com/dcs4cop/xcube) JupyterLab integration

This extension is composed of a Python package named `xcube_jl_ext`
for the JupyterLab server extension and a NPM package named `xcube-jl-ext`
for the JupyterLab frontend extension.

The extension adds the following features to JupyterLab:

1. Allows running a configurable xcube Viewer as widget in the JupyterLab.
2. Allows using xcube Server and Viewer from within Jupyter Notebooks, 
   even if JupyterLab is running remotely, i.e., spawned by JupyterHub.

---
**NOTE** 

This extension is still experimental and has neither been packaged 
nor deployed. Refer to the section **Development** below for dev installs.

---

## Requirements

- JupyterLab >= 3.0
- xcube >= 0.13

## Install

To install the extension, execute:

```bash
pip install xcube_jl_ext
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall xcube_jl_ext
```

## Troubleshoot

If you are seeing the frontend extension, but it is not working, check
that the server extension is enabled:

```bash
jupyter server extension list
```

If the server extension is installed and enabled, but you are not seeing
the frontend extension, check the frontend extension is installed:

```bash
jupyter labextension list
```

## Development

### Setup environment

Build [xcube Viewer](https://github.com/dcs4cop/xcube-viewer) resources
from sources. Note you'll need `yarn` to be installed on your system.

```bash
cd ${projects}
git clone https://github.com/dcs4cop/xcube-viewer.git
cd xcube-viewer
yarn install
yarn build
```

Now set environment variable `XCUBE_VIEWER_PATH` to point
to the xcube Viewer build directory:

```env
export XCUBE_VIEWER_PATH=${projects}/xcube-viewer/build
```

Make sure to have a source installation 
of [xcube](https://github.com/dcs4cop/xcube) in a
dedicated xcube Python environment. 

```bash
cd ${projects}
git clone https://github.com/dcs4cop/xcube.git
cd xcube
mamba env create
```

Activate `xcube` environment and install xcube in editable (development) mode:

```bash
conda activate xcube
pip install -ve .
```

Update environment with required packages for building and running
the JupyterLab extension.

Note, the version of the `jupyterlab` in our development environment 
should match the version of the target system. We also install
`jupyter-server-proxy`.

```bash
mamba install -c conda-forge -c nodefaults jupyterlab=3.4.0 jupyter-server-proxy
```

Also install some packaging and build tools:

```bash
mamba install -c conda-forge -c nodefaults nodejs jupyter-packaging
pip install build
```

Refer also to the [JupyterLab Extension Tutorial](https://jupyterlab.readthedocs.io/en/stable/extension/extension_tutorial.html)
for the use these tools.

### Install extension from sources

Make sure, `xcube` environment is active:

```bash
conda activate xcube
```

Clone xcube JupyterLab extension repository next to the `xcube` source
folder:

```bash
cd ${projects}
git clone https://github.com/dcs4cop/xcube-jl-ext.git
cd xcube-jl-ext
```

Install the initial project dependencies and install the extension into 
the JupyterLab environment. Copy the frontend part of the extension into 
JupyterLab. We can run this pip install command again every time we make 
a change to copy the change into JupyterLab.

```bash
pip install -ve .
```

Create a symbolic link from JupyterLab to our source directory. 
This means our changes are automatically available in JupyterLab:

```bash
jupyter labextension develop --overwrite .
```

If successful, we can run JupyterLab and check if the extension
works as expected:

```bash
jupyter lab
```

### Build after changes

Run the following to rebuild the extension. This will be required
after any changes of `package.json` or changes of frontend TypeScript 
files and other resources.

```bash
jlpm run build
```

If you wish to avoid building after each change, you can run the 

```bash
jlpm run watch
```

from your extension directory in another terminal. 
This will automatically compile the TypeScript files as they 
are changed and saved.

## Contributing

### Development install

Note: You will need NodeJS to build the extension package.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Change directory to the xcube_jl_ext directory
# Install package in development mode
pip install -e ".[test]"
# Link your development version of the extension with JupyterLab
jupyter labextension develop . --overwrite
# Server extension must be manually installed in develop mode
jupyter server extension enable xcube_jl_ext
# Rebuild extension Typescript source after making changes
jlpm build
```

You can watch the source directory and run JupyterLab at the same time in different terminals to watch for changes in the extension's source and automatically rebuild the extension.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
jlpm watch
# Run JupyterLab in another terminal
jupyter lab
```

With the watch command running, every saved change will immediately be built locally and available in your running JupyterLab. Refresh JupyterLab to load the change in your browser (you may need to wait several seconds for the extension to be rebuilt).

By default, the `jlpm build` command generates the source maps for this extension to make it easier to debug using the browser dev tools. To also generate source maps for the JupyterLab core extensions, you can run the following command:

```bash
jupyter lab build --minimize=False
```

### Development uninstall

```bash
# Server extension must be manually disabled in develop mode
jupyter server extension disable xcube_jl_ext
pip uninstall xcube_jl_ext
```

In development mode, you will also need to remove the symlink created by `jupyter labextension develop`
command. To find its location, you can run `jupyter labextension list` to figure out where the `labextensions`
folder is located. Then you can remove the symlink named `xcube-jl-ext` within that folder.

### Testing the extension

#### Server tests

This extension is using [Pytest](https://docs.pytest.org/) for Python code testing.

Install test dependencies (needed only once):

```sh
pip install -e ".[test]"
# Each time you install the Python package, you need to restore the front-end extension link
jupyter labextension develop . --overwrite
```

To execute them, run:

```sh
pytest -vv -r ap --cov xcube_jl_ext
```

#### Frontend tests

This extension is using [Jest](https://jestjs.io/) for JavaScript code testing.

To execute them, execute:

```sh
jlpm
jlpm test
```

#### Integration tests

This extension uses [Playwright](https://playwright.dev/docs/intro/) for the integration tests (aka user level tests).
More precisely, the JupyterLab helper [Galata](https://github.com/jupyterlab/jupyterlab/tree/master/galata) is used to handle testing the extension in JupyterLab.

More information are provided within the [ui-tests](./ui-tests/README.md) README.

### Packaging the extension

See [RELEASE](RELEASE.md)
