# Use the UBI 8 minimal base image
# kics-scan disable=fd54f200-402c-4333-a5a4-36ef6709af2f
FROM registry.access.redhat.com/ubi8/ubi-minimal:latest AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # Paths for the virtual environment and working directory
    PYSETUP_PATH="/complyscribe-tests" \
    VENV_PATH="/complyscribe-tests/.venv"

LABEL maintainer="Red Hat Product Security" \
      summary="ComplyScribe"

# Ensure we use the virtualenv
ENV PATH="$VENV_PATH/bin:$PATH"

RUN microdnf update -y \
    && microdnf install -y python3.9 git \
    && microdnf clean all \
    && rm -rf /var/lib/apt/lists/*

FROM python-base AS dependencies

ARG POETRY_VERSION=1.7.1
ARG INSTALL_PLUGINS=true

# https://python-poetry.org/docs/configuration/#using-environment-variables
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# install poetry globally just for this intermediate build stage
RUN python3.9 -m pip install --no-cache-dir --upgrade pip setuptools && \
    python3.9 -m pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR "/build"
COPY . "/build"

# Install runtime deps and install the project in non-editable mode.
# Ensure pip and setuptools are updated in the virtualenv as well.
RUN python3.9 -m venv "$VENV_PATH" && \
    . "$VENV_PATH"/bin/activate && \
    python3.9 -m pip install --no-cache-dir --upgrade pip setuptools && \
    if [ "$INSTALL_PLUGINS" == "true" ]; then \
      poetry install --with plugins --no-root; \
    else \
      poetry install --no-root; \
    fi

RUN  python3.9 -m venv "$VENV_PATH" && \
  . "$VENV_PATH"/bin/activate && \
  poetry build -f wheel -n && \
  pip install --no-cache-dir --no-deps dist/*.whl && \
  rm -rf dist ./*.egg-info

FROM python-base AS final

COPY --from=dependencies $PYSETUP_PATH $PYSETUP_PATH

# Add wrappers for entrypoints that provide support for the actions
COPY ./actions/common.sh /
COPY ./actions/autosync/auto-sync-entrypoint.sh /
COPY ./actions/rules-transform/rules-transform-entrypoint.sh /
COPY ./actions/create-cd/create-cd-entrypoint.sh /
COPY ./actions/sync-upstreams/sync-upstreams-entrypoint.sh /

RUN chmod +x /auto-sync-entrypoint.sh /rules-transform-entrypoint.sh /create-cd-entrypoint.sh /sync-upstreams-entrypoint.sh

ENTRYPOINT ["python3.9", "-m" , "complyscribe"]
CMD ["--help"]
