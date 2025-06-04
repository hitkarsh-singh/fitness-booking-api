# Fitness Studio Booking API

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime, timezone
from typing import List, Optional
import sqlite3
import logging
import pytz
from contextlib import contextmanager
import uuid
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fitness Studio Booking API",
    description="A booking system for fitness classes with timezone support",
    version="1.0.0"
)

class ClassCreate(BaseModel):
    name: str
    instructor: str
    datetime_str: str
    total_slots: int
    timezone_str: str = "Asia/Kolkata"  
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Class name cannot be empty')
        return v.strip()
    
    @validator('total_slots')
    def validate_slots(cls, v):
        if v <= 0:
            raise ValueError('Total slots must be greater than 0')
        return v

class ClassResponse(BaseModel):
    id: str
    name: str
    instructor: str
    datetime_utc: datetime
    datetime_local: str
    timezone: str
    total_slots: int
    available_slots: int
    booked_slots: int

class BookingRequest(BaseModel):
    class_id: str
    client_name: str
    client_email: EmailStr
    
    @validator('client_name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Client name cannot be empty')
        return v.strip()

class BookingResponse(BaseModel):
    id: str
    class_id: str
    class_name: str
    client_name: str
    client_email: str
    booking_time: datetime
    class_datetime: datetime

class DatabaseManager:
    def __init__(self, db_path: str = "fitness_studio.db"):
        self.db_path = db_path
        self.init_database()
        self.seed_sample_data()
    
    @contextmanager
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        with self.get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS classes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    instructor TEXT NOT NULL,
                    datetime_utc TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    total_slots INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS bookings (
                    id TEXT PRIMARY KEY,
                    class_id TEXT NOT NULL,
                    client_name TEXT NOT NULL,
                    client_email TEXT NOT NULL,
                    booking_time TEXT NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES classes (id)
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def seed_sample_data(self):
        """Add sample fitness classes"""
        with self.get_db_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM classes")
            if cursor.fetchone()[0] > 0:
                return
            
            ist = pytz.timezone('Asia/Kolkata')
            sample_classes = [
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Morning Yoga',
                    'instructor': 'Priya Sharma',
                    'datetime_utc': datetime(2025, 6, 10, 1, 30).replace(tzinfo=timezone.utc).isoformat(),  # 7:00 AM IST
                    'timezone': 'Asia/Kolkata',
                    'total_slots': 20,
                    'created_at': datetime.now(timezone.utc).isoformat()
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Evening Zumba',
                    'instructor': 'Rahul Mehta',
                    'datetime_utc': datetime(2025, 6, 10, 13, 30).replace(tzinfo=timezone.utc).isoformat(),  # 7:00 PM IST
                    'timezone': 'Asia/Kolkata',
                    'total_slots': 15,
                    'created_at': datetime.now(timezone.utc).isoformat()
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'HIIT Training',
                    'instructor': 'Arjun Singh',
                    'datetime_utc': datetime(2025, 6, 11, 2, 0).replace(tzinfo=timezone.utc).isoformat(),  # 7:30 AM IST
                    'timezone': 'Asia/Kolkata',
                    'total_slots': 12,
                    'created_at': datetime.now(timezone.utc).isoformat()
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Power Yoga',
                    'instructor': 'Sneha Patel',
                    'datetime_utc': datetime(2025, 6, 12, 0, 0).replace(tzinfo=timezone.utc).isoformat(),  # 5:30 AM IST
                    'timezone': 'Asia/Kolkata',
                    'total_slots': 18,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            ]
            
            for class_data in sample_classes:
                conn.execute('''
                    INSERT INTO classes (id, name, instructor, datetime_utc, timezone, total_slots, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    class_data['id'],
                    class_data['name'],
                    class_data['instructor'],
                    class_data['datetime_utc'],
                    class_data['timezone'],
                    class_data['total_slots'],
                    class_data['created_at']
                ))
            
            conn.commit()
            logger.info(f"Seeded {len(sample_classes)} sample classes")

db_manager = DatabaseManager()


def get_available_slots(class_id: str) -> int:
    """Calculate available slots for a class"""
    with db_manager.get_db_connection() as conn:
        cursor = conn.execute("SELECT total_slots FROM classes WHERE id = ?", (class_id,))
        result = cursor.fetchone()
        if not result:
            return 0
        
        total_slots = result['total_slots']
        
        cursor = conn.execute("SELECT COUNT(*) as booked FROM bookings WHERE class_id = ?", (class_id,))
        booked_slots = cursor.fetchone()['booked']
        
        return total_slots - booked_slots

def convert_timezone(dt_utc: datetime, target_timezone: str) -> str:
    try:
        tz = pytz.timezone(target_timezone)
        dt_local = dt_utc.replace(tzinfo=timezone.utc).astimezone(tz)
        return dt_local.strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception as e:
        logger.error(f"Timezone conversion error: {e}")
        return dt_utc.strftime('%Y-%m-%d %H:%M:%S UTC')


@app.get("/", summary="API Health Check")
async def root():
    """Health check endpoint"""
    return {
        "message": "Fitness Studio Booking API is running!",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/classes", response_model=List[ClassResponse], summary="Get All Classes")
async def get_classes(
    timezone_str: str = Query("Asia/Kolkata", description="Timezone for displaying class times"),
    upcoming_only: bool = Query(True, description="Show only upcoming classes")
):
    
    try:
        with db_manager.get_db_connection() as conn:
            query = "SELECT * FROM classes"
            if upcoming_only:
                current_time = datetime.now(timezone.utc).isoformat()
                query += f" WHERE datetime_utc > '{current_time}'"
            query += " ORDER BY datetime_utc ASC"
            
            cursor = conn.execute(query)
            classes = cursor.fetchall()
        
        result = []
        for class_row in classes:
            class_id = class_row['id']
            available_slots = get_available_slots(class_id)
            booked_slots = class_row['total_slots'] - available_slots
            
            dt_utc = datetime.fromisoformat(class_row['datetime_utc'].replace('Z', '+00:00'))
            
            class_response = ClassResponse(
                id=class_id,
                name=class_row['name'],
                instructor=class_row['instructor'],
                datetime_utc=dt_utc,
                datetime_local=convert_timezone(dt_utc, timezone_str),
                timezone=timezone_str,
                total_slots=class_row['total_slots'],
                available_slots=available_slots,
                booked_slots=booked_slots
            )
            result.append(class_response)
        
        logger.info(f"Retrieved {len(result)} classes")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving classes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/book", response_model=BookingResponse, summary="Book a Class")
async def book_class(booking: BookingRequest):
    
    try:
        with db_manager.get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM classes WHERE id = ? AND datetime_utc > ?",
                (booking.class_id, datetime.now(timezone.utc).isoformat())
            )
            class_row = cursor.fetchone()
            
            if not class_row:
                raise HTTPException(
                    status_code=404, 
                    detail="Class not found or has already occurred"
                )
            
            available_slots = get_available_slots(booking.class_id)
            if available_slots <= 0:
                raise HTTPException(
                    status_code=409, 
                    detail="No available slots for this class"
                )
            
            cursor = conn.execute(
                "SELECT id FROM bookings WHERE class_id = ? AND client_email = ?",
                (booking.class_id, booking.client_email)
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=409, 
                    detail="You have already booked this class"
                )
            
            booking_id = str(uuid.uuid4())
            booking_time = datetime.now(timezone.utc).isoformat()
            
            conn.execute('''
                INSERT INTO bookings (id, class_id, client_name, client_email, booking_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                booking_id,
                booking.class_id,
                booking.client_name,
                booking.client_email,
                booking_time
            ))
            
            conn.commit()
            
            class_datetime = datetime.fromisoformat(class_row['datetime_utc'].replace('Z', '+00:00'))
            
            response = BookingResponse(
                id=booking_id,
                class_id=booking.class_id,
                class_name=class_row['name'],
                client_name=booking.client_name,
                client_email=booking.client_email,
                booking_time=datetime.fromisoformat(booking_time.replace('Z', '+00:00')),
                class_datetime=class_datetime
            )
            
            logger.info(f"Booking created: {booking_id} for class {booking.class_id}")
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/bookings", response_model=List[BookingResponse], summary="Get User Bookings")
async def get_bookings(
    email: EmailStr = Query(..., description="Client email address"),
    upcoming_only: bool = Query(True, description="Show only upcoming bookings")
):

    try:
        with db_manager.get_db_connection() as conn:
            query = '''
                SELECT b.*, c.name as class_name, c.datetime_utc as class_datetime
                FROM bookings b
                JOIN classes c ON b.class_id = c.id
                WHERE b.client_email = ?
            '''
            params = [email]
            
            if upcoming_only:
                query += " AND c.datetime_utc > ?"
                params.append(datetime.now(timezone.utc).isoformat())
            
            query += " ORDER BY c.datetime_utc ASC"
            
            cursor = conn.execute(query, params)
            bookings = cursor.fetchall()
        
        result = []
        for booking_row in bookings:
            booking_response = BookingResponse(
                id=booking_row['id'],
                class_id=booking_row['class_id'],
                class_name=booking_row['class_name'],
                client_name=booking_row['client_name'],
                client_email=booking_row['client_email'],
                booking_time=datetime.fromisoformat(booking_row['booking_time'].replace('Z', '+00:00')),
                class_datetime=datetime.fromisoformat(booking_row['class_datetime'].replace('Z', '+00:00'))
            )
            result.append(booking_response)
        
        logger.info(f"Retrieved {len(result)} bookings for {email}")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving bookings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/classes", response_model=ClassResponse, summary="Create New Class")
async def create_class(class_data: ClassCreate):
   
    try:
        local_tz = pytz.timezone(class_data.timezone_str)
        
        local_dt = datetime.strptime(class_data.datetime_str, '%Y-%m-%d %H:%M')
        local_dt = local_tz.localize(local_dt)
        utc_dt = local_dt.astimezone(timezone.utc)
        
        if utc_dt <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="Class datetime must be in the future"
            )
        
        class_id = str(uuid.uuid4())
        
        with db_manager.get_db_connection() as conn:
            conn.execute('''
                INSERT INTO classes (id, name, instructor, datetime_utc, timezone, total_slots, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                class_id,
                class_data.name,
                class_data.instructor,
                utc_dt.isoformat(),
                class_data.timezone_str,
                class_data.total_slots,
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()
        
        response = ClassResponse(
            id=class_id,
            name=class_data.name,
            instructor=class_data.instructor,
            datetime_utc=utc_dt,
            datetime_local=convert_timezone(utc_dt, class_data.timezone_str),
            timezone=class_data.timezone_str,
            total_slots=class_data.total_slots,
            available_slots=class_data.total_slots,
            booked_slots=0
        )
        
        logger.info(f"Created new class: {class_id}")
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating class: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")