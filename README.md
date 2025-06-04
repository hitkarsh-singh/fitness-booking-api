# 🧘‍♀️ Fitness Studio Booking API

A comprehensive RESTful API for managing fitness class bookings with timezone support, built with FastAPI and SQLite.

## 🚀 Features

- **Class Management**: View available fitness classes with real-time slot availability
- **Smart Booking System**: Book classes with duplicate prevention and slot validation
- **Timezone Support**: All times stored in UTC with dynamic timezone conversion
- **User Booking History**: Track all bookings by email address
- **Comprehensive Validation**: Robust input validation and error handling
- **Clean Architecture**: Modular, well-documented, and testable code
- **Interactive API Docs**: Auto-generated Swagger/OpenAPI documentation

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.8+)
- **Database**: SQLite (in-memory for development)
- **Validation**: Pydantic with email validation
- **Timezone Handling**: pytz
- **Testing**: pytest with comprehensive test coverage
- **Server**: Uvicorn ASGI server
- **Logging**: Python logging with structured output

## 📋 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check endpoint |
| `GET` | `/classes` | Get all available classes |
| `POST` | `/book` | Book a class |
| `GET` | `/bookings` | Get user bookings by email |
| `POST` | `/classes` | Create new class (Admin) |

### Endpoint Details

#### GET /classes
- **Query Parameters**:
  - `timezone_str` (optional): Target timezone (default: Asia/Kolkata)
  - `upcoming_only` (optional): Show only future classes (default: true)
- **Response**: List of classes with availability info

#### POST /book
- **Body**: `{ "class_id": "string", "client_name": "string", "client_email": "email" }`
- **Response**: Booking confirmation details
- **Validations**: 
  - Class exists and is upcoming
  - Available slots
  - No duplicate bookings for same email

#### GET /bookings
- **Query Parameters**:
  - `email` (required): Client email address
  - `upcoming_only` (optional): Show only future bookings (default: true)
- **Response**: List of user's bookings

## 🔧 Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd fitness-booking-api
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python main.py
```
or
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. **Access the API**
- API Base URL: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing

### Run Tests
```bash
# Install pytest if not already installed
pip install pytest pytest-asyncio

# Run all tests
pytest test_main.py -v

# Run with coverage
pip install pytest-cov
pytest test_main.py --cov=main --cov-report=html
```

### Test Coverage
The test suite covers:
- ✅ API endpoint functionality
- ✅ Input validation
- ✅ Error handling
- ✅ Business logic (booking constraints)
- ✅ Database operations
- ✅ Timezone conversions

## 📝 Sample API Requests

### 1. Get All Classes
```bash
curl -X GET "http://localhost:8000/classes" \
  -H "accept: application/json"
```

**Response:**
```json
[
  {
    "id": "uuid-here",
    "name": "Morning Yoga",
    "instructor": "Priya Sharma",
    "datetime_utc": "2025-06-10T01:30:00",
    "datetime_local": "2025-06-10 07:00:00 IST",
    "timezone": "Asia/Kolkata",
    "total_slots": 20,
    "available_slots": 18,
    "booked_slots": 2
  }
]
```

### 2. Book a Class
```bash
curl -X POST "http://localhost:8000/book" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "class_id": "your-class-id-here",
    "client_name": "John Doe",
    "client_email": "john.doe@example.com"
  }'
```

**Response:**
```json
{
  "id": "booking-uuid",
  "class_id": "class-uuid",
  "class_name": "Morning Yoga",
  "client_name": "John Doe",
  "client_email": "john.doe@example.com",
  "booking_time": "2025-06-04T10:30:00",
  "class_datetime": "2025-06-10T01:30:00"
}
```

### 3. Get User Bookings
```bash
curl -X GET "http://localhost:8000/bookings?email=john.doe@example.com" \
  -H "accept: application/json"
```

### 4. Get Classes in Different Timezone
```bash
curl -X GET "http://localhost:8000/classes?timezone_str=US/Pacific" \
  -H "accept: application/json"
```

### 5. Create New Class (Admin)
```bash
curl -X POST "http://localhost:8000/classes" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Evening Pilates",
    "instructor": "Sarah Johnson",
    "datetime_str": "2025-06-15 18:00",
    "total_slots": 15,
    "timezone_str": "Asia/Kolkata"
  }'
