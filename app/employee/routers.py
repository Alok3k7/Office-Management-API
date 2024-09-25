from fastapi import APIRouter, HTTPException, Query
from app.config.db import db
from bson import ObjectId
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter()
employees_collection = db['employees']  # MongoDB collection for employees


class EmployeeBase(BaseModel):
    name: str = Field(..., description="The name of the employee.")
    position: str = Field(..., description="The position of the employee.")
    salary: float = Field(..., description="The salary of the employee.")


class Employee(EmployeeBase):
    id: str = Field(..., description="The unique identifier of the employee.")


class EmployeeResponse(BaseModel):
    detail: str
    data: Optional[Employee] = None


@router.post("/", response_model=EmployeeResponse, status_code=201)
def create_employee(employee: EmployeeBase):
    """Create a new employee."""
    try:
        existing_employee = employees_collection.find_one({"name": employee.name})
        if existing_employee:
            raise HTTPException(status_code=400, detail="Employee with this name already exists")

        employee_dict = employee.dict()
        result = employees_collection.insert_one(employee_dict)
        employee_dict["_id"] = str(result.inserted_id)  # Add the new MongoDB ID
        return EmployeeResponse(detail="Employee created successfully.", data=Employee(**employee_dict))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Employee])
def get_employees():
    """Retrieve a list of all employees."""
    try:
        employees = list(employees_collection.find())
        for emp in employees:
            emp["_id"] = str(emp["_id"])  # Convert ObjectId to string
        return [Employee(**emp) for emp in employees]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", response_model=List[Employee])
def search_employees(
        id: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        position: Optional[str] = Query(None),
        salary: Optional[float] = Query(None)
):
    """Search for employees based on ID, name, position, or salary."""
    try:
        query = {}
        if id:
            query["_id"] = ObjectId(id)
        if name:
            query["name"] = {"$regex": name, "$options": "i"}  # Case-insensitive match
        if position:
            query["position"] = position
        if salary:
            query["salary"] = salary

        employees = list(employees_collection.find(query))
        for emp in employees:
            emp["_id"] = str(emp["_id"])  # Convert ObjectId to string
        return [Employee(**emp) for emp in employees]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: str, employee: EmployeeBase):
    """Update an existing employee's details."""
    try:
        employee_dict = employee.dict()
        result = employees_collection.update_one(
            {"_id": ObjectId(employee_id)},
            {"$set": employee_dict}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Employee not found")

        employee_dict["_id"] = employee_id  # Include the ID in the response
        return EmployeeResponse(detail="Employee updated successfully.", data=Employee(**employee_dict))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{employee_id}", response_model=dict)
def delete_employee(employee_id: str):
    """Delete an employee by ID."""
    try:
        result = employees_collection.delete_one({"_id": ObjectId(employee_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {"detail": "Employee deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
