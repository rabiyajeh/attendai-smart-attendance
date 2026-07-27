import enum, uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, Text, Boolean, Float, LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def now(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass
class Role(str, enum.Enum): admin="admin"; teacher="teacher"; student="student"
class Status(str, enum.Enum): present="present"; late="late"; absent="absent"; excused="excused"; pending_review="pending_review"
class User(Base):
    __tablename__="users"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    email:Mapped[str]=mapped_column(String(255),unique=True,index=True)
    full_name:Mapped[str]=mapped_column(String(160))
    password_hash:Mapped[str]=mapped_column(Text)
    role:Mapped[str]=mapped_column(String(20),index=True)
    active:Mapped[bool]=mapped_column(Boolean,default=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    deleted_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
class Department(Base):
    __tablename__="departments"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    name:Mapped[str]=mapped_column(String(120),unique=True)
class Student(Base):
    __tablename__="students"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    user_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("users.id"),unique=True)
    student_no:Mapped[str]=mapped_column(String(40),unique=True,index=True)
    department_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("departments.id"))
    biometric_consent:Mapped[bool]=mapped_column(Boolean,default=False)
class Teacher(Base):
    __tablename__="teachers"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    user_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("users.id"),unique=True)
    employee_no:Mapped[str]=mapped_column(String(40),unique=True)
class Course(Base):
    __tablename__="courses"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    code:Mapped[str]=mapped_column(String(30),unique=True,index=True)
    name:Mapped[str]=mapped_column(String(160))
    department_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("departments.id"))
class CourseEnrollment(Base):
    __tablename__="course_enrollments"; __table_args__=(UniqueConstraint("course_id","student_id"),)
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    course_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("courses.id"))
    student_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("students.id"))
class ClassSchedule(Base):
    __tablename__="class_schedules"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    course_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("courses.id"))
    teacher_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("teachers.id"))
    room:Mapped[str]=mapped_column(String(80)); starts_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
class AttendanceSession(Base):
    __tablename__="attendance_sessions"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    schedule_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("class_schedules.id"))
    started_by:Mapped[uuid.UUID]=mapped_column(ForeignKey("users.id"))
    started_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    ended_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    late_after_minutes:Mapped[int]=mapped_column(default=10)
class AttendanceRecord(Base):
    __tablename__="attendance_records"; __table_args__=(UniqueConstraint("session_id","student_id",name="uq_attendance_student_session"),)
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    session_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("attendance_sessions.id"),index=True)
    student_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("students.id"),index=True)
    status:Mapped[str]=mapped_column(String(24),index=True)
    confidence:Mapped[float|None]=mapped_column(Float)
    recorded_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    modified_by:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("users.id"))
    modification_reason:Mapped[str|None]=mapped_column(Text)
class FaceEmbedding(Base):
    __tablename__="face_embeddings"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    student_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("students.id"),index=True)
    encrypted_embedding:Mapped[bytes]=mapped_column(LargeBinary)
    model_version:Mapped[str]=mapped_column(String(50))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class CorrectionRequest(Base):
    __tablename__="correction_requests"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    record_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("attendance_records.id"))
    requested_by:Mapped[uuid.UUID]=mapped_column(ForeignKey("users.id"))
    reason:Mapped[str]=mapped_column(Text); status:Mapped[str]=mapped_column(String(20),default="pending")
class Notification(Base):
    __tablename__="notifications"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    user_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("users.id"),index=True)
    message:Mapped[str]=mapped_column(Text); read:Mapped[bool]=mapped_column(Boolean,default=False)
class Holiday(Base):
    __tablename__="holidays"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    name:Mapped[str]=mapped_column(String(120)); date:Mapped[datetime]=mapped_column(DateTime(timezone=True),unique=True)
class SystemSetting(Base):
    __tablename__="system_settings"
    key:Mapped[str]=mapped_column(String(100),primary_key=True); value:Mapped[str]=mapped_column(Text)
class AuditLog(Base):
    __tablename__="audit_logs"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    actor_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("users.id"),index=True)
    action:Mapped[str]=mapped_column(String(100),index=True); entity:Mapped[str]=mapped_column(String(80))
    entity_id:Mapped[str|None]=mapped_column(String(50)); detail:Mapped[str|None]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True)
