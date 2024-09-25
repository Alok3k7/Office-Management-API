from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from app.config.db import db
from bson import ObjectId
from typing import List, Optional

router = APIRouter()
chats_collection = db['chats']  # MongoDB collection for chats


class ChatCreate(BaseModel):
    message: str = Field(..., description="The content of the chat message.")
    sender: str = Field(..., description="The name of the person sending the message.")
    timestamp: str = Field(..., description="The timestamp when the message was sent.")


class ChatResponse(BaseModel):
    id: str = Field(..., description="The unique identifier of the chat.")
    message: str = Field(..., description="The content of the chat message.")
    sender: str = Field(..., description="The name of the person who sent the message.")
    timestamp: str = Field(..., description="The timestamp when the message was sent.")


class SuccessResponse(BaseModel):
    detail: str
    data: Optional[ChatResponse] = None


@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(chat: ChatCreate):
    """Create a new chat entry."""
    chat_dict = chat.dict()
    try:
        result = chats_collection.insert_one(chat_dict)
        chat_dict["_id"] = str(result.inserted_id)
        response_data = ChatResponse(id=chat_dict["_id"], **chat_dict)
        return SuccessResponse(detail="Chat created successfully.", data=response_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=List[ChatResponse], status_code=status.HTTP_200_OK)
async def get_chats():
    """Retrieve all chats."""
    try:
        chats = list(chats_collection.find())
        return [ChatResponse(id=str(chat["_id"]), **chat) for chat in chats]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/search/", response_model=List[ChatResponse], status_code=status.HTTP_200_OK)
async def search_chats(
        message: Optional[str] = Query(None, description="Search chats by message content."),
        sender: Optional[str] = Query(None, description="Search chats by sender's name."),
        timestamp: Optional[str] = Query(None, description="Search chats by timestamp.")
):
    """Search for chats based on message, sender, or timestamp."""
    query = {}
    if message:
        query["message"] = {"$regex": message, "$options": "i"}  # Case-insensitive match
    if sender:
        query["sender"] = sender
    if timestamp:
        query["timestamp"] = timestamp

    try:
        chats = list(chats_collection.find(query))
        return [ChatResponse(id=str(chat["_id"]), **chat) for chat in chats]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{chat_id}", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def update_chat(chat_id: str, chat: ChatCreate):
    """Update an existing chat by ID."""
    chat_dict = chat.dict()
    try:
        result = chats_collection.update_one(
            {"_id": ObjectId(chat_id)},
            {"$set": chat_dict}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
        chat_dict["_id"] = chat_id
        response_data = ChatResponse(id=chat_id, **chat_dict)
        return SuccessResponse(detail="Chat updated successfully.", data=response_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: str):
    """Delete a chat by ID."""
    try:
        result = chats_collection.delete_one({"_id": ObjectId(chat_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Chat not found")
        # No response body for a 204 No Content response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
