from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import secrets
import gspread
from google.oauth2.service_account import Credentials
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
import os
import json

app = FastAPI()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    info=json.loads(os.environ.get("SERVICE_ACCOUNT_INFO")),
    scopes=SCOPES,
)

client = gspread.authorize(creds)


@app.get("/track/{tracker_id}")
def index(tracker_id: str):
    sheet = client.open_by_key("1LqMXuRoU8uljeM5MeZkrnVN1rmzNqUh2h1hUhkNsKKQ").sheet1
    sheet_df = pd.DataFrame(sheet.get_all_records())
    row_indices = sheet_df.index[sheet_df["Pixel ID"] == tracker_id].tolist()
    if row_indices:
        row_index = row_indices[0]
        sheet_df.at[row_index, "Reads"] += 1
        sheet_df.at[row_index, "Status"] = (
            "Read" if sheet_df.at[row_index, "Reads"] > 0 else "Sent"
        )
        sheet_df.fillna("", inplace=True)
        sheet.update([sheet_df.columns.values.tolist()] + sheet_df.values.tolist())

        pixel_path = "pixel.png"

        return FileResponse(
            pixel_path,
            media_type="image/png",
        )

    return JSONResponse(
        content={
            "error": "Pixel not found",
        },
        status_code=404,
    )


class EmailRequest(BaseModel):
    email: str


@app.post("/track")
async def track_pixel(request: EmailRequest):
    email = request.email
    tracker_id = str(secrets.token_urlsafe(16))
    pixel_url = f"https://pixel-tracker-xi.vercel.app/track/{tracker_id}"

    new_row = {
        "Pixel ID": tracker_id,
        "Email": email,
        "Status": "Sent",
        "Reads": 0,
        "Created At": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }
    sheet = client.open_by_key("1LqMXuRoU8uljeM5MeZkrnVN1rmzNqUh2h1hUhkNsKKQ").sheet1
    sheet.append_row(list(new_row.values()))

    return JSONResponse(
        content={
            "id": tracker_id,
            "trackingUrl": pixel_url,
        }
    )
