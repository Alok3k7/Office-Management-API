import uvicorn
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi import Request
from app.employee.routers import router as employee_router
from app.chat.routers import router as chat_router
from app.document.routers import router as document_router
from app.meeting.routers import router as meeting_router
from app.project.routers import router as project_router
from app.config.settings import settings  # Assuming settings module for configurations

# Initialize FastAPI app
app = FastAPI(
    title="Employee Management API",
    description="A complete solution for managing employees, projects, documents, chats, and meetings.",
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Alok - API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)


# Use lifespan context manager for startup and shutdown
@app.on_event("startup")
async def startup_event():
    print("Application startup...")
    # Perform startup tasks (e.g., connect to the database)


@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down...")
    # Perform shutdown tasks (e.g., close the database connection)


# Include routers
app.include_router(employee_router, prefix="/employees", tags=["Employees"])
app.include_router(chat_router, prefix="/chats", tags=["Chats"])
app.include_router(document_router, prefix="/documents", tags=["Documents"])
app.include_router(meeting_router, prefix="/meetings", tags=['Meetings'])
app.include_router(project_router, prefix="/projects", tags=['Projects'])


# Root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Employee Management API"}


# Custom error handling (optional)
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
