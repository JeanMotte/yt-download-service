# --- Stage 1: Builder ---
# This stage installs build tools and builds our application wheel.
FROM python:3.11-slim-bookworm as builder

# Install poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy only the files needed to build dependencies
# This leverages Docker's layer caching
COPY poetry.lock pyproject.toml ./

# Install dependencies, but not dev dependencies
# --no-root is important so it doesn't try to install the project itself yet
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the application source code
COPY ./src ./src

# Build the wheel file
RUN poetry build


# --- Stage 2: Final Image ---
# This stage takes the built artifact and creates a slim final image.
FROM python:3.11-slim-bookworm

ENV USER=myapp-user
ENV HOME_DIR=/app

WORKDIR ${HOME_DIR}

# Create a non-root user
RUN useradd -s /bin/bash -m -d ${HOME_DIR} ${USER}

# Copy the built wheel from the builder stage
COPY --from=builder /app/dist/*.whl /tmp/app.whl

# Install the application wheel using pip
# This is faster and simpler than installing poetry again
RUN pip install --no-cache-dir /tmp/app.whl && rm /tmp/app.whl

# Switch to the non-root user
USER ${USER}

# The command to run your application
CMD ["uvicorn", "src.yt_download_service.main:app", "--host", "0.0.0.0", "--port", "8000"]