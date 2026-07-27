from datetime import datetime, timezone
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, WebSocket
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from .core import settings, verify_password, token, cipher
from .database import get_db
from .models import User, AttendanceSession, AttendanceRecord, FaceEmbedding, AuditLog

app=FastAPI(title="AttendAI API",version="1.0.0",description="Privacy-first smart attendance platform")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:3000","http://localhost:5173"],allow_methods=["*"],allow_headers=["*"])
oauth=OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@app.middleware("http")
async def secure_headers(request,call_next):
    response=await call_next(request)
    response.headers.update({"X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY","Referrer-Policy":"no-referrer","Permissions-Policy":"camera=(self)"})
    return response

async def current_user(raw:str=Depends(oauth),db:AsyncSession=Depends(get_db)):
    try: data=jwt.decode(raw,settings().jwt_secret,algorithms=["HS256"])
    except JWTError: raise HTTPException(401,"Invalid or expired token")
    user=await db.get(User,UUID(data["sub"]))
    if not user or not user.active: raise HTTPException(401,"Inactive account")
    return user
def roles(*allowed):
    async def check(user=Depends(current_user)):
        if user.role not in allowed: raise HTTPException(403,"Insufficient permissions")
        return user
    return check
class SessionIn(BaseModel): schedule_id:UUID; late_after_minutes:int=Field(10,ge=0,le=120)
class RecognitionIn(BaseModel):
    student_id:UUID; confidence:float=Field(ge=0,le=1); consecutive_frames:int=Field(ge=1); liveness_passed:bool
class CorrectionIn(BaseModel): status:str; reason:str=Field(min_length=5,max_length=1000)
class EmbeddingIn(BaseModel): student_id:UUID; embedding:list[float]=Field(min_length=128,max_length=1024); consent:bool

@app.get("/health")
async def health(): return {"status":"ok","recognition":"available"}
@app.post("/api/v1/auth/login")
async def login(form:OAuth2PasswordRequestForm=Depends(),db:AsyncSession=Depends(get_db)):
    user=(await db.execute(select(User).where(User.email==form.username))).scalar_one_or_none()
    if not user or not verify_password(form.password,user.password_hash): raise HTTPException(401,"Invalid credentials")
    return {"access_token":token(str(user.id),user.role),"refresh_token":token(str(user.id),user.role,True),"token_type":"bearer","role":user.role}
@app.get("/api/v1/users/me")
async def me(user=Depends(current_user)): return {"id":user.id,"email":user.email,"name":user.full_name,"role":user.role}
@app.post("/api/v1/attendance/sessions",status_code=201)
async def start_session(body:SessionIn,user=Depends(roles("admin","teacher")),db:AsyncSession=Depends(get_db)):
    session=AttendanceSession(schedule_id=body.schedule_id,started_by=user.id,late_after_minutes=body.late_after_minutes)
    db.add(session); await db.flush(); db.add(AuditLog(actor_id=user.id,action="session.started",entity="attendance_session",entity_id=str(session.id))); await db.commit()
    return {"id":session.id,"started_at":session.started_at}
@app.post("/api/v1/attendance/sessions/{session_id}/recognize")
async def recognize(session_id:UUID,body:RecognitionIn,user=Depends(roles("admin","teacher")),db:AsyncSession=Depends(get_db)):
    if not body.liveness_passed or body.consecutive_frames<3: return {"status":"pending_review","confirmed":False}
    if body.confidence<.88: return {"status":"unknown","confirmed":False}
    session=await db.get(AttendanceSession,session_id)
    if not session or session.ended_at: raise HTTPException(409,"Session is not active")
    minutes=(datetime.now(timezone.utc)-session.started_at).total_seconds()/60
    record=AttendanceRecord(session_id=session_id,student_id=body.student_id,status="late" if minutes>session.late_after_minutes else "present",confidence=body.confidence)
    db.add(record)
    try: await db.commit()
    except IntegrityError: await db.rollback(); return {"status":"already_recorded","confirmed":True}
    return {"status":record.status,"confirmed":True,"confidence":body.confidence}
@app.patch("/api/v1/attendance/records/{record_id}")
async def correct(record_id:UUID,body:CorrectionIn,user=Depends(roles("admin","teacher")),db:AsyncSession=Depends(get_db)):
    record=await db.get(AttendanceRecord,record_id)
    if not record: raise HTTPException(404,"Record not found")
    record.status=body.status; record.modified_by=user.id; record.modification_reason=body.reason
    db.add(AuditLog(actor_id=user.id,action="attendance.corrected",entity="attendance_record",entity_id=str(record.id),detail=body.reason)); await db.commit()
    return {"ok":True}
@app.post("/api/v1/faces/enroll",status_code=201)
async def enroll(body:EmbeddingIn,user=Depends(roles("admin","teacher")),db:AsyncSession=Depends(get_db)):
    if not body.consent: raise HTTPException(422,"Explicit biometric consent is required")
    encrypted=cipher().encrypt(",".join(map(str,body.embedding)).encode())
    db.add(FaceEmbedding(student_id=body.student_id,encrypted_embedding=encrypted,model_version="insightface-buffalo_l-v1"))
    db.add(AuditLog(actor_id=user.id,action="biometric.enrolled",entity="student",entity_id=str(body.student_id))); await db.commit()
    return {"enrolled":True}
@app.delete("/api/v1/faces/{student_id}",status_code=204)
async def delete_face(student_id:UUID,user=Depends(roles("admin")),db:AsyncSession=Depends(get_db)):
    rows=(await db.execute(select(FaceEmbedding).where(FaceEmbedding.student_id==student_id))).scalars()
    for row in rows: await db.delete(row)
    db.add(AuditLog(actor_id=user.id,action="biometric.deleted",entity="student",entity_id=str(student_id))); await db.commit()
@app.get("/api/v1/analytics/summary")
async def analytics(user=Depends(current_user),db:AsyncSession=Depends(get_db)):
    total=(await db.execute(select(func.count()).select_from(AttendanceRecord))).scalar()
    present=(await db.execute(select(func.count()).select_from(AttendanceRecord).where(AttendanceRecord.status.in_(["present","late"])))).scalar()
    return {"records":total,"attendance_rate":round(100*present/total,1) if total else 0}
@app.websocket("/ws/sessions/{session_id}")
async def live_updates(ws:WebSocket,session_id:str):
    await ws.accept(); await ws.send_json({"session_id":session_id,"state":"connected"})
    try:
        while True: await ws.receive_text()
    except Exception: await ws.close()
