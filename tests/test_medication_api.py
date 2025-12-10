"""
Test Medication API
===================
Test script để kiểm tra các API endpoints của medication feature.

Chạy script này để test:
- Tạo lịch uống thuốc
- Lấy danh sách lịch
- Cập nhật lịch
- Ghi nhận đã uống/bỏ qua
- Thống kê tuân thủ
"""

import requests
import json
from datetime import datetime, timedelta

# Base URL
BASE_URL = "http://localhost:5000/api"

# Test user credentials (cần đăng ký trước)
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Test123456"

def login():
    """Đăng nhập và lấy JWT token"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print(f"✅ Login successful! Token: {token[:20]}...")
        return token
    else:
        print(f"❌ Login failed: {response.json()}")
        return None

def test_create_schedule(token):
    """Test tạo lịch uống thuốc"""
    print("\n📝 Testing: Create medication schedule...")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "medication_name": "Paracetamol",
        "dosage": "500mg",
        "frequency": "twice_daily",
        "time_of_day": ["08:00", "20:00"],
        "start_date": datetime.now().strftime('%Y-%m-%d'),
        "notes": "Uống sau ăn"
    }
    
    response = requests.post(
        f"{BASE_URL}/medication/schedules",
        headers=headers,
        json=data
    )
    
    if response.status_code == 201:
        schedule = response.json()['schedule']
        print(f"✅ Schedule created! ID: {schedule['schedule_id']}")
        return schedule['schedule_id']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def test_get_schedules(token):
    """Test lấy danh sách lịch"""
    print("\n📋 Testing: Get medication schedules...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/medication/schedules",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} schedules")
        for schedule in data['schedules']:
            print(f"   - {schedule['medication_name']} ({schedule['dosage']})")
    else:
        print(f"❌ Failed: {response.json()}")

def test_get_logs(token):
    """Test lấy lịch sử"""
    print("\n📊 Testing: Get medication logs...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/medication/logs",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} logs")
        for log in data['logs'][:5]:  # Hiển thị 5 logs đầu
            print(f"   - {log['scheduled_time']}: {log['status']}")
    else:
        print(f"❌ Failed: {response.json()}")

def test_record_medication(token, log_id):
    """Test ghi nhận đã uống thuốc"""
    print(f"\n💊 Testing: Record medication taken (log_id={log_id})...")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "log_id": log_id,
        "status": "taken",
        "note": "Uống đúng giờ"
    }
    
    response = requests.post(
        f"{BASE_URL}/medication/logs",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        print(f"✅ Medication marked as taken!")
    else:
        print(f"❌ Failed: {response.json()}")

def test_get_stats(token):
    """Test thống kê tuân thủ"""
    print("\n📈 Testing: Get compliance stats...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/medication/logs/stats?days=30",
        headers=headers
    )
    
    if response.status_code == 200:
        stats = response.json()['stats']
        print(f"✅ Compliance Stats (30 days):")
        print(f"   Total: {stats['total']}")
        print(f"   Taken: {stats['taken']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Pending: {stats['pending']}")
        print(f"   Compliance Rate: {stats['compliance_rate']}%")
    else:
        print(f"❌ Failed: {response.json()}")

def main():
    """Chạy tất cả tests"""
    print("=" * 60)
    print("🧪 MEDICATION API TEST SUITE")
    print("=" * 60)
    
    # 1. Login
    token = login()
    if not token:
        print("\n❌ Cannot proceed without login token")
        return
    
    # 2. Tạo lịch
    schedule_id = test_create_schedule(token)
    
    # 3. Lấy danh sách lịch
    test_get_schedules(token)
    
    # 4. Lấy lịch sử logs
    test_get_logs(token)
    
    # 5. Thống kê
    test_get_stats(token)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == '__main__':
    main()
