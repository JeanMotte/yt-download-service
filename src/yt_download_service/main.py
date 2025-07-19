from fastapi import FastAPI

# OpenAPI Generation is handled automatically by FastAPI.
# You can customize it here.
app = FastAPI(
    title="My Clean Architecture API",
    description="A demonstration of FastAPI with Clean Architecture.",
    version="1.0.0",
)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}