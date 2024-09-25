from fastapi import APIRouter, HTTPException, Query
from app.config.db import db
from bson import ObjectId
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter()
documents_collection = db['documents']  # MongoDB collection for documents


class DocumentBase(BaseModel):
    title: str = Field(..., description="The title of the document.")
    description: str = Field(..., description="Description of the document.")
    uploaded_by: str = Field(..., description="Name of the person who uploaded the document.")


class Document(DocumentBase):
    id: str = Field(..., description="The unique identifier of the document.")


class DocumentResponse(BaseModel):
    detail: str
    data: Optional[Document] = None


@router.post("/", response_model=DocumentResponse, status_code=201)
def create_document(document: DocumentBase):
    """Create a new document."""
    existing_document = documents_collection.find_one({"title": document.title})
    if existing_document:
        raise HTTPException(status_code=400, detail="Document with this title already exists")

    document_dict = document.dict()
    result = documents_collection.insert_one(document_dict)
    document_dict["_id"] = str(result.inserted_id)  # Add the new MongoDB ID

    # Ensure we create the Document instance with the correct ID
    return DocumentResponse(detail="Document created successfully.",
                            data=Document(**{**document_dict, "id": document_dict["_id"]}))


@router.get("/", response_model=List[Document])
def get_documents():
    """Retrieve a list of all documents."""
    try:
        documents = list(documents_collection.find())
        for doc in documents:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        return [Document(**{**doc, "id": str(doc["_id"])}) for doc in documents]  # Include id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", response_model=List[Document])
def search_documents(
        id: Optional[str] = Query(None),
        title: Optional[str] = Query(None),
        uploaded_by: Optional[str] = Query(None)
):
    """Search for documents based on ID, title, or uploaded_by."""
    try:
        query = {}
        if id:
            query["_id"] = ObjectId(id)
        if title:
            query["title"] = {"$regex": title, "$options": "i"}  # Case-insensitive match
        if uploaded_by:
            query["uploaded_by"] = {"$regex": uploaded_by, "$options": "i"}

        documents = list(documents_collection.find(query))
        for doc in documents:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        return [Document(**{**doc, "id": str(doc["_id"])}) for doc in documents]  # Include id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(document_id: str, document: DocumentBase):
    """Update an existing document's details."""
    try:
        document_dict = document.dict()
        result = documents_collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": document_dict}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")

        document_dict["_id"] = document_id  # Include the ID in the response
        return DocumentResponse(detail="Document updated successfully.",
                                data=Document(**{**document_dict, "id": document_id}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", response_model=dict)
def delete_document(document_id: str):
    """Delete a document by ID."""
    try:
        result = documents_collection.delete_one({"_id": ObjectId(document_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"detail": "Document deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
