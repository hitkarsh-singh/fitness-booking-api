import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import sqlite3

# Import our main application
from main import app, DatabaseManager, db_manager

client = TestClient(app)

class TestFitnessBookingAPI:
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Setup a fresh test database for each test"""
        # Create a temporary database file
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Replace the global db_manager with a test one
        global db_manager
        db_manager = DatabaseManager(self.test_db.name)
        
        yield
        
        # Cleanup
        os.unlink(self.test_db.name)
    
    def test_health_check(self):
        """Test the root endpoint for health check"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Fitness Studio Booking API is running!"
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_get_classes(self):
        """Test retrieving all classes"""
        response = client.get("/classes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check first class structure
        first_class = data[0]
        required_fields = ['id', 'name', 'instructor', 'datetime_utc', 'datetime_local', 
                          'timezone', 'total_slots', 'available_slots', 'booked_slots']
        for field in required_fields:
            assert field in first_class
    
    def test_get_classes_with_timezone(self):
        """Test retrieving classes with different timezone"""
        response = client.get("/classes?timezone_str=US/Pacific")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # Check that timezone is correctly set
        first_class = data[0]
        assert first_class['timezone'] == 'US/Pacific'
        assert 'PST' in first_class['datetime_local'] or 'PDT' in first_class['datetime_local']
    
    def test_book_class_success(self):
        """Test successful class booking"""
        # First get available classes
        classes_response = client.get("/classes")
        classes = classes_response.json()
        assert len(classes) > 0
        
        class_id = classes[0]['id']
        
        booking_data = {
            "class_id": class_id,
            "client_name": "John Doe",
            "client_email": "john.doe@example.com"
        }
        
        response = client.post("/book", json=booking_data)
        assert response.status_code == 200
        
        booking = response.json()
        assert booking['class_id'] == class_id
        assert booking['client_name'] == "John Doe"
        assert booking['client_email'] == "john.doe@example.com"
        assert 'id' in booking
        assert 'booking_time' in booking
    
    def test_book_nonexistent_class(self):
        """Test booking a non-existent class"""
        booking_data = {
            "class_id": "non-existent-id",
            "client_name": "John Doe",
            "client_email": "john.doe@example.com"
        }
        
        response = client.post("/book", json=booking_data)
        assert response.status_code == 404
        assert "Class not found" in response.json()['detail']
    
    def test_duplicate_booking(self):
        """Test preventing duplicate bookings"""
        # Get a class
        classes_response = client.get("/classes")
        classes = classes_response.json()
        class_id = classes[0]['id']
        
        booking_data = {
            "class_id": class_id,
            "client_name": "Jane Smith",
            "client_email": "jane.smith@example.com"
        }
        
        # First booking should succeed
        response1 = client.post("/book", json=booking_data)
        assert response1.status_code == 200
        
        # Second booking with same email should fail
        response2 = client.post("/book", json=booking_data)
        assert response2.status_code == 409
        assert "already booked" in response2.json()['detail']
    
    def test_booking_validation(self):
        """Test booking request validation"""
        # Missing required fields
        response = client.post("/book", json={})
        assert response.status_code == 422
        
        # Invalid email
        invalid_booking = {
            "class_id": "some-id",
            "client_name": "John Doe",
            "client_email": "invalid-email"
        }
        response = client.post("/book", json=invalid_booking)
        assert response.status_code == 422
        
        # Empty name
        invalid_booking = {
            "class_id": "some-id",
            "client_name": "",
            "client_email": "valid@example.com"
        }
        response = client.post("/book", json=invalid_booking)
        assert response.status_code == 422
    
    def test_get_bookings(self):
        """Test retrieving bookings for a user"""
        # First make a booking
        classes_response = client.get("/classes")
        classes = classes_response.json()
        class_id = classes[0]['id']
        
        booking_data = {
            "class_id": class_id,
            "client_name": "Alice Johnson",
            "client_email": "alice.johnson@example.com"
        }
        
        booking_response = client.post("/book", json=booking_data)
        assert booking_response.status_code == 200
        
        # Now get bookings for this user
        response = client.get("/bookings?email=alice.johnson@example.com")
        assert response.status_code == 200
        
        bookings = response.json()
        assert len(bookings) == 1
        assert bookings[0]['client_email'] == "alice.johnson@example.com"
        assert bookings[0]['class_id'] == class_id
    
    def test_get_bookings_empty(self):
        """Test retrieving bookings for user with no bookings"""
        response = client.get("/bookings?email=nonexistent@example.com")
        assert response.status_code == 200
        
        bookings = response.json()
        assert len(bookings) == 0
    
    def test_class_slots_decrease_after_booking(self):
        """Test that available slots decrease after booking"""
        # Get initial class state
        classes_response = client.get("/classes")
        classes = classes_response.json()
        initial_class = classes[0]
        initial_available_slots = initial_class['available_slots']
        class_id = initial_class['id']
        
        # Make a booking
        booking_data = {
            "class_id": class_id,
            "client_name": "Bob Wilson",
            "client_email": "bob.wilson@example.com"
        }
        
        booking_response = client.post("/book", json=booking_data)
        assert booking_response.status_code == 200
        
        # Check updated class state
        classes_response = client.get("/classes")
        classes = classes_response.json()
        updated_class = next(c for c in classes if c['id'] == class_id)
        
        assert updated_class['available_slots'] == initial_available_slots - 1
        assert updated_class['booked_slots'] == initial_class['booked_slots'] + 1
    
    def test_create_class(self):
        """Test creating a new class"""
        class_data = {
            "name": "Test Pilates",
            "instructor": "Test Instructor",
            "datetime_str": "2025-12-31 10:00",
            "total_slots": 25,
            "timezone_str": "Asia/Kolkata"
        }
        
        response = client.post("/classes", json=class_data)
        assert response.status_code == 200
        
        new_class = response.json()
        assert new_class['name'] == "Test Pilates"
        assert new_class['instructor'] == "Test Instructor"
        assert new_class['total_slots'] == 25
        assert new_class['available_slots'] == 25
        assert new_class['booked_slots'] == 0
        assert 'id' in new_class
    
    def test_create_class_in_past(self):
        """Test creating a class in the past should fail"""
        class_data = {
            "name": "Past Class",
            "instructor": "Test Instructor",
            "datetime_str": "2020-01-01 10:00",
            "total_slots": 20,
            "timezone_str": "Asia/Kolkata"
        }
        
        response = client.post("/classes", json=class_data)
        assert response.status_code == 400
        assert "future" in response.json()['detail']
    
    def test_class_creation_validation(self):
        """Test class creation validation"""
        # Empty name
        invalid_class = {
            "name": "",
            "instructor": "Test Instructor",
            "datetime_str": "2025-12-31 10:00",
            "total_slots": 20
        }
        response = client.post("/classes", json=invalid_class)
        assert response.status_code == 422
        
        # Invalid slots
        invalid_class = {
            "name": "Test Class",
            "instructor": "Test Instructor",
            "datetime_str": "2025-12-31 10:00",
            "total_slots": 0
        }
        response = client.post("/classes", json=invalid_class)
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v"])