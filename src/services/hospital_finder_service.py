"""
Hospital Finder Service - OpenStreetMap Edition
================================================
Service tìm kiếm bệnh viện gần vị trí người dùng sử dụng OpenStreetMap (Nominatim).

✅ HOÀN TOÀN MIỄN PHÍ - Không cần API key
✅ Không giới hạn requests (chỉ cần tuân thủ rate limit: 1 request/giây)
✅ Dữ liệu mở từ cộng đồng

Tính năng:
- Tìm bệnh viện trong bán kính nhất định
- Lọc theo chuyên khoa
- Tính khoảng cách từ vị trí user
- Lấy thông tin cơ bản (tên, địa chỉ, tọa độ)

API sử dụng:
- Overpass API (OpenStreetMap query engine)
- Haversine formula để tính khoảng cách
"""

import requests
import logging
from math import radians, cos, sin, asin, sqrt
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)


class HospitalFinderService:
    """
    Service tìm kiếm bệnh viện sử dụng OpenStreetMap (100% miễn phí).
    """
    
    # Overpass API endpoint (OpenStreetMap query engine)
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    # Nominatim API (for geocoding - backup)
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    
    # Rate limiting: 1 request/giây để tôn trọng server
    LAST_REQUEST_TIME = 0
    MIN_REQUEST_INTERVAL = 1.0  # seconds
    
    @staticmethod
    def _rate_limit():
        """
        Rate limiting để tuân thủ quy định của OpenStreetMap.
        Đảm bảo tối thiểu 1 giây giữa các requests.
        """
        current_time = time.time()
        time_since_last = current_time - HospitalFinderService.LAST_REQUEST_TIME
        
        if time_since_last < HospitalFinderService.MIN_REQUEST_INTERVAL:
            sleep_time = HospitalFinderService.MIN_REQUEST_INTERVAL - time_since_last
            time.sleep(sleep_time)
        
        HospitalFinderService.LAST_REQUEST_TIME = time.time()
    
    @staticmethod
    def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Tính khoảng cách giữa 2 điểm GPS sử dụng công thức Haversine.
        
        Args:
            lat1, lng1: Vĩ độ, kinh độ điểm 1
            lat2, lng2: Vĩ độ, kinh độ điểm 2
            
        Returns:
            Khoảng cách tính bằng km
            
        Example:
            >>> calculate_distance(10.762622, 106.660172, 10.776889, 106.700806)
            4.23  # km
        """
        # Chuyển độ sang radian
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        
        # Công thức Haversine
        dlng = lng2 - lng1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * asin(sqrt(a))
        
        # Bán kính trái đất = 6371 km
        km = 6371 * c
        return round(km, 2)
    
    def find_nearby_hospitals(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5000,
        specialty: Optional[str] = None,
        limit: int = 5
    ) -> Dict:
        """
        Tìm bệnh viện gần vị trí người dùng sử dụng OpenStreetMap.
        
        Args:
            latitude: Vĩ độ (VD: 10.762622 cho TP.HCM)
            longitude: Kinh độ (VD: 106.660172)
            radius: Bán kính tìm kiếm (mét), mặc định 5km
            specialty: Chuyên khoa (VD: "nhi", "tim mạch") - tìm trong tên bệnh viện
            limit: Số lượng kết quả tối đa
            
        Returns:
            Dictionary chứa:
            - success: True/False
            - hospitals: List các bệnh viện
            - message: Thông báo lỗi (nếu có)
            
        Example:
            >>> service.find_nearby_hospitals(10.762622, 106.660172)
            {
                'success': True,
                'hospitals': [
                    {
                        'name': 'Bệnh viện Chợ Rẫy',
                        'address': '201B Nguyễn Chí Thanh, Quận 5',
                        'distance': 1.2,
                        'latitude': 10.7545,
                        'longitude': 106.6646
                    },
                    ...
                ]
            }
        """
        try:
            # Rate limiting
            self._rate_limit()
            
            # Tạo Overpass query để tìm bệnh viện
            # Overpass QL: Tìm node và way có tag amenity=hospital
            query = f"""
            [out:json][timeout:25];
            (
              node["amenity"="hospital"](around:{radius},{latitude},{longitude});
              way["amenity"="hospital"](around:{radius},{latitude},{longitude});
              relation["amenity"="hospital"](around:{radius},{latitude},{longitude});
            );
            out body;
            >;
            out skel qt;
            """
            
            logger.info(f"🔍 Searching hospitals near ({latitude}, {longitude}) with radius {radius}m")
            
            # Gọi Overpass API
            response = requests.post(
                self.OVERPASS_URL,
                data={'data': query},
                timeout=30,
                headers={'User-Agent': 'MedicalChatbot/1.0'}  # Bắt buộc phải có User-Agent
            )
            response.raise_for_status()
            
            data = response.json()
            elements = data.get('elements', [])
            
            if not elements:
                return {
                    'success': True,
                    'hospitals': [],
                    'message': 'Không tìm thấy bệnh viện nào trong khu vực này'
                }
            
            # Parse kết quả
            hospitals = []
            seen_names = set()  # Để tránh trùng lặp
            
            for element in elements:
                tags = element.get('tags', {})
                name = tags.get('name', tags.get('name:vi', 'Bệnh viện không tên'))
                
                # Bỏ qua nếu trùng tên
                if name in seen_names:
                    continue
                
                # Lọc theo chuyên khoa (nếu có)
                if specialty and specialty.lower() not in name.lower():
                    continue
                
                # Lấy tọa độ
                if element['type'] == 'node':
                    elem_lat = element.get('lat')
                    elem_lon = element.get('lon')
                elif element['type'] == 'way':
                    # Với way, lấy tọa độ trung tâm (nếu có)
                    elem_lat = element.get('center', {}).get('lat') or element.get('lat')
                    elem_lon = element.get('center', {}).get('lon') or element.get('lon')
                else:
                    continue  # Skip relations
                
                if not elem_lat or not elem_lon:
                    continue
                
                # Tính khoảng cách
                distance = self.calculate_distance(latitude, longitude, elem_lat, elem_lon)
                
                # Lấy địa chỉ
                address_parts = []
                if tags.get('addr:street'):
                    address_parts.append(tags['addr:street'])
                if tags.get('addr:housenumber'):
                    address_parts.insert(0, tags['addr:housenumber'])
                if tags.get('addr:district'):
                    address_parts.append(tags['addr:district'])
                if tags.get('addr:city'):
                    address_parts.append(tags['addr:city'])
                
                address = ', '.join(address_parts) if address_parts else 'Không rõ địa chỉ'
                
                hospital = {
                    'name': name,
                    'address': address,
                    'latitude': elem_lat,
                    'longitude': elem_lon,
                    'distance': distance,
                    'phone': tags.get('phone', tags.get('contact:phone')),
                    'website': tags.get('website', tags.get('contact:website')),
                    'emergency': tags.get('emergency') == 'yes',
                    'beds': tags.get('beds'),
                    'operator': tags.get('operator')  # Đơn vị quản lý (công/tư)
                }
                
                hospitals.append(hospital)
                seen_names.add(name)
            
            # === ƯU TIÊN BỆNH VIỆN LỚN ===
            # Tính điểm ưu tiên cho mỗi bệnh viện
            # Điểm càng cao = ưu tiên càng cao
            for hospital in hospitals:
                priority_score = 0
                
                # 1. Khoảng cách (càng gần càng tốt)
                # Điểm tối đa 100 cho bệnh viện trong bán kính 1km
                distance_score = max(0, 100 - (hospital['distance'] * 20))
                priority_score += distance_score
                
                # 2. Bệnh viện công lập (+50 điểm)
                operator = hospital.get('operator', '').lower()
                if any(keyword in operator for keyword in ['bộ y tế', 'nhà nước', 'công', 'quận', 'thành phố']):
                    priority_score += 50
                    hospital['is_public'] = True
                else:
                    hospital['is_public'] = False
                
                # 3. Có cấp cứu 24/7 (+40 điểm)
                if hospital.get('emergency'):
                    priority_score += 40
                
                # 4. Số giường bệnh (bệnh viện lớn)
                beds = hospital.get('beds')
                if beds:
                    try:
                        beds_num = int(beds)
                        # +30 điểm nếu > 500 giường
                        # +20 điểm nếu > 200 giường
                        # +10 điểm nếu > 100 giường
                        if beds_num > 500:
                            priority_score += 30
                        elif beds_num > 200:
                            priority_score += 20
                        elif beds_num > 100:
                            priority_score += 10
                    except:
                        pass
                
                # 5. Tên bệnh viện có từ khóa quan trọng
                name_lower = hospital['name'].lower()
                if any(keyword in name_lower for keyword in ['đại học', 'trung ương', 'chợ rẫy', 'bạch mai', 'việt đức']):
                    priority_score += 30  # Bệnh viện hạng đầu
                elif any(keyword in name_lower for keyword in ['thành phố', 'tỉnh', 'quận']):
                    priority_score += 20  # Bệnh viện công lập cấp cao
                
                hospital['priority_score'] = priority_score
            
            # Sắp xếp theo điểm ưu tiên (cao → thấp)
            hospitals.sort(key=lambda x: x['priority_score'], reverse=True)
            
            logger.info(f"✓ Prioritized hospitals. Top: {hospitals[0]['name']} (score: {hospitals[0]['priority_score']:.1f})")

            
            # Giới hạn số lượng
            hospitals = hospitals[:limit]
            
            logger.info(f"✓ Found {len(hospitals)} hospitals from OpenStreetMap")
            
            return {
                'success': True,
                'hospitals': hospitals,
                'search_location': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'radius_km': radius / 1000,
                'data_source': 'OpenStreetMap (Free)'
            }
            
        except requests.exceptions.Timeout:
            logger.error("Overpass API timeout")
            return {
                'success': False,
                'message': 'Timeout khi tìm kiếm. Vui lòng thử lại.',
                'hospitals': []
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            return {
                'success': False,
                'message': f'Lỗi kết nối: {str(e)}',
                'hospitals': []
            }
        except Exception as e:
            logger.error(f"Error finding hospitals: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Lỗi: {str(e)}',
                'hospitals': []
            }
    
    def format_hospitals_for_chatbot(self, hospitals: List[Dict]) -> str:
        """
        Format danh sách bệnh viện thành text để đưa vào chatbot response.
        
        Args:
            hospitals: List các bệnh viện từ find_nearby_hospitals()
            
        Returns:
            String formatted sẵn để hiển thị cho user
        """
        if not hospitals:
            return """Không tìm thấy bệnh viện nào trong khu vực.

