FROM python:3.11-slim-bookworm

# Avoid prompts from apt during installation
ENV DEBIAN_FRONTEND=noninteractive

# Define environment variables for the user and home directory
ENV USER=devuser
ENV HOME_DIR=/app

# Set the working directory inside the container
WORKDIR ${HOME_DIR}

# Install essential system-level packages like Git, Bash, , FFmpeg, OpenSSH
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -s /bin/bash -m -d ${HOME_DIR} ${USER} \
    && chown -R ${USER}:${USER} ${HOME_DIR}

# Switch to the newly created non-root user
USER ${USER}

# --- Tooling Installation ---
RUN python3 -m pip install --user poetry uv

# This makes the 'poetry' and 'uv' commands available in the shell.
ENV PATH="${HOME_DIR}/.local/bin:${PATH}"

# --- Poetry Configuration ---
RUN poetry config virtualenvs.in-project true

ENTRYPOINT []