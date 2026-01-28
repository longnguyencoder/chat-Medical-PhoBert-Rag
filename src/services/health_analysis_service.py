"""
Health Analysis Service
=======================
Service phân tích hồ sơ sức khỏe và đưa ra lời khuyên cá nhân hóa.

Chức năng:
1. Phân tích BMI và đánh giá tình trạng cân nặng
2. Phân tích bệnh mãn tính và đưa ra lời khuyên
3. Tạo lời khuyên về chế độ ăn uống
4. Tạo lời khuyên về nghỉ ngơi và giấc ngủ
5. Tạo lời khuyên về luyện tập thể dục
6. Tích hợp AI để tạo phân tích tổng hợp
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import OpenAI
from src.models.health_profile import HealthProfile
from src.services.health_profile_service import health_profile_service

logger = logging.getLogger(__name__)

# Khởi tạo OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class HealthAnalysisService:
    """
    Service phân tích sức khỏe và tạo lời khuyên cá nhân hóa.
    """
    
    # Tiêu chuẩn BMI cho người Châu Á (WHO)
    BMI_CATEGORIES = {
        'underweight': {'max': 18.5, 'label': 'Thiếu cân', 'label_en': 'Underweight'},
        'normal': {'min': 18.5, 'max': 23.0, 'label': 'Bình thường', 'label_en': 'Normal'},
        'overweight': {'min': 23.0, 'max': 27.5, 'label': 'Thừa cân', 'label_en': 'Overweight'},
        'obese': {'min': 27.5, 'label': 'Béo phì', 'label_en': 'Obese'}
    }
    
    @staticmethod
    def analyze_bmi(profile: HealthProfile) -> Dict[str, Any]:
        """
        Phân tích BMI và đưa ra đánh giá.
        
        Args:
            profile: HealthProfile object
            
        Returns:
            Dict chứa thông tin phân tích BMI
        """
        bmi = profile.calculate_bmi()
        
        if not bmi:
            return {
                'value': None,
                'category': 'unknown',
                'category_label': 'Chưa có dữ liệu',
                'assessment': 'Vui lòng cập nhật chiều cao và cân nặng để được phân tích BMI.',
                'recommendations': ['Cập nhật chiều cao và cân nặng trong hồ sơ sức khỏe']
            }
        
        # Xác định category
        category = 'unknown'
        category_label = 'Không xác định'
        
        if bmi < HealthAnalysisService.BMI_CATEGORIES['underweight']['max']:
            category = 'underweight'
            category_label = HealthAnalysisService.BMI_CATEGORIES['underweight']['label']
            assessment = f'Chỉ số BMI của bạn là {bmi}, thuộc nhóm thiếu cân. Bạn nên tăng cường dinh dưỡng và tập luyện để cải thiện sức khỏe.'
            recommendations = [
                'Tăng lượng calories hấp thụ hàng ngày',
                'Ăn nhiều bữa nhỏ trong ngày (5-6 bữa)',
                'Bổ sung protein từ thịt, cá, trứng, đậu',
                'Tập luyện sức bền và tăng cơ',
                'Tham khảo ý kiến bác sĩ dinh dưỡng nếu BMI quá thấp'
            ]
        elif bmi < HealthAnalysisService.BMI_CATEGORIES['normal']['max']:
            category = 'normal'
            category_label = HealthAnalysisService.BMI_CATEGORIES['normal']['label']
            assessment = f'Chỉ số BMI của bạn là {bmi}, nằm trong ngưỡng khỏe mạnh. Hãy duy trì lối sống lành mạnh hiện tại!'
            recommendations = [
                'Duy trì chế độ ăn cân bằng',
                'Tập thể dục đều đặn 3-5 lần/tuần',
                'Ngủ đủ 7-8 giờ mỗi ngày',
                'Kiểm tra sức khỏe định kỳ',
                'Giữ cân nặng ổn định'
            ]
        elif bmi < HealthAnalysisService.BMI_CATEGORIES['overweight']['max']:
            category = 'overweight'
            category_label = HealthAnalysisService.BMI_CATEGORIES['overweight']['label']
            assessment = f'Chỉ số BMI của bạn là {bmi}, thuộc nhóm thừa cân. Bạn nên điều chỉnh chế độ ăn uống và tăng cường vận động.'
            recommendations = [
                'Giảm lượng calories hấp thụ hàng ngày (giảm 300-500 kcal)',
                'Hạn chế đồ ngọt, đồ chiên rán, thức ăn nhanh',
                'Tăng rau xanh và trái cây trong bữa ăn',
                'Tập cardio 30-45 phút, 4-5 lần/tuần',
                'Theo dõi cân nặng hàng tuần'
            ]
        else:
            category = 'obese'
            category_label = HealthAnalysisService.BMI_CATEGORIES['obese']['label']
            assessment = f'Chỉ số BMI của bạn là {bmi}, thuộc nhóm béo phì. Bạn nên tham khảo ý kiến bác sĩ để có kế hoạch giảm cân an toàn.'
            recommendations = [
                '⚠️ Tham khảo ý kiến bác sĩ hoặc chuyên gia dinh dưỡng',
                'Giảm cân từ từ (0.5-1kg/tuần)',
                'Thay đổi thói quen ăn uống lâu dài',
                'Bắt đầu với vận động nhẹ, tăng dần cường độ',
                'Kiểm tra các chỉ số sức khỏe khác (đường huyết, huyết áp, mỡ máu)',
                'Có thể cần hỗ trợ tâm lý trong quá trình giảm cân'
            ]
        
        return {
            'value': bmi,
            'category': category,
            'category_label': category_label,
            'assessment': assessment,
            'recommendations': recommendations
        }
    
    @staticmethod
    def analyze_chronic_conditions(profile: HealthProfile) -> List[Dict[str, Any]]:
        """
        Phân tích bệnh mãn tính và đưa ra lời khuyên.
        
        Args:
            profile: HealthProfile object
            
        Returns:
            List các bệnh mãn tính và lời khuyên tương ứng
        """
        conditions = profile.get_chronic_conditions_list()
        
        if not conditions:
            return []
        
        # Mapping bệnh mãn tính với lời khuyên
        condition_advice = {
            'diabetes': {
                'keywords': ['tiểu đường', 'diabetes', 'đái tháo đường'],
                'diet': [
                    'Hạn chế đường và tinh bột tinh chế',
                    'Ăn nhiều rau xanh, ngũ cốc nguyên hạt',
                    'Kiểm soát lượng carbohydrate trong mỗi bữa',
                    'Ăn nhiều bữa nhỏ trong ngày',
                    'Tránh đồ uống có đường'
                ],
                'exercise': [
                    'Tập thể dục đều đặn giúp kiểm soát đường huyết',
                    'Đi bộ 30 phút sau bữa ăn',
                    'Kết hợp cardio và tập tạ'
                ],
                'monitoring': ['Theo dõi đường huyết thường xuyên', 'Uống thuốc đúng giờ']
            },
            'hypertension': {
                'keywords': ['cao huyết áp', 'hypertension', 'huyết áp cao'],
                'diet': [
                    'Hạn chế muối (< 5g/ngày)',
                    'Tránh đồ ăn mặn, đồ chế biến sẵn',
                    'Ăn nhiều rau củ, trái cây giàu kali',
                    'Hạn chế caffeine và rượu bia',
                    'Tăng cường thực phẩm giàu magie'
                ],
                'exercise': [
                    'Tập cardio nhẹ nhàng (đi bộ, bơi lội)',
                    'Tránh tập quá sức',
                    'Thở sâu và yoga để giảm stress'
                ],
                'monitoring': ['Đo huyết áp hàng ngày', 'Kiểm tra sức khỏe định kỳ']
            },
            'heart_disease': {
                'keywords': ['tim mạch', 'heart', 'cardiac', 'mạch vành'],
                'diet': [
                    'Hạn chế chất béo bão hòa và trans fat',
                    'Ăn cá giàu omega-3 (cá hồi, cá thu)',
                    'Tăng chất xơ từ rau củ và ngũ cốc',
                    'Hạn chế cholesterol'
                ],
                'exercise': [
                    'Tập luyện nhẹ nhàng theo chỉ định bác sĩ',
                    'Tránh vận động quá sức',
                    'Theo dõi nhịp tim khi tập'
                ],
                'monitoring': ['Khám tim định kỳ', 'Uống thuốc đúng giờ']
            },
            'asthma': {
                'keywords': ['hen suyễn', 'asthma', 'khó thở'],
                'diet': [
                    'Tránh thực phẩm gây dị ứng',
                    'Bổ sung vitamin D',
                    'Ăn nhiều rau củ quả giàu chất chống oxi hóa'
                ],
                'exercise': [
                    'Khởi động kỹ trước khi tập',
                    'Tránh tập trong môi trường lạnh, khô',
                    'Luôn mang theo thuốc xịt'
                ],
                'monitoring': ['Theo dõi triệu chứng', 'Tránh các yếu tố kích thích']
            }
        }
        
        analysis = []
        
        for condition in conditions:
            condition_lower = condition.lower()
            matched = False
            
            for key, advice in condition_advice.items():
                if any(keyword in condition_lower for keyword in advice['keywords']):
                    analysis.append({
                        'condition': condition,
                        'type': key,
                        'diet_recommendations': advice['diet'],
                        'exercise_recommendations': advice['exercise'],
                        'monitoring': advice['monitoring']
                    })
                    matched = True
                    break
            
            if not matched:
                # Bệnh không có trong danh sách, đưa ra lời khuyên chung
                analysis.append({
                    'condition': condition,
                    'type': 'general',
                    'diet_recommendations': ['Chế độ ăn cân bằng, đa dạng dinh dưỡng'],
                    'exercise_recommendations': ['Tập luyện phù hợp với tình trạng sức khỏe'],
                    'monitoring': ['Tham khảo ý kiến bác sĩ chuyên khoa']
                })
        
        return analysis
    
    @staticmethod
    def generate_diet_recommendations(profile: HealthProfile) -> Dict[str, Any]:
        """
        Tạo lời khuyên về chế độ ăn uống dựa trên hồ sơ sức khỏe.
        
        Args:
            profile: HealthProfile object
            
        Returns:
            Dict chứa lời khuyên về chế độ ăn
        """
        recommendations = []
        foods_to_avoid = []
        foods_to_include = []
        
        # 1. Dựa trên BMI
        bmi_analysis = HealthAnalysisService.analyze_bmi(profile)
        category = bmi_analysis['category']
        
        if category == 'underweight':
            recommendations.extend([
                'Tăng lượng calories hấp thụ (thêm 300-500 kcal/ngày)',
                'Ăn nhiều bữa nhỏ trong ngày (5-6 bữa)',
                'Bổ sung protein chất lượng cao'
            ])
            foods_to_include.extend(['Thịt nạc', 'Cá', 'Trứng', 'Sữa', 'Các loại hạt', 'Bơ', 'Ngũ cốc nguyên hạt'])
            
        elif category == 'overweight' or category == 'obese':
            recommendations.extend([
                'Giảm lượng calories (giảm 300-500 kcal/ngày)',
                'Kiểm soát khẩu phần ăn',
                'Tăng rau xanh, giảm tinh bột'
            ])
            foods_to_avoid.extend(['Đồ ngọt', 'Đồ chiên rán', 'Thức ăn nhanh', 'Nước ngọt có ga', 'Bánh kẹo'])
            foods_to_include.extend(['Rau xanh', 'Trái cây', 'Thịt nạc', 'Cá', 'Ngũ cốc nguyên hạt'])
        
        # 2. Dựa trên dị ứng
        allergies = profile.get_allergies_list()
        if allergies:
            foods_to_avoid.extend(allergies)
            recommendations.append(f'⚠️ TUYỆT ĐỐI TRÁNH: {", ".join(allergies)} (dị ứng)')
        
        # 3. Dựa trên bệnh mãn tính
        chronic_analysis = HealthAnalysisService.analyze_chronic_conditions(profile)
        for condition in chronic_analysis:
            if condition['diet_recommendations']:
                recommendations.extend(condition['diet_recommendations'][:2])  # Lấy 2 lời khuyên quan trọng nhất
        
        # 4. Lời khuyên chung
        general_recommendations = [
            'Uống đủ nước (2-2.5 lít/ngày)',
            'Ăn đủ 3 bữa chính, tránh bỏ bữa',
            'Hạn chế đồ ăn chế biến sẵn',
            'Tăng cường rau xanh và trái cây',
            'Ăn chậm, nhai kỹ'
        ]
        
        # Tạo summary
        summary = f"Chế độ ăn uống được thiết kế dựa trên BMI ({bmi_analysis['category_label']})"
        if allergies:
            summary += f", dị ứng với {', '.join(allergies)}"
        if chronic_analysis:
            conditions_str = ', '.join([c['condition'] for c in chronic_analysis])
            summary += f", và tình trạng sức khỏe ({conditions_str})"
        summary += "."
        
        return {
            'summary': summary,
            'recommendations': list(set(recommendations + general_recommendations[:3])),  # Loại bỏ trùng lặp
            'foods_to_avoid': list(set(foods_to_avoid)),
            'foods_to_include': list(set(foods_to_include))
        }
    
    @staticmethod
    def generate_rest_recommendations(profile: HealthProfile) -> Dict[str, Any]:
        """
        Tạo lời khuyên về nghỉ ngơi và giấc ngủ.
        
        Args:
            profile: HealthProfile object
            
        Returns:
            Dict chứa lời khuyên về nghỉ ngơi
        """
        age = profile.calculate_age()
        
        # Khuyến nghị số giờ ngủ theo độ tuổi
        if age is None:
            sleep_hours = "7-9 giờ/ngày"
            age_group = "người trưởng thành"
        elif age < 18:
            sleep_hours = "8-10 giờ/ngày"
            age_group = "thanh thiếu niên"
        elif age < 65:
            sleep_hours = "7-9 giờ/ngày"
            age_group = "người trưởng thành"
        else:
            sleep_hours = "7-8 giờ/ngày"
            age_group = "người cao tuổi"
        
        recommendations = [
            f'Ngủ đủ {sleep_hours} (khuyến nghị cho {age_group})',
            'Đi ngủ và thức dậy đúng giờ mỗi ngày',
            'Tránh sử dụng điện thoại, máy tính trước khi ngủ 1 giờ',
            'Tạo môi trường ngủ thoải mái (tối, mát, yên tĩnh)',
            'Tránh caffeine sau 2 giờ chiều',
            'Thư giãn trước khi ngủ (đọc sách, nghe nhạc nhẹ)',
            'Ngủ trưa 15-30 phút nếu cần thiết'
        ]
        
        # Lời khuyên dựa trên bệnh mãn tính
        chronic_conditions = profile.get_chronic_conditions_list()
        if chronic_conditions:
            for condition in chronic_conditions:
                condition_lower = condition.lower()
                if 'stress' in condition_lower or 'lo âu' in condition_lower or 'anxiety' in condition_lower:
                    recommendations.extend([
                        'Thực hành thiền hoặc yoga trước khi ngủ',
                        'Ghi chép suy nghĩ để giảm lo âu'
                    ])
                    break
        
        return {
            'sleep_hours': sleep_hours,
            'age_group': age_group,
            'recommendations': recommendations
        }
    
    @staticmethod
    def generate_exercise_recommendations(profile: HealthProfile) -> Dict[str, Any]:
        """
        Tạo lời khuyên về luyện tập thể dục.
        
        Args:
            profile: HealthProfile object
            
        Returns:
            Dict chứa lời khuyên về tập luyện
        """
        age = profile.calculate_age()
        bmi_analysis = HealthAnalysisService.analyze_bmi(profile)
        category = bmi_analysis['category']
        
        # Khuyến nghị cơ bản
        frequency = "3-5 lần/tuần"
        duration = "30-45 phút/lần"
        types = []
        recommendations = []
        
        # Dựa trên BMI
        if category == 'underweight':
            types = ['Tập tạ (strength training)', 'Yoga', 'Pilates', 'Bơi lội']
            recommendations.extend([
                'Tập trung vào tăng cơ, không nên cardio quá nhiều',
                'Tập tạ 3-4 lần/tuần',
                'Nghỉ ngơi đủ giữa các buổi tập'
            ])
        elif category == 'normal':
            types = ['Cardio (chạy bộ, đạp xe)', 'Tập tạ', 'Bơi lội', 'Yoga', 'Thể thao đồng đội']
            recommendations.extend([
                'Kết hợp cardio và strength training',
                'Duy trì thói quen tập luyện đều đặn',
                'Thử các môn thể thao mới để không nhàm chán'
            ])
        elif category == 'overweight' or category == 'obese':
            types = ['Đi bộ nhanh', 'Bơi lội', 'Đạp xe', 'Aerobic nhẹ', 'Yoga']
            duration = "45-60 phút/lần"
            frequency = "4-6 lần/tuần"
            recommendations.extend([
                'Bắt đầu với cường độ nhẹ, tăng dần',
                'Ưu tiên cardio để đốt cháy calories',
                'Tập trong nước (bơi lội, aqua aerobic) để giảm áp lực lên khớp',
                'Kết hợp với chế độ ăn để giảm cân hiệu quả'
            ])
        
        # Dựa trên tuổi
        if age and age > 60:
            types = ['Đi bộ', 'Yoga', 'Tai chi', 'Bơi lội', 'Tập duỗi cơ']
            recommendations.extend([
                'Tập nhẹ nhàng, tránh chấn thương',
                'Tập cân bằng để phòng ngừa té ngã',
                'Khởi động kỹ trước khi tập'
            ])
        
        # Dựa trên bệnh mãn tính
        chronic_analysis = HealthAnalysisService.analyze_chronic_conditions(profile)
        for condition in chronic_analysis:
            if condition['exercise_recommendations']:
                recommendations.extend(condition['exercise_recommendations'][:2])
        
        # Lời khuyên chung
        general_tips = [
            'Khởi động 5-10 phút trước khi tập',
            'Giãn cơ sau khi tập',
            'Uống đủ nước trong khi tập',
            'Lắng nghe cơ thể, nghỉ ngơi khi cần',
            'Tăng cường độ từ từ theo thời gian'
        ]
        
        return {
            'frequency': frequency,
            'duration': duration,
            'types': types,
            'recommendations': list(set(recommendations + general_tips[:3]))
        }
    
    @staticmethod
    def generate_comprehensive_analysis(user_id: int) -> Dict[str, Any]:
        """
        Tạo phân tích tổng hợp với AI.
        
        Args:
            user_id: ID người dùng
            
        Returns:
            Dict chứa phân tích tổng hợp
        """
        try:
            # Lấy hồ sơ sức khỏe
            profile = health_profile_service.get_profile(user_id)
            
            if not profile:
                return {
                    'success': False,
                    'message': 'Chưa có hồ sơ sức khỏe. Vui lòng cập nhật hồ sơ để được phân tích.',
                    'ai_insights': None
                }
            
            # Tạo context cho AI
            age = profile.calculate_age()
            bmi = profile.calculate_bmi()
            gender = profile.gender or 'Không xác định'
            allergies = profile.get_allergies_list()
            chronic_conditions = profile.get_chronic_conditions_list()
            medications = profile.get_medications_list()
            
            context = f"""
