from fastapi import FastAPI

app = FastAPI()


@app.get("/healthz")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
