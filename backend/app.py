import os
import uuid
import json
import asyncio
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from pipeline import run_ml_pipeline
import zipfile
from database import init_db, AsyncSessionLocal, Job, Group
from sqlalchemy import select
from sqlalchemy.orm import selectinload

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, "data", "temp_jobs")
EXPORT_DIR = os.path.join(BASE_DIR, "data", "exports")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# In-memory store for job events for SSE streaming
job_events = {}

class ExportRequest(BaseModel):
    groups: list

@app.post("/api/process")
async def process_images(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    saved_files = []
    for file in files:
        safe_filename = os.path.basename(file.filename)
        file_path = os.path.join(job_dir, safe_filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        saved_files.append(safe_filename)
        
    job_events[job_id] = asyncio.Queue()
    
    async with AsyncSessionLocal() as session:
        new_job = Job(id=job_id, status="processing", progress_msg="Starting...")
        session.add(new_job)
        await session.commit()
    
    # Run the pipeline in a background thread to not block the async event loop
    loop = asyncio.get_running_loop()
    background_tasks.add_task(background_pipeline_runner, job_id, job_dir, saved_files, loop)
    
    return {"job_id": job_id}

async def update_db_progress(job_id, msg):
    async with AsyncSessionLocal() as session:
        job = await session.get(Job, job_id)
        if job:
            job.progress_msg = msg
            await session.commit()

async def insert_db_group(job_id, group_data):
    async with AsyncSessionLocal() as session:
        new_group = Group(
            id=group_data["id"],
            job_id=job_id,
            name=group_data["name"],
            images=group_data["images"]
        )
        session.add(new_group)
        await session.commit()

async def update_db_status(job_id, status, msg=""):
    async with AsyncSessionLocal() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = status
            if msg:
                job.progress_msg = msg
            await session.commit()

def background_pipeline_runner(job_id, job_dir, saved_files, loop):
    queue = job_events[job_id]
    
    def sync_update_progress(msg):
        asyncio.run_coroutine_threadsafe(queue.put({"event": "progress", "data": msg}), loop)
        asyncio.run_coroutine_threadsafe(update_db_progress(job_id, msg), loop)
        
    try:
        for result in run_ml_pipeline(job_dir, saved_files, sync_update_progress):
            asyncio.run_coroutine_threadsafe(queue.put({"event": "group", "data": result}), loop)
            asyncio.run_coroutine_threadsafe(insert_db_group(job_id, result), loop)
            
        asyncio.run_coroutine_threadsafe(queue.put({"event": "done", "data": "Pipeline Finished!"}), loop)
        asyncio.run_coroutine_threadsafe(update_db_status(job_id, "done", "Pipeline Finished!"), loop)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(queue.put({"event": "error", "data": str(e)}), loop)
        asyncio.run_coroutine_threadsafe(update_db_status(job_id, "error", str(e)), loop)

@app.get("/api/jobs/{job_id}")
async def get_job_state(job_id: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Job).options(selectinload(Job.groups)).filter(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return {"error": "Job not found"}
        
        groups_data = []
        for g in job.groups:
            groups_data.append({
                "id": g.id,
                "name": g.name,
                "images": g.images
            })
            
        return {
            "id": job.id,
            "status": job.status,
            "progress_msg": job.progress_msg,
            "groups": groups_data
        }

@app.get("/api/events/{job_id}")
async def event_stream(job_id: str):
    queue = job_events.get(job_id)
    if not queue:
        return {"error": "Job not found"}
        
    async def event_generator():
        while True:
            msg = await queue.get()
            yield f"data: {json.dumps(msg)}\n\n"
            if msg["event"] in ["done", "error"]:
                break
                
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/images/{job_id}/{filename}")
async def get_image(job_id: str, filename: str):
    file_path = os.path.join(TEMP_DIR, job_id, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

@app.post("/api/export")
async def export_zip(req: ExportRequest):
    export_id = str(uuid.uuid4())
    zip_path = os.path.join(EXPORT_DIR, f"{export_id}.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for group in req.groups:
            group_name = group['name']
            job_id = group['job_id']
            
            for idx, img in enumerate(group['images']):
                use_bg = img.get('use_bg_removed', False)
                filename = img['bg_removed'] if use_bg else img['original']
                source_path = os.path.join(TEMP_DIR, job_id, filename)
                
                if os.path.exists(source_path):
                    ext = os.path.splitext(filename)[1]
                    zipf.write(source_path, arcname=f"{group_name}_{idx+1}{ext}")
                    
    return {"download_url": f"/api/download/{export_id}.zip"}

@app.get("/api/download/{filename}")
async def download_export(filename: str):
    file_path = os.path.join(EXPORT_DIR, filename)
    return FileResponse(file_path, media_type='application/zip', filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
