from fastapi import FastAPI

app = FastAPI(title="BookCircle API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}