from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/track/{tracker_id}")
def index(tracker_id: str):
    pixel_path = "pixel.png"

    return FileResponse(
        pixel_path,
        media_type="image/png",
    )
