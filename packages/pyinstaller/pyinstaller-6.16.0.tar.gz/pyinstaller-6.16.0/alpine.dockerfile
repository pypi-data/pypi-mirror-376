# Setup an Alpine test environment with Python, PyInstaller and its test dependencies.
#
# To build, boot into and invoke pytest inside this image run:
#
#   docker build -f alpine.dockerfile -t some-arbitrary-name .
#   docker run -it some-arbitrary-name
#   pytest
#
# Or if you prefer a one-liner:
#
#   docker run -it $(docker build -q -f alpine.dockerfile .) pytest
#
# This docker file should be used for testing only. The bootloaders it compiles internally are not suitable for PyPI.
#
# ---
# This dockerfile is 2-part. The first half builds and the second tests. The test half should only contain PyInstaller's
# runtime and test dependencies - no C compiler or dev packages. Once other packages start shipping musl compatible
# wheels, most or possibly all of the build half will be safely removable.

FROM python:alpine AS wheel-factory

# Install a C compiler.
RUN apk add musl-dev gcc
# With zlib headers to compiler the bootloader,
RUN apk add zlib-dev
# Linux headers to build psutil from source.
RUN apk add linux-headers

# Build/download wheels for all test requirements.
RUN mkdir -p /io/tests
WORKDIR /io
COPY tests/requirements-base.txt tests/
COPY tests/requirements-tools.txt tests/
RUN pip wheel -r tests/requirements-tools.txt -w wheels

# Recent versions of python docker image do not provide setuptools and wheel with python (>= 3.12) by default.
# See: https://github.com/docker-library/python/issues/952
RUN pip install --upgrade hatchling

# Build a wheel for PyInstaller. Do this last and use as few files as possible to maximize cache-ability.
COPY COPYING.txt .
COPY README.rst .
COPY hatch_build.py .
COPY pyproject.toml .
COPY bootloader bootloader
COPY PyInstaller PyInstaller
RUN pip wheel --no-build-isolation --no-dependencies --wheel-dir=wheels .


FROM python:alpine

CMD ash
WORKDIR /io

# Runtime libraries required by lxml.
RUN apk add libxml2 libxslt
# Required by tkinter.
RUN apk add tk
# Used as a test library for some ctypes finding tests.
RUN apk add libpng
# And by PyInstaller itself.
RUN apk add binutils

COPY pyproject.toml pytest.ini .

# Import and the precompiled wheels from the `build` image.
COPY --from=wheel-factory /io/wheels /wheels
RUN pip install /wheels/*.whl

COPY tests /io/tests