```

## 🌍 Timezone Management

The API handles timezones intelligently:
- **Storage**: All times stored in UTC in the database
- **Input**: Classes created with local time + timezone specification
- **Output**: Times converted to requested timezone for display
- **Default**: Asia/Kolkata (IST) timezone
- **Supported**: Any pytz-compatible timezone string

### Example Timezone Conversion
- **Stored**: `2025-06-10T01:30:00+00:00` (UTC)
- **IST Display**: `2025-06-10 07:00:00 IST`
- **PST Display**: `2025-06-09 17:30:00 PST`

## 🔍 Sample Data

The application comes pre-loaded with sample fitness classes:

| Class | Instructor | Time (IST) | Slots |
|-------|------------|------------|-------|
| Morning Yoga | Priya Sharma | 7:00 AM | 20 |
| Evening Zumba | Rahul Mehta | 7:00 PM | 15 |
| HIIT Training | Arjun Singh | 7:30 AM | 12 |
| Power Yoga | Sneha Patel | 5:30 AM | 18 |

## 🏗️ Architecture & Design

### Project Structure
```
fitness-booking-api/
├── main.py              # Main application file
├── test_main.py         # Comprehensive test suite
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── fitness_studio.db   # SQLite database (auto-created)
└── logs/               # Application logs (auto-created)
```

### Key Design Decisions

1. **FastAPI Framework**: Modern, fast, with automatic API documentation
2. **SQLite Database**: Lightweight, serverless, perfect for development
3. **UTC Storage**: All timestamps stored in UTC for consistency
4. **Pydantic Validation**: Robust request/response validation
5. **Context Managers**: Safe database connection handling
6. **Logging**: Comprehensive logging for debugging and monitoring

### Database Schema

#### Classes Table
```sql
CREATE TABLE classes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    instructor TEXT NOT NULL,
    datetime_utc TEXT NOT NULL,
    timezone TEXT NOT NULL,
    total_slots INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
```

#### Bookings Table
```sql
CREATE TABLE bookings (
    id TEXT PRIMARY KEY,
    class_id TEXT NOT NULL,
    client_name TEXT NOT NULL,
    client_email TEXT NOT NULL,
    booking_time TEXT NOT NULL,
    FOREIGN KEY (class_id) REFERENCES classes (id)
);
```

## 🛡️ Error Handling

The API provides comprehensive error handling:

| Error Code | Description | Example |
|------------|-------------|---------|
| 400 | Bad Request | Invalid datetime format |
| 404 | Not Found | Class doesn't exist |
| 409 | Conflict | Duplicate booking, no slots |
| 422 | Validation Error | Invalid email, missing fields |
| 500 | Server Error | Database connection issues |

### Example Error Response
```json
{
  "detail": "No available slots for this class"
}
```

## 🔒 Security Considerations

- Input validation using Pydantic
- SQL injection prevention with parameterized queries
- Email format validation
- Request size limitations
- Structured error messages (no sensitive data exposure)

## 🚀 Production Deployment

### Environment Variables
```bash
export DATABASE_URL="sqlite:///production.db"
export LOG_LEVEL="INFO"
export API_HOST="0.0.0.0"
export API_PORT="8000"
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Scaling Considerations
- Replace SQLite with PostgreSQL/MySQL for production
- Add Redis for caching frequently accessed data
- Implement rate limiting
- Add authentication/authorization
- Use environment-based configuration

## 📈 Performance Features

- **Efficient Queries**: Optimized database queries with proper indexing
- **Connection Pooling**: Context managers for safe connection handling
- **Minimal Dependencies**: Lightweight with essential packages only
- **Async Support**: FastAPI's async capabilities for concurrent requests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Known Issues & Future Enhancements

### Current Limitations
- SQLite doesn't support concurrent writes well
- No authentication/authorization
- Basic timezone handling (could be more sophisticated)

### Future Enhancements
- [ ] User authentication with JWT
- [ ] Payment integration
- [ ] Email notifications
- [ ] Class capacity waiting lists
- [ ] Recurring class schedules
- [ ] Instructor management
- [ ] Analytics dashboard
- [ ] Mobile app integration

## 📞 Support

For questions or issues:
1. Check the interactive API docs at `/docs`
2. Review the test cases for usage examples
3. Create an issue in the repository
4. Contact: hittusingh350@gmail.com

---

**Built with ❤️ by Hitkarsh**
