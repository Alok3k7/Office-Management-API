from fastapi import APIRouter, HTTPException, Query
from app.config.db import db
from bson import ObjectId
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter()
projects_collection = db['projects']  # MongoDB collection for projects


class ProjectBase(BaseModel):
    name: str = Field(..., description="The name of the project.")
    description: str = Field(..., description="Description of the project.")
    start_date: str = Field(..., description="Project start date in YYYY-MM-DD format.")
    end_date: Optional[str] = Field(None, description="Project end date in YYYY-MM-DD format.")
    status: str = Field(..., description="Current status of the project.")
    members: List[str] = Field(..., description="List of team members involved in the project.")


class Project(ProjectBase):
    id: str = Field(..., description="The unique identifier of the project.")


class ProjectResponse(BaseModel):
    detail: str
    data: Optional[Project] = None


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(project: ProjectBase):
    """Create a new project."""
    existing_project = projects_collection.find_one({"name": project.name})
    if existing_project:
        raise HTTPException(status_code=400, detail="Project with this name already exists")

    project_dict = project.dict()
    result = projects_collection.insert_one(project_dict)
    project_dict["_id"] = str(result.inserted_id)  # Add the new MongoDB ID

    return ProjectResponse(detail="Project created successfully.",
                           data=Project(**{**project_dict, "id": project_dict["_id"]}))


@router.get("/", response_model=List[Project])
def get_projects():
    """Retrieve a list of all projects."""
    try:
        projects = list(projects_collection.find())
        for project in projects:
            project["_id"] = str(project["_id"])  # Convert ObjectId to string
        return [Project(**{**project, "id": str(project["_id"])}) for project in projects]  # Include id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", response_model=List[Project])
def search_projects(
        id: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        status: Optional[str] = Query(None)
):
    """Search for projects based on ID, name, or status."""
    try:
        query = {}
        if id:
            query["_id"] = ObjectId(id)
        if name:
            query["name"] = {"$regex": name, "$options": "i"}  # Case-insensitive match
        if status:
            query["status"] = {"$regex": status, "$options": "i"}

        projects = list(projects_collection.find(query))
        for project in projects:
            project["_id"] = str(project["_id"])  # Convert ObjectId to string
        return [Project(**{**project, "id": str(project["_id"])}) for project in projects]  # Include id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, project: ProjectBase):
    """Update an existing project's details."""
    try:
        project_dict = project.dict()
        result = projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": project_dict}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")

        project_dict["_id"] = project_id  # Include the ID in the response
        return ProjectResponse(detail="Project updated successfully.",
                               data=Project(**{**project_dict, "id": project_id}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}", response_model=dict)
def delete_project(project_id: str):
    """Delete a project by ID."""
    try:
        result = projects_collection.delete_one({"_id": ObjectId(project_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"detail": "Project deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Note: Ensure to include this router in your FastAPI app instance in your main.py file
