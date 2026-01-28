"""
Test Script for Health Analysis Feature
========================================
Script để test các chức năng phân tích sức khỏe.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.health_analysis_service import health_analysis_service
from src.services.health_profile_service import health_profile_service
from src.models.health_profile import HealthProfile
from datetime import datetime, date


def test_bmi_analysis():
    """Test BMI analysis với các trường hợp khác nhau"""
    print("\n" + "="*60)
    print("TEST 1: BMI ANALYSIS")
    print("="*60)
    
    # Tạo mock profile
    class MockProfile:
        def __init__(self, height, weight):
            self.height = height
            self.weight = weight
            self.allergies = None
            self.chronic_conditions = None
            self.medications = None
            
        def calculate_bmi(self):
            if not self.height or not self.weight:
                return None
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 2)
        
        def get_allergies_list(self):
            return []
        
        def get_chronic_conditions_list(self):
            return []
        
        def get_medications_list(self):
            return []
    
    # Test cases
    test_cases = [
        {"name": "Thiếu cân", "height": 170, "weight": 50},
        {"name": "Bình thường", "height": 170, "weight": 65},
        {"name": "Thừa cân", "height": 170, "weight": 75},
        {"name": "Béo phì", "height": 170, "weight": 90}
    ]
    
    for case in test_cases:
        profile = MockProfile(case['height'], case['weight'])
        result = health_analysis_service.analyze_bmi(profile)
        
        print(f"\n{case['name']}:")
        print(f"  BMI: {result['value']}")
        print(f"  Phân loại: {result['category_label']}")
        print(f"  Đánh giá: {result['assessment']}")
        print(f"  Số lời khuyên: {len(result['recommendations'])}")


def test_chronic_conditions_analysis():
    """Test phân tích bệnh mãn tính"""
    print("\n" + "="*60)
    print("TEST 2: CHRONIC CONDITIONS ANALYSIS")
    print("="*60)
    
    class MockProfile:
        def __init__(self, conditions):
            self.chronic_conditions = conditions
            self.height = 170
            self.weight = 65
            self.allergies = None
            self.medications = None
            
        def calculate_bmi(self):
            return 22.5
        
        def get_allergies_list(self):
            return []
        
        def get_chronic_conditions_list(self):
            import json
            if not self.chronic_conditions:
                return []
            try:
                return json.loads(self.chronic_conditions)
            except:
                return []
        
        def get_medications_list(self):
            return []
    
    # Test với tiểu đường
    import json
    profile = MockProfile(json.dumps(["Tiểu đường type 2", "Cao huyết áp"]))
    result = health_analysis_service.analyze_chronic_conditions(profile)
    
    print(f"\nSố bệnh phát hiện: {len(result)}")
    for condition in result:
        print(f"\n  Bệnh: {condition['condition']}")
        print(f"  Loại: {condition['type']}")
        print(f"  Lời khuyên ăn uống: {len(condition['diet_recommendations'])} mục")
        print(f"  Lời khuyên tập luyện: {len(condition['exercise_recommendations'])} mục")


def test_diet_recommendations():
    """Test lời khuyên về chế độ ăn"""
    print("\n" + "="*60)
    print("TEST 3: DIET RECOMMENDATIONS")
    print("="*60)
    
    class MockProfile:
        def __init__(self, bmi_category, allergies=None):
            self.height = 170
            self.weight = 90 if bmi_category == 'obese' else 65
            self.allergies = allergies
            self.chronic_conditions = None
            self.medications = None
            
        def calculate_bmi(self):
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 2)
        
        def get_allergies_list(self):
            import json
            if not self.allergies:
                return []
            try:
                return json.loads(self.allergies)
            except:
                return []
        
        def get_chronic_conditions_list(self):
            return []
        
        def get_medications_list(self):
            return []
    
    # Test với người béo phì + dị ứng hải sản
    import json
    profile = MockProfile('obese', json.dumps(["Hải sản", "Lạc"]))
    result = health_analysis_service.generate_diet_recommendations(profile)
    
    print(f"\nTóm tắt: {result['summary']}")
    print(f"\nSố lời khuyên: {len(result['recommendations'])}")
    print(f"Thực phẩm nên tránh: {', '.join(result['foods_to_avoid'])}")
    print(f"Thực phẩm nên ăn: {', '.join(result['foods_to_include'][:3])}...")


def test_exercise_recommendations():
    """Test lời khuyên về tập luyện"""
    print("\n" + "="*60)
    print("TEST 4: EXERCISE RECOMMENDATIONS")
    print("="*60)
    
    class MockProfile:
        def __init__(self, age, bmi_category):
            self.date_of_birth = date(2024 - age, 1, 1)
            self.height = 170
            self.weight = 90 if bmi_category == 'obese' else 65
            self.allergies = None
            self.chronic_conditions = None
            self.medications = None
            
        def calculate_age(self):
            today = datetime.utcnow().date()
            age = today.year - self.date_of_birth.year
            if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
                age -= 1
            return age
        
        def calculate_bmi(self):
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 2)
        
        def get_allergies_list(self):
            return []
        
        def get_chronic_conditions_list(self):
            return []
        
        def get_medications_list(self):
            return []
    
    # Test với người 65 tuổi, béo phì
    profile = MockProfile(65, 'obese')
    result = health_analysis_service.generate_exercise_recommendations(profile)
    
    print(f"\nTần suất: {result['frequency']}")
    print(f"Thời lượng: {result['duration']}")
    print(f"Các loại hình: {', '.join(result['types'])}")
    print(f"Số lời khuyên: {len(result['recommendations'])}")


def test_rest_recommendations():
    """Test lời khuyên về nghỉ ngơi"""
    print("\n" + "="*60)
    print("TEST 5: REST RECOMMENDATIONS")
    print("="*60)
    
    class MockProfile:
        def __init__(self, age):
            self.date_of_birth = date(2024 - age, 1, 1)
            self.height = 170
            self.weight = 65
            self.allergies = None
            self.chronic_conditions = None
            self.medications = None
            
        def calculate_age(self):
            today = datetime.utcnow().date()
            age = today.year - self.date_of_birth.year
            if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
                age -= 1
            return age
        
        def calculate_bmi(self):
            return 22.5
        
        def get_allergies_list(self):
            return []
        
        def get_chronic_conditions_list(self):
            return []
        
        def get_medications_list(self):
            return []
    
    # Test với người 30 tuổi
    profile = MockProfile(30)
    result = health_analysis_service.generate_rest_recommendations(profile)
    
    print(f"\nSố giờ ngủ khuyến nghị: {result['sleep_hours']}")
    print(f"Nhóm tuổi: {result['age_group']}")
    print(f"Số lời khuyên: {len(result['recommendations'])}")
    print(f"Lời khuyên đầu tiên: {result['recommendations'][0]}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("HEALTH ANALYSIS SERVICE - TEST SUITE")
    print("="*60)
    
    try:
        test_bmi_analysis()
        test_chronic_conditions_analysis()
        test_diet_recommendations()
        test_exercise_recommendations()
        test_rest_recommendations()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
