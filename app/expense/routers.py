from fastapi import APIRouter, HTTPException, Query
from app.config.db import db
from bson import ObjectId
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter()
expenses_collection = db['expenses']  # MongoDB collection for expenses

class ExpenseBase(BaseModel):
    title: str = Field(..., description="The title of the expense.")
    amount: float = Field(..., description="The amount of the expense.")
    category: str = Field(..., description="The category of the expense.")
    incurred_by: str = Field(..., description="Name of the person who incurred the expense.")
    date: str = Field(..., description="The date of the expense.")

class Expense(ExpenseBase):
    id: str = Field(..., description="The unique identifier of the expense.")

class ExpenseResponse(BaseModel):
    detail: str
    data: Optional[Expense] = None

@router.post("/", response_model=ExpenseResponse, status_code=201)
def create_expense(expense: ExpenseBase):
    """Create a new expense."""
    expense_dict = expense.dict()
    result = expenses_collection.insert_one(expense_dict)
    expense_dict["_id"] = str(result.inserted_id)  # Add the new MongoDB ID

    # Ensure we create the Expense instance with the correct ID
    return ExpenseResponse(detail="Expense created successfully.", data=Expense(**{**expense_dict, "id": expense_dict["_id"]}))


@router.get("/", response_model=List[Expense])
def get_expenses():
    """Retrieve a list of all expenses."""
    try:
        expenses = list(expenses_collection.find())
        for exp in expenses:
            exp["_id"] = str(exp["_id"])  # Convert ObjectId to string
        return [Expense(**{**exp, "id": str(exp["_id"])}) for exp in expenses]  # Include id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", response_model=List[Expense])
def search_expenses(
        id: Optional[str] = Query(None),
        title: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        incurred_by: Optional[str] = Query(None)
):
    """Search for expenses based on ID, title, category, or incurred_by."""
    try:
        query = {}
        if id:
            query["_id"] = ObjectId(id)
        if title:
            query["title"] = {"$regex": title, "$options": "i"}  # Case-insensitive match
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        if incurred_by:
            query["incurred_by"] = {"$regex": incurred_by, "$options": "i"}

        expenses = list(expenses_collection.find(query))
        for exp in expenses:
            exp["_id"] = str(exp["_id"])  # Convert ObjectId to string
        return [Expense(**{**exp, "id": str(exp["_id"])}) for exp in expenses]  # Include id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: str, expense: ExpenseBase):
    """Update an existing expense's details."""
    try:
        expense_dict = expense.dict()
        result = expenses_collection.update_one(
            {"_id": ObjectId(expense_id)},
            {"$set": expense_dict}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Expense not found")

        expense_dict["_id"] = expense_id  # Include the ID in the response
        return ExpenseResponse(detail="Expense updated successfully.", data=Expense(**{**expense_dict, "id": expense_id}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{expense_id}", response_model=dict)
def delete_expense(expense_id: str):
    """Delete an expense by ID."""
    try:
        result = expenses_collection.delete_one({"_id": ObjectId(expense_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Expense not found")
        return {"detail": "Expense deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