🚨 **ĐƯỜNG DÂY NÓNG Y TẾ**
📞 **115** - Cấp cứu y tế 24/7 (miễn phí)
Gọi ngay nếu cần hỗ trợ khẩn cấp!

⚠️ *Lưu ý: Thông tin chỉ mang tính chất tham khảo. Vui lòng tham khảo ý kiến bác sĩ để được chẩn đoán và điều trị chính xác.*"""
        
        result = f"Tìm thấy {len(hospitals)} bệnh viện gần bạn:\n\n"
        
        # Danh sách số điện thoại của các bệnh viện lớn (fallback nếu OSM không có)
        KNOWN_HOSPITAL_PHONES = {
            # TP.HCM
            'chợ rẫy': '028 3855 4137',
            'bệnh viện chợ rẫy': '028 3855 4137',
            'thống nhất': '028 3829 5071',
            'bệnh viện thống nhất': '028 3829 5071',
            '115': '115',
            'bệnh viện 115': '028 3950 7506',
            'nhi đồng 1': '028 3829 5723',
            'nhi đồng 2': '028 3899 3498',
            'từ dũ': '028 3829 5024',
            'hùng vương': '028 3829 5024',
            'thành phố thủ đức': '028 3897 1212',
            'bệnh viện thành phố thủ đức': '028 3897 1212',
            'quận dân y miền đông': '028 3724 3434',
            'đa khoa miền đông': '028 3724 3434',
            
            # Hà Nội
            'bạch mai': '024 3869 3731',
            'bệnh viện bạch mai': '024 3869 3731',
            'việt đức': '024 3825 3531',
            'bệnh viện việt đức': '024 3825 3531',
        }
        
        for i, h in enumerate(hospitals, 1):
            # Thêm icon cho bệnh viện công lập/lớn
            name_prefix = ""
            if h.get('is_public'):
                name_prefix = "🏛️ "  # Bệnh viện công
            
            result += f"**{i}. {name_prefix}{h['name']}**\n"
            result += f"   📍 Địa chỉ: {h['address']}\n"
            result += f"   📏 Khoảng cách: {h['distance']} km\n"
            
            # Hiển thị loại bệnh viện
            if h.get('is_public'):
                result += f"   🏥 Bệnh viện công lập\n"
            
            # Số điện thoại - ưu tiên từ OSM, fallback sang danh sách known
            phone = h.get('phone')
            if not phone:
                # Tìm trong danh sách known hospitals
                hospital_name_lower = h['name'].lower()
                for key, known_phone in KNOWN_HOSPITAL_PHONES.items():
                    if key in hospital_name_lower:
                        phone = known_phone
                        break
            
            if phone:
                result += f"   📞 Điện thoại: {phone}\n"
            else:
                # Gợi ý tìm trên Google
                result += f"   📞 Điện thoại: Tìm trên Google '{h['name']} số điện thoại'\n"

            
            if h.get('emergency'):
                result += f"   🚨 Có cấp cứu 24/7\n"
            
            if h.get('beds'):
                result += f"   🛏️ Số giường: {h['beds']}\n"
            
            if h.get('operator'):
                result += f"   👥 Quản lý: {h['operator']}\n"
            
            result += "\n"
        
        # Thêm thông tin đường dây nóng và lời khuyên y tế
        result += """---

🚨 **ĐƯỜNG DÂY NÓNG Y TẾ**
📞 **115** - Cấp cứu y tế 24/7 (miễn phí)
Gọi ngay nếu bạn hoặc người thân cần hỗ trợ y tế khẩn cấp!

💡 *Dữ liệu từ OpenStreetMap • Ưu tiên bệnh viện công lập và lớn*

⚠️ **Lưu ý quan trọng:** Thông tin trên chỉ mang tính chất tham khảo. Vui lòng đến gặp bác sĩ hoặc cơ sở y tế để được khám, chẩn đoán và điều trị chính xác. Chatbot không thể thay thế ý kiến của chuyên gia y tế."""
        
        return result



# Singleton instance
hospital_finder_service = HospitalFinderService()