Hồ sơ sức khỏe:
- Tuổi: {age if age else 'Chưa cập nhật'}
- Giới tính: {gender}
- Chiều cao: {profile.height if profile.height else 'Chưa cập nhật'} cm
- Cân nặng: {profile.weight if profile.weight else 'Chưa cập nhật'} kg
- BMI: {bmi if bmi else 'Chưa có dữ liệu'}
- Dị ứng: {', '.join(allergies) if allergies else 'Không có'}
- Bệnh mãn tính: {', '.join(chronic_conditions) if chronic_conditions else 'Không có'}
- Thuốc đang dùng: {', '.join(medications) if medications else 'Không có'}
- Tiền sử gia đình: {profile.family_history if profile.family_history else 'Không có'}
"""
            
            # Gọi AI để phân tích
            prompt = f"""Bạn là bác sĩ gia đình với 15 năm kinh nghiệm, chuyên tư vấn sức khỏe cho người Việt Nam.

Hãy phân tích hồ sơ sức khỏe sau và đưa ra lời khuyên TOÀN DIỆN, CÁ NHÂN HÓA về:
1. Đánh giá tổng quan tình trạng sức khỏe
2. Chế độ ăn uống cụ thể (nên ăn gì, tránh gì)
3. Chế độ nghỉ ngơi và giấc ngủ
4. Luyện tập thể dục phù hợp
5. Các lưu ý đặc biệt (nếu có bệnh mãn tính hoặc dị ứng)

