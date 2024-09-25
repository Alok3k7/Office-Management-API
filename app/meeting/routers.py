from fastapi import APIRouter, HTTPException, Query
from app.config.db import db
from bson import ObjectId
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter()
meetings_collection = db['meetings']  # MongoDB collection for meetings

class MeetingBase(BaseModel):
    title: str = Field(..., description="The title of the meeting.")
    description: str = Field(..., description="Description of the meeting.")
    organizer: str = Field(..., description="Name of the person organizing the meeting.")
    date: str = Field(..., description="Date of the meeting in YYYY-MM-DD format.")
    start_time: str = Field(..., description="Meeting start time in HH:MM format.")
    end_time: str = Field(..., description="Meeting end time in HH:MM format.")
    attendees: List[str] = Field(..., description="List of attendees for the meeting.")

class Meeting(MeetingBase):
    id: str = Field(..., description="The unique identifier of the meeting.")

class MeetingResponse(BaseModel):
    detail: str
    data: Optional[Meeting] = None

@router.post("/", response_model=MeetingResponse, status_code=201)
def create_meeting(meeting: MeetingBase):
    """Create a new meeting."""
    existing_meeting = meetings_collection.find_one({"title": meeting.title, "date": meeting.date})
    if existing_meeting:
        raise HTTPException(status_code=400, detail="Meeting with this title on the same date already exists")

    meeting_dict = meeting.dict()
    result = meetings_collection.insert_one(meeting_dict)
    meeting_dict["_id"] = str(result.inserted_id)  # Add the new MongoDB ID

    return MeetingResponse(detail="Meeting created successfully.", data=Meeting(**{**meeting_dict, "id": meeting_dict["_id"]}))

@router.get("/", response_model=List[Meeting])
def get_meetings():
    """Retrieve a list of all meetings."""
    try:
        meetings = list(meetings_collection.find())
        for meeting in meetings:
            meeting["_id"] = str(meeting["_id"])  # Convert ObjectId to string
        return [Meeting(**{**meeting, "id": str(meeting["_id"])}) for meeting in meetings]  # Include id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/", response_model=List[Meeting])
def search_meetings(
        id: Optional[str] = Query(None),
        title: Optional[str] = Query(None),
        organizer: Optional[str] = Query(None),
        date: Optional[str] = Query(None)
):
    """Search for meetings based on ID, title, organizer, or date."""
    try:
        query = {}
        if id:
            query["_id"] = ObjectId(id)
        if title:
            query["title"] = {"$regex": title, "$options": "i"}  # Case-insensitive match
        if organizer:
            query["organizer"] = {"$regex": organizer, "$options": "i"}
        if date:
            query["date"] = date

        meetings = list(meetings_collection.find(query))
        for meeting in meetings:
            meeting["_id"] = str(meeting["_id"])  # Convert ObjectId to string
        return [Meeting(**{**meeting, "id": str(meeting["_id"])}) for meeting in meetings]  # Include id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{meeting_id}", response_model=MeetingResponse)
def update_meeting(meeting_id: str, meeting: MeetingBase):
    """Update an existing meeting's details."""
    try:
        meeting_dict = meeting.dict()
        result = meetings_collection.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": meeting_dict}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Meeting not found")

        meeting_dict["_id"] = meeting_id  # Include the ID in the response
        return MeetingResponse(detail="Meeting updated successfully.", data=Meeting(**{**meeting_dict, "id": meeting_id}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{meeting_id}", response_model=dict)
def delete_meeting(meeting_id: str):
    """Delete a meeting by ID."""
    try:
        result = meetings_collection.delete_one({"_id": ObjectId(meeting_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return {"detail": "Meeting deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Note: Ensure to include this router in your FastAPI app instance in your main.py file
