FROM python:3.11-slim-bookworm as builder

RUN pip install poetry

WORKDIR /app

# Copy only the files needed to build dependencies
COPY poetry.lock pyproject.toml ./

# Install dependencies, but not the project itself (the "root" package)
RUN poetry install --no-root --no-interaction --no-ansi

COPY ./src ./src
COPY README.md . 

# Build the wheel file
RUN poetry build


FROM python:3.11-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

ENV USER=myapp-user
ENV HOME_DIR=/app

WORKDIR ${HOME_DIR}

# Create a non-root user
RUN useradd -s /bin/bash -m -d ${HOME_DIR} ${USER}

# Copy the built wheel(s) into a temporary directory, preserving the original filename
COPY --from=builder /app/dist/*.whl /tmp/

# Install the wheel using a wildcard, then clean up
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*

# Switch to the non-root user
USER ${USER}

CMD ["uvicorn", "yt_download_service.main:app", "--host", "0.0.0.0", "--port", "8000"]