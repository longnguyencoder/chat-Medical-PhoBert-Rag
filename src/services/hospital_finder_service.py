"""
Hospital Finder Service - Smart Edition
================================================
Service tìm kiếm bệnh viện sử dụng OpenStreetMap kết hợp Knowledge Base.
"""

import requests
import logging
from math import radians, cos, sin, asin, sqrt
from typing import List, Dict, Optional
import time
import unicodedata

logger = logging.getLogger(__name__)

def remove_accents(input_str):
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

class HospitalFinderService:
    
    # Danh sách các Server Overpass (Main + Backup)
    OVERPASS_URLS = [
        "https://overpass-api.de/api/interpreter",          # Global Main
        "https://lz4.overpass-api.de/api/interpreter",      # Global Mirror
        "https://caltopo.com/api/overpass/result",          # US Mirror (khá nhanh)
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter" # Russia Mirror
    ]
    
    SPECIALTY_KNOWLEDGE_BASE = {
        # =========================================================================
        # 1. TIM MẠCH (Cardiology)
        # =========================================================================
        'tim': ['vien tim', 'tim mach', 'cho ray', 'bach mai', 'thong nhat', '115'],
        'tim mach': ['vien tim', 'tim mach', 'cho ray', 'bach mai', 'thong nhat', '115'],
        'nhoi mau co tim': ['vien tim', '115', 'cho ray', 'bach mai', 'thong nhat'],
        'huyet ap': ['tim mach', 'lao khoa', 'thong nhat', 'bach mai'],
        'cao huyet ap': ['tim mach', 'lao khoa'],
        'h2': ['tim mach', 'cho ray', 'bach mai'], # Suy tim
        'mach mau': ['binh dan', 'cho ray', 'dai hoc y duoc'], # Ngoại lồng ngực mạch máu

        # =========================================================================
        # 2. THẦN KINH - ĐỘT QUỴ (Neurology & Stroke)
        # =========================================================================
        'than kinh': ['cho ray', 'ngoai than kinh', 'bach mai', 'viet duc', '115'],
        'ngoai than kinh': ['cho ray', 'viet duc', 'bach mai', '115'],
        'dau dau': ['than kinh', 'cho ray'],
        'roi loan tien dinh': ['than kinh', 'tai mui hong'],
        'mat ngu': ['tam than', 'suc khoe tam than', 'than kinh', 'y hoc co truyen'],
        'dot quy': ['115', 'dot quy', 'cho ray', 'bach mai', 'nhan dan 115'],
        'tai bien': ['115', 'dot quy', 'cho ray', 'bach mai'],
        'dong kinh': ['tam than', 'than kinh'],
        'parkinson': ['lao khoa', 'thong nhat', 'than kinh'],

        # =========================================================================
        # 3. UNG BƯỚU (Oncology)
        # =========================================================================
        'ung buou': ['ung buou', 'benh vien k', 'cho ray', 'bach mai', '175', '115'],
        'ung thu': ['ung buou', 'benh vien k', 'cho ray', 'bach mai'],
        'xa tri': ['ung buou', 'benh vien k', 'cho ray'],
        'hoa tri': ['ung buou', 'benh vien k', 'cho ray'],
        'k': ['benh vien k', 'ung buou'], 
        'u xo': ['ung buou', 'san', 'phu khoa'],
        'u nang': ['ung buou', 'san', 'phu khoa'],
        'tuyen vu': ['ung buou', 'benh vien k'],
        'buu co': ['ung buou', 'noi tiet', 'cho ray', 'bach mai', '115', 'dai hoc y duoc'], 
        'tuyen giap': ['ung buou', 'noi tiet', 'cho ray', 'bach mai', '115'],
        'ung buou tp hcm': ['ung buou'], 

        # =========================================================================
        # 4. NỘI TIẾT (Endocrinology)
        # =========================================================================
        'noi tiet': ['noi tiet', 'bach mai', 'cho ray', '115', 'dai hoc y duoc'],
        'tieu duong': ['noi tiet', 'bach mai', 'cho ray', '115'],
        'dai thao duong': ['noi tiet', 'lao khoa'],
        'basedow': ['noi tiet', 'ung buou'],

        # =========================================================================
        # 5. TIÊU HÓA - GAN MẬT (Gastroenterology & Hepatology)
        # =========================================================================
        'tieu hoa': ['binh dan', 'dai hoc y duoc', 'cho ray', 'bach mai', '108'],
        'da day': ['binh dan', 'dai hoc y duoc', 'cho ray', 'bach mai'],
        'dau bao tu': ['binh dan', 'dai hoc y duoc'],
        'dai trang': ['binh dan', 'dai hoc y duoc', 'cho ray'],
        'tri': ['binh dan', 'dai hoc y duoc', 'y hoc co truyen'], # Trĩ
        'hau mon': ['binh dan', 'dai hoc y duoc'],
        'truc trang': ['binh dan', 'ung buou'],
        'gan': ['nhiet doi', 'cho ray', 'bach mai', '108', 'binh dan'],
        'viem gan': ['nhiet doi', 'bach mai', 'cho ray'],
        'xo gan': ['nhiet doi', 'cho ray'],
        'mat': ['binh dan', 'cho ray'], # Mật

        # =========================================================================
        # 6. THẬN - TIẾT NIỆU (Nephrology & Urology)
        # =========================================================================
        'than': ['binh dan', 'cho ray', 'bach mai', 'viet duc'],
        'suy than': ['binh dan', 'cho ray', 'bach mai'],
        'chay than': ['binh dan', 'cho ray', 'thong nhat'],
        'tiet nieu': ['binh dan', 'cho ray', 'viet duc'],
        'soi than': ['binh dan', 'cho ray', 'viet duc'],
        'bang quang': ['binh dan'],
        
        # =========================================================================
        # 7. XƯƠNG KHỚP - CHẤN THƯƠNG (Orthopedics)
        # =========================================================================
        'xuong khop': ['chan thuong chinh hinh', 'viet duc', '115', 'cho ray', 'bach mai', '108'],
        'chan thuong': ['chan thuong chinh hinh', 'viet duc', '115', 'cho ray', 'thanh nien', 'sai gon ito'],
        'cot song': ['chan thuong chinh hinh', 'ngoai than kinh', 'viet duc', 'cho ray'],
        'thoat vi': ['chan thuong chinh hinh', 'ngoai than kinh', 'viet duc', '115'],
        'gay xuong': ['chan thuong chinh hinh', '115', 'viet duc'],
        'dau lung': ['chan thuong chinh hinh', 'y hoc co truyen'],
        'khop': ['chan thuong chinh hinh', 'cho ray'],
        'gout': ['chan thuong chinh hinh', 'cho ray', 'bach mai'], # Gút

        # =========================================================================
        # 8. SẢN - PHỤ KHOA (OB/GYN)
        # =========================================================================
        'san': ['tu du', 'hung vuong', 'phu san', 'me va be', 'hanh phuc', 'quoc te'],
        'phu khoa': ['tu du', 'hung vuong', 'phu san'],
        'mang thai': ['tu du', 'hung vuong', 'phu san'],
        'ba bau': ['tu du', 'hung vuong', 'phu san'],
        'sinh de': ['tu du', 'hung vuong', 'phu san'],
        'vo sinh': ['tu du', 'hung vuong', 'phu san', 'binh dan', 'tam anh', 'buu dien'],
        'hiem muon': ['tu du', 'hung vuong', 'phu san', 'binh dan', 'tam anh', 'buu dien'],
        'ivf': ['tu du', 'hung vuong', 'phu san', 'tam anh', 'my duc'],

        # =========================================================================
        # 9. NHI KHOA (Pediatrics)
        # =========================================================================
        'nhi': ['nhi dong', 'tu du', 'hung vuong', 'bach mai', 'viet duc', 'xanh pon', 'nam sai gon'],
        'tre em': ['nhi dong', 'bach mai', 'xanh pon'],
        'so sinh': ['nhi dong', 'tu du', 'hung vuong'],
        'dinh duong': ['nhi dong', 'dinh duong'], # Viện Dinh Dưỡng
        'tiem chung': ['nhi dong', 'pasteur', 'vnvc'],

        # =========================================================================
        # 10. HÔ HẤP - PHỔI (Pulmonology)
        # =========================================================================
        'ho hap': ['pham ngoc thach', 'bach mai', 'cho ray', 'phoi', 'dai hoc y duoc'],
        'phoi': ['pham ngoc thach', 'phoi', 'bach mai', 'cho ray'],
        'lao': ['pham ngoc thach', 'phoi'],
        'hen suyen': ['pham ngoc thach', 'ho hap', 'dai hoc y duoc'],
        'viem phoi': ['pham ngoc thach', 'bach mai', 'cho ray'],

        # =========================================================================
        # 11. TAI MŨI HỌNG - MẮT - RĂNG HÀM MẶT
        # =========================================================================
        'mat': ['mat', 'cho ray', 'tw', 'xanh pon', 'nga', 'sg'],
        'can thi': ['mat'],
        'duc thuy tinh the': ['mat'],
        'tai mui hong': ['tai mui hong', 'cho ray', 'bach mai'],
        'xoang': ['tai mui hong'],
        'thinh luc': ['tai mui hong'],
        'rang ham mat': ['rang ham mat', 'cho ray', 'dai hoc y'],
        'nha khoa': ['rang ham mat', 'nha khoa'],
        'nho rang': ['rang ham mat'],
        'nieng rang': ['rang ham mat'],

        # =========================================================================
        # 12. DA LIỄU - DỊ ỨNG (Dermatology)
        # =========================================================================
        'da lieu': ['da lieu', 'quy hoa', 'tp hcm'],
        'di ung': ['da lieu', 'bach mai', 'cho ray', 'mien dich'],
        'noi me day': ['da lieu'],
        'mun': ['da lieu'],
        'vay nen': ['da lieu'],
        'tham my': ['da lieu', 'tham my', 'cho ray'], # Khoa tạo hình thẩm mỹ BV Chợ Rẫy/108
        'dich vu': ['da lieu', 'tham my'],

        # =========================================================================
        # 13. TRUYỀN NHIỄM (Infectious Diseases)
        # =========================================================================
        'truyen nhiem': ['nhiet doi', 'bach mai', 'cho ray'],
        'sot xuat huyet': ['nhiet doi', 'nhi dong'],
        'viem nao': ['nhiet doi', 'nhi dong'],
        'hiv': ['nhiet doi'],
        'ky sinh trung': ['nhiet doi', 'sot ret'], # Viện sốt rét ký sinh trùng

        # =========================================================================
        # 14. NAM KHOA - SỨC KHỎE GIỚI TÍNH
        # =========================================================================
        'nam khoa': ['binh dan', 'viet duc', 'dai hoc y ha noi', 'tu du'],
        'yeu sinh ly': ['binh dan'],
        'cat bao quy dau': ['binh dan'],
        'benh xa hoi': ['da lieu'],

        # =========================================================================
        # 15. TÂM THẦN (Psychiatry)
        # =========================================================================
        'tam than': ['tam than', 'suc khoe tam than', 'mai huong'],
        'tram cam': ['tam than', 'suc khoe tam than'],
        'stress': ['tam than', 'y hoc co truyen'],
        'tu ky': ['nhi dong', 'tam than'],

        # =========================================================================
        # 16. Y HỌC CỔ TRUYỀN - PHỤC HỒI CHỨC NĂNG
        # =========================================================================
        'y hoc co truyen': ['y hoc co truyen'],
        'dong y': ['y hoc co truyen'],
        'cham cuu': ['y hoc co truyen', 'cham cuu'],
        'vat ly tri lieu': ['phuc hoi chuc nang', '1A', 'chinh hinh'],
        'phuc hoi chuc nang': ['phuc hoi chuc nang', '1A', 'bach mai'],

        # =========================================================================
        # 17. KHÁC
        # =========================================================================
        'bong': ['bong', 'cho ray', 'le huu trac', '103'],
        'lao khoa': ['lao khoa', 'thong nhat'], # Người già
        'nguoi gia': ['lao khoa', 'thong nhat'],
        'huyet hoc': ['huyet hoc', 'truyen mau', 'cho ray', 'bach mai'], # Máu
        'mau': ['huyet hoc', 'truyen mau'],
        'xet nghiem': ['pasteur', 'hoa hao', 'medic'], # Trung tâm xét nghiệm lớn
        'kham tong quat': ['hoa hao', 'dai hoc y duoc', 'cho ray', 'bach mai'],
    }

    TOP_TIER_HOSPITALS = [
        # TP.HCM
        'cho ray', 'dai hoc y duoc', '115', 'nhan dan 115', 'thong nhat', 'gia dinh', 'nguyen tri phuong',
        'tu du', 'hung vuong', 'nhi dong', 'nhiet doi', 'ung buou', 'binh dan', 'tai mui hong', 'mat', 'da lieu', 'chan thuong chinh hinh', 'pham ngoc thach', 'vien tim', 'truyen mau huyet hoc',
        
        # Hà Nội
        'bach mai', 'viet duc', '108', 'quan y 103', 'huu nghi', 'e', 'xanh pon', 'thanh nhan', 'dong da',
        'phu san trung uong', 'phu san ha noi', 'nhi trung uong', 'k', 'ung buou ha noi', 'noi tiet', 'tai mui hong trung uong', 'mat trung uong', 'da lieu trung uong', 'lao phoi', 'nhiet doi trung uong',
        
        # Hệ sinh thái tư nhân lớn/uy tín
        'tam anh', 'vinmec', 'hoan my', 'hanh phuc', 'fv', 'xuyen a'
    ]

    # Link đặt lịch khám / Website chính thức
    KNOWN_HOSPITAL_URLS = {
        # --- TP.HCM ---
        'cho ray': 'https://medpro.vn/cho-ray',
        '115': 'https://medpro.vn/benh-vien-nhan-dan-115',
        'dai hoc y duoc': 'https://dangkykham.bvdaihoc.com.vn',
        'thong nhat': 'https://medpro.vn/benh-vien-thong-nhat',
        'tu du': 'https://medpro.vn/benh-vien-tu-du',
        'hung vuong': 'https://medpro.vn/benh-vien-hung-vuong',
        'nhi dong 1': 'https://medpro.vn/benh-vien-nhi-dong-1',
        'nhi dong 2': 'https://medpro.vn/benh-vien-nhi-dong-2',
        'nhi dong thanh pho': 'https://medpro.vn/benh-vien-nhi-dong-thanh-pho',
        'ung buou': 'https://medpro.vn/benh-vien-ung-buou',
        'binh dan': 'https://medpro.vn/benh-vien-binh-dan',
        'tai mui hong': 'https://taimuihongtphcm.vn/dang-ky-kham-benh',
        'mat': 'https://medpro.vn/benh-vien-mat',
        'da lieu': 'https://medpro.vn/benh-vien-da-lieu',
        'chan thuong chinh hinh': 'https://medpro.vn/benh-vien-chan-thuong-chinh-hinh',
        'pham ngoc thach': 'https://medpro.vn/benh-vien-pham-ngoc-thach',
        'nhiet doi': 'https://medpro.vn/benh-vien-benh-nhiet-doi',
        'vien tim': 'https://medpro.vn/vien-tim',
        'gia dinh': 'https://medpro.vn/benh-vien-gia-dinh',
        'nguyen tri phuong': 'https://medpro.vn/benh-vien-nguyen-tri-phuong',
        
        # --- Hà Nội ---
        'bach mai': 'https://medpro.vn/benh-vien-bach-mai',
        'viet duc': 'https://medpro.vn/benh-vien-viet-duc',
        '108': 'https://benhvien108.vn/dang-ky-kham',
        'benh vien k': 'https://medpro.vn/benh-vien-k',
        'nhi trung uong': 'https://medpro.vn/benh-vien-nhi-trung-uong',
        'phu san trung uong': 'https://medpro.vn/benh-vien-phu-san-trung-uong',
        'dai hoc y ha noi': 'https://dangkykham.benhviendaihocyhanoi.com',
        'da lieu trung uong': 'https://medpro.vn/benh-vien-da-lieu-trung-uong',

        # --- Tư nhân ---
        'vinmec': 'https://www.vinmec.com/vi/dat-lich-kham/',
        'tam anh': 'https://tamanhhospital.vn/dat-lich/',
        'hoan my': 'https://hoanmy.com/dat-lich/',
        'fv': 'https://www.fvhospital.com/make-an-appointment/',
        'medlatec': 'https://medlatec.vn/dat-lich',
        'xuyen a': 'https://xuyenahospital.com/dat-lich-kham/',
        'city international': 'https://cih.com.vn/vi/dat-lich-kham/',
    }

    LAST_REQUEST_TIME = 0
    MIN_REQUEST_INTERVAL = 1.0
    
    @staticmethod
    def _rate_limit():
        current_time = time.time()
        time_since_last = current_time - HospitalFinderService.LAST_REQUEST_TIME
        if time_since_last < HospitalFinderService.MIN_REQUEST_INTERVAL:
            time.sleep(HospitalFinderService.MIN_REQUEST_INTERVAL - time_since_last)
        HospitalFinderService.LAST_REQUEST_TIME = time.time()
    
    @staticmethod
    def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        try:
            lat1, lng1, lat2, lng2 = map(float, [lat1, lng1, lat2, lng2])
            lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
            dlng = lng2 - lng1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
            c = 2 * asin(sqrt(a))
            return round(6371 * c, 2)
        except Exception:
            return 999.0
    
    def find_nearby_hospitals(
        self,
        latitude: float,
        longitude: float,
        radius: int = 20000, # BUMP to 20km
        specialty: Optional[str] = None,
        limit: int = 15 # Bump to 15
    ) -> Dict:
        # Rate limit
        self._rate_limit()

        # === MAPBOX INTEGRATION (Primary) ===
        mapbox_elements = []
        try:
            import os
            mapbox_token = os.getenv('MAPBOX_ACCESS_TOKEN')
            if mapbox_token:
                # Prepare search term
                # Specialty might be a long string from RAG (e.g., "nhi, khoa nhi, trẻ em")
                # Mapbox works best with short queries. We take the FIRST keyword.
                primary_keyword = specialty.split(',')[0].strip() if specialty else ""
                
                search_term = "bệnh viện"
                if primary_keyword:
                    search_term = f"bệnh viện {primary_keyword}"
                
                # Mapbox Geocoding API Request
                # Use 'mapbox.places' endpoint
                mapbox_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{search_term}.json"
                params = {
                    'access_token': mapbox_token,
                    'proximity': f"{longitude},{latitude}",
                    'types': 'poi',
                    'limit': '10', # Max limit per request
                    'language': 'vi'
                }
                
                logger.info(f"🔍 Mapbox Query: '{search_term}' @ {latitude},{longitude}")
                mb_response = requests.get(mapbox_url, params=params, timeout=5)
                
                if mb_response.status_code == 200:
                    features = mb_response.json().get('features', [])
                    if features:
                        logger.info(f"✓ Mapbox found {len(features)} locations.")
                        for f in features:
                            # Convert Mapbox Feature -> "Pseudo" OSM Element
                            # to reuse existing scoring logic
                            props = f.get('properties', {})
                            center = f.get('center', [0, 0]) # [lon, lat]
                            
                            # Construct tags
                            tags = {
                                'name': f.get('text', ''),
                                'name:vi': f.get('text_vi') or f.get('text', ''),
                                'addr:full': f.get('place_name', ''), # Custom tag
                                'phone': props.get('tel'),
                                'website': props.get('website'),
                                'amenity': 'hospital', # Assume hospital context
                                'source': 'mapbox'
                            }
                            
                            # Extract address components if available (simplified)
                            if 'place_name' in f:
                                tags['addr:street'] = f['place_name']
                            
                            if props.get('category'):
                                tags['category'] = props['category']

                            element = {
                                'lat': center[1],
                                'lon': center[0],
                                'tags': tags
                            }
                            mapbox_elements.append(element)
        except Exception as e:
            logger.error(f"⚠️ Mapbox Error: {e}")

        # If Mapbox found results, use them
        if mapbox_elements:
            elements = mapbox_elements
            # Skip Overpass
        else:
            # === OVERPASS FALLBACK (Secondary) ===
            logger.info("ℹ️ Fallback to Overpass API...")
            
            # Query: Lấy nodes, ways VÀ RELATIONS
            query_body = f"""
            (
              node["amenity"~"hospital|clinic"](around:{radius},{latitude},{longitude});
              way["amenity"~"hospital|clinic"](around:{radius},{latitude},{longitude});
              relation["amenity"~"hospital|clinic"](around:{radius},{latitude},{longitude});
            );
            out center;
            """
            
            data = None
            
            # === RETRY MECHANISM ===
            for url in self.OVERPASS_URLS:
                try:
                    full_query = f"[out:json][timeout:25];{query_body}"
                    logger.info(f"🔍 Connecting to map server: {url}")
                    
                    response = requests.post(
                        url, 
                        data={'data': full_query},
                        timeout=30, 
                        headers={'User-Agent': 'MedicalChatbot/1.0'}
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'elements' in data:
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Server {url} failed: {e}. Trying next...")
                    continue
            
            if not data or 'elements' not in data:
                return {
                    'success': False, 
                    'message': 'Hệ thống bản đồ đang quá tải. Vui lòng thử lại sau vài phút.', 
                    'hospitals': []
                }
                
            elements = data.get('elements', [])
        
        if not elements:
            return {'success': True, 'hospitals': [], 'message': 'Không tìm thấy bệnh viện nào trong khu vực.'}
        
        hospitals = []
        seen_names = set()
        
        specialty_keywords = []
        search_keywords = []
        rag_keywords = []  # NEW: Keywords from RAG
        
        if specialty:
            # === NEW: TRY RAG SEMANTIC SEARCH FIRST ===
            try:
                from src.services.hospital_specialty_rag import hybrid_specialty_matching
                rag_keywords = hybrid_specialty_matching(specialty, top_k=5)
                search_keywords.extend(rag_keywords)
                logger.info(f"✓ RAG found {len(rag_keywords)} specialty keywords: {rag_keywords[:5]}")
            except Exception as e:
                logger.warning(f"⚠ RAG failed, fallback to keyword matching: {e}")
            
            # === EXISTING: FALLBACK KEYWORD MATCHING ===
            normalized_specialty = remove_accents(specialty.lower())
            for key, values in self.SPECIALTY_KNOWLEDGE_BASE.items():
                if key in normalized_specialty or normalized_specialty in key:
                    search_keywords.extend(values)
            search_keywords.append(normalized_specialty)
            
            # Deduplicate
            search_keywords = list(set(search_keywords))
            logger.info(f"Total keywords (RAG + fallback): {len(search_keywords)}")


        for element in elements:
            tags = element.get('tags', {})
            name = tags.get('name', tags.get('name:vi', ''))
            if not name: continue
            
            if name in seen_names: continue
            
            lat = element.get('lat') or element.get('center', {}).get('lat')
            lon = element.get('lon') or element.get('center', {}).get('lon')
            
            if not lat or not lon: continue
            
            distance = self.calculate_distance(latitude, longitude, lat, lon)
            
            # === ENHANCED SCORING ===
            priority_score = 0
            match_reason = []
            name_normalized = remove_accents(name.lower())
            
            is_specialty_match = False
            is_semantic_match = False
            
            if specialty:
                # Check RAG semantic match first (higher priority)
                for kw in rag_keywords:
                    if kw in name_normalized:
                        priority_score += 600  # Higher score for semantic match
                        match_reason.append("Khớp chuyên khoa (AI)")
                        is_semantic_match = True
                        is_specialty_match = True
                        break
                
                # If no semantic match, check traditional keyword match
                if not is_semantic_match:
                    for kw in search_keywords:
                        if kw in name_normalized:
                            priority_score += 500
                            match_reason.append("Đúng chuyên khoa")
                            is_specialty_match = True
                            break
            
            if specialty and not is_specialty_match:
                priority_score -= 1000 
            
            for top in self.TOP_TIER_HOSPITALS:
                if top in name_normalized:
                    priority_score += 100
                    match_reason.append("Bệnh viện đầu ngành")
                    break
                    
            priority_score -= (distance * 10)
            
            if tags.get('emergency') == 'yes': priority_score += 20
            if tags.get('amenity') == 'hospital': priority_score += 10 

            address_parts = []
            if tags.get('addr:housenumber'): address_parts.append(tags['addr:housenumber'])
            if tags.get('addr:street'): address_parts.append(tags['addr:street'])
            if tags.get('addr:district'): address_parts.append(tags['addr:district'])
            address = ', '.join(address_parts) if address_parts else 'Đang cập nhật'

            # Website Lookup
            website = tags.get('website', tags.get('contact:website', ''))
            if not website:
                # Fallback to Known URLs
                for k, v in self.KNOWN_HOSPITAL_URLS.items():
                    # Chỉ match nếu key xuất hiện trọn vẹn (để tránh lỗi 'k' trong 'đa khoa')
                    # Tuy nhiên, name_normalized là string dài, k là sub-string.
                    # Cách fix: Đổi key 'k' thành 'benh vien k' ở trên dict.
                    if k in name_normalized:
                        website = v
                        break

            hospitals.append({
                'name': name,
                'address': address,
                'distance': distance,
                'priority_score': priority_score,
                'match_reasons': match_reason,
                'phone': tags.get('phone', tags.get('contact:phone')),
                'website': website,
                'latitude': lat,
                'longitude': lon
            })
            seen_names.add(name)
        
        hospitals.sort(key=lambda x: x['priority_score'], reverse=True)
        hospitals = hospitals[:limit]
        
        return {
            'success': True,
            'hospitals': hospitals,
            'search_info': {'specialty': specialty}
        }

    def format_hospitals_for_chatbot(self, hospitals: List[Dict]) -> str:
        if not hospitals:
            return "Không tìm thấy bệnh viện phù hợp trong khu vực này."
            
        result = f"🏥 **Danh sách Bệnh viện đề xuất**:\n\n"
        
        KNOWN_PHONES = {
            'cho ray': '028 3855 4137',
            'bach mai': '024 3869 3731',
            '115': '028 3950 7506',
            'nhi dong 1': '028 3829 5723',
            'nhi dong 2': '028 3899 3498',
            'tu du': '028 3829 5024',
            'hung vuong': '028 3855 8532',
             'viet duc': '024 3825 3531',
             'da lieu': '028 3930 8131'
        }
        
        for i, h in enumerate(hospitals, 1):
            icon = "🏥"
            reasons = h.get('match_reasons', [])
            if "Bệnh viện đầu ngành" in reasons: icon = "🏛️"
            if "Đúng chuyên khoa" in reasons: icon = "⭐"
            
            result += f"**{i}. {icon} {h['name']}**\n"
            
            if reasons:
                result += f"   ✅ {', '.join(reasons)}\n"
            
            result += f"   📍 {h['address']}\n"
            
            phone = h.get('phone')
            if not phone:
                 for k, v in KNOWN_PHONES.items():
                     if k in remove_accents(h['name'].lower()):
                         phone = v
                         break
            if phone:
                result += f"   📞 {phone}\n"
            
            # Booking Link
            website = h.get('website')
            if website:
                 result += f"   🌐 [Đặt lịch / Website]({website})\n"
            else:
                 search_query = f"dat lich kham {h['name']}".replace(" ", "+")
                 result += f"   🌐 [Tìm đặt lịch (Google)](https://www.google.com/search?q={search_query})\n"
            
            # Map Link (Option 1 Implementation)
            lat = h.get('latitude')
            lon = h.get('longitude')
            if lat and lon:
                map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            else:
                # Fallback to name search if coords are missing
                map_query = h['name'].replace(" ", "+")
                map_link = f"https://www.google.com/maps/search/?api=1&query={map_query}"
            
            result += f"   🗺️ [Xem bản đồ chỉ đường]({map_link})\n"

            result += "\n"
        
        return result

hospital_finder_service = HospitalFinderService()