{context}

YÊU CẦU:
- Lời khuyên phải CỤ THỂ, DỄ THỰC HIỆN cho người Việt Nam
- Ưu tiên AN TOÀN, phù hợp với tình trạng sức khỏe hiện tại
- Nếu có bệnh mãn tính hoặc dị ứng, phải LƯU Ý RÕ RÀNG
- Sử dụng ngôn ngữ thân thiện, dễ hiểu
- Độ dài: 300-400 từ

⚠️ QUAN TRỌNG: Kết thúc bằng disclaimer: "Lời khuyên trên chỉ mang tính chất tham khảo. Vui lòng tham khảo ý kiến bác sĩ chuyên khoa để được tư vấn chính xác."
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Bạn là bác sĩ gia đình chuyên nghiệp, tư vấn sức khỏe cho người Việt Nam."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            ai_insights = response.choices[0].message.content.strip()
            
            logger.info(f"Generated comprehensive analysis for user {user_id}")
            
            return {
                'success': True,
                'ai_insights': ai_insights,
                'profile_summary': {
                    'age': age,
                    'gender': gender,
                    'bmi': bmi,
                    'has_allergies': len(allergies) > 0,
                    'has_chronic_conditions': len(chronic_conditions) > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive analysis: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Không thể tạo phân tích: {str(e)}',
                'ai_insights': None
            }


# Tạo singleton instance
health_analysis_service = HealthAnalysisService()
