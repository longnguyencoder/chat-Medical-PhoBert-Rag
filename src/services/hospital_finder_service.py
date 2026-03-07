"""
Hospital Finder Service - Smart Edition
================================================
Service tìm kiếm bệnh viện sử dụng OpenStreetMap kết hợp Knowledge Base.
"""

import requests
import re
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
    
    def __init__(self):
        self.csv_hospitals = self._load_hcmc_csv()

    def _load_hcmc_csv(self) -> List[Dict]:
        """Loads custom HCMC hospital data from CSV."""
        import csv
        import os
        hospitals = []
        try:
            # Assuming the file is in src/data/hcmc_hospitals.csv
            file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'hcmc_hospitals.csv')
            if os.path.exists(file_path):
                with open(file_path, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Convert types
                        try:
                            row['lat'] = float(row['lat'])
                            row['lng'] = float(row['lng'])
                            row['reputation_score'] = float(row['reputation_score'])
                            row['avg_cost_score'] = float(row['avg_cost_score'])
                        except (ValueError, TypeError):
                            continue
                        hospitals.append(row)
                logger.info(f"✓ Loaded {len(hospitals)} custom hospitals from {file_path}")
            else:
                logger.warning(f"⚠ CSV file not found at {file_path}")
        except Exception as e:
            logger.error(f"✗ Error loading hospital CSV: {e}")
        return hospitals

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
        'mat': ['mat', 'mat sai gon', 'cho ray', 'tw', 'xanh pon', 'nga', 'sg'],
        'can thi': ['mat', 'mat sai gon'],
        'duc thuy tinh the': ['mat'],
        'tai mui hong': ['tai mui hong', 'cho ray', 'bach mai'],
        'xoang': ['tai mui hong'],
        'thinh luc': ['tai mui hong'],
        'rang ham mat': ['rang ham mat', 'cho ray', 'dai hoc y', 'rang ham mat trung uong'],
        'nha khoa': ['rang ham mat', 'nha khoa'],
        'nho rang': ['rang ham mat'],
        'nieng rang': ['rang ham mat'],
        'rang': ['rang ham mat'],

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
        'cho ray', 'dai hoc y duoc', '115', 'nhan dan 115', 'thong nhat', 'gia dinh', 'nhan dan gia dinh', 'nguyen tri phuong', 'quan y 175', '175', 'trung vuong', 'nguyen trai', 'tu du', 'hung vuong', 'nhi dong', 'nhiet doi', 'benh nhiet doi', 'ung buou', 'binh dan', 'tai mui hong', 'mat', 'da lieu', 'chan thuong chinh hinh', 'pham ngoc thach', 'vien tim', 'truyen mau huyet hoc', 'rang ham mat trung uong', 'rang ham mat tp hcm', 'phuc hoi chuc nang', 'y hoc co truyen tp hcm', 'vien y duoc hoc dan toc',
        
        # Hà Nội
        'bach mai', 'viet duc', '108', 'quan y 103', 'huu nghi', 'e', 'xanh pon', 'thanh nhan', 'dong da',
        'phu san trung uong', 'phu san ha noi', 'nhi trung uong', 'k', 'ung buou ha noi', 'noi tiet', 'tai mui hong trung uong', 'mat trung uong', 'da lieu trung uong', 'lao phoi', 'nhiet doi trung uong', 'rang ham mat trung uong',
        
        # Hệ sinh thái tư nhân lớn/uy tín
        'tam anh', 'vinmec', 'hoan my', 'hanh phuc', 'fv', 'xuyen a', 'hong ngoc', 'thu cuc', 'phuong dong', 'viet phap'
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
        'nhan dan gia dinh': 'https://medpro.vn/benh-vien-nhan-dan-gia-dinh',
        'nguyen tri phuong': 'https://medpro.vn/benh-vien-nguyen-tri-phuong',
        'quan y 175': 'https://medpro.vn/benh-vien-quan-y-175',
        '175': 'https://medpro.vn/benh-vien-quan-y-175',
        'trung vuong': 'https://medpro.vn/benh-vien-trung-vuong',
        'nguyen trai': 'https://medpro.vn/benh-vien-nguyen-trai',
        'nhi dong thanh pho': 'https://medpro.vn/benh-vien-nhi-dong-thanh-pho',
        'tai mui hong tp hcm': 'https://medpro.vn/benh-vien-tai-mui-hong-tp-hcm',
        'rang ham mat trung uong': 'https://medpro.vn/benh-vien-rang-ham-mat-trung-uong-tp-hcm',
        'da lieu tp hcm': 'https://medpro.vn/benh-vien-da-lieu-tp-hcm',
        'y hoc co truyen tp hcm': 'https://medpro.vn/benh-vien-y-hoc-co-truyen-tphcm',
        
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
        """
        Calculate the Haversine distance between two points on the earth.
        Returns distance in km.
        """
        try:
            # Explicit float conversion
            lat1, lng1, lat2, lng2 = float(lat1), float(lng1), float(lat2), float(lng2)
            
            # Use 6371.0 km as the mean Earth radius
            R = 6371.0
            
            phi1, phi2 = radians(lat1), radians(lat2)
            dphi = radians(lat2 - lat1)
            dlambda = radians(lng2 - lng1)
            
            a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
            c = 2 * asin(sqrt(a))
            
            dist = R * c
            return round(dist, 2)
        except Exception as e:
            logger.error(f"Error in calculate_distance: {e}")
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
                primary_keyword = specialty.split(',')[0].strip() if specialty else ""
                
                search_term = "bệnh viện"
                if primary_keyword:
                    search_term = f"bệnh viện {primary_keyword}"
                
                mapbox_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{search_term}.json"
                params = {
                    'access_token': mapbox_token,
                    'proximity': f"{longitude},{latitude}",
                    'types': 'poi',
                    'limit': '10',
                    'language': 'vi'
                }
                
                logger.info(f"🔍 Mapbox Query: '{search_term}' @ {latitude},{longitude}")
                mb_response = requests.get(mapbox_url, params=params, timeout=5)
                
                if mb_response.status_code == 200:
                    features = mb_response.json().get('features', [])
                    if features:
                        logger.info(f"✓ Mapbox found {len(features)} locations.")
                        for f in features:
                            props = f.get('properties', {})
                            center = f.get('center', [0, 0])
                            
                            tags = {
                                'name': f.get('text', ''),
                                'name:vi': f.get('text_vi') or f.get('text', ''),
                                'addr:full': f.get('place_name', ''),
                                'phone': props.get('tel'),
                                'website': props.get('website'),
                                'amenity': 'hospital',
                                'source': 'mapbox'
                            }
                            
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

        if mapbox_elements:
            elements = mapbox_elements
        else:
            # === OVERPASS FALLBACK ===
            logger.info("ℹ️ Fallback to Overpass API...")
            query_body = f"""
            (
              node["amenity"~"hospital|clinic"](around:{radius},{latitude},{longitude});
              way["amenity"~"hospital|clinic"](around:{radius},{latitude},{longitude});
              relation["amenity"~"hospital|clinic"](around:{radius},{latitude},{longitude});
            );
            out center;
            """
            
            data = None
            for url in self.OVERPASS_URLS:
                try:
                    full_query = f"[out:json][timeout:25];{query_body}"
                    response = requests.post(url, data={'data': full_query}, timeout=30, headers={'User-Agent': 'MedicalChatbot/1.0'})
                    response.raise_for_status()
                    data = response.json()
                    if 'elements' in data: break
                except Exception as e:
                    logger.warning(f"⚠️ Server {url} failed: {e}")
                    continue
            
            if not data or 'elements' not in data:
                return {'success': False, 'message': 'Hệ thống bản đồ đang quá tải.', 'hospitals': []}
            elements = data.get('elements', [])
        
        if not elements:
            elements = [] # Initialize as empty list to allow CSV injection
        
        hospitals = []
        seen_names = set()
        search_keywords = []
        rag_keywords = []
        
        if specialty:
            try:
                from src.services.hospital_specialty_rag import hybrid_specialty_matching
                rag_keywords = hybrid_specialty_matching(specialty, top_k=5)
                search_keywords.extend(rag_keywords)
            except Exception: pass
            
            normalized_specialty = remove_accents(specialty.lower()).strip()
            for key, values in self.SPECIALTY_KNOWLEDGE_BASE.items():
                if key == normalized_specialty or (len(normalized_specialty) > 3 and normalized_specialty in key):
                    search_keywords.extend(values)
            search_keywords.append(normalized_specialty)
            search_keywords = list(set([k for k in search_keywords if k]))
            
            logger.info(f"🔑 Search Keywords: {search_keywords}")
            logger.info(f"🤖 RAG Keywords: {rag_keywords}")

        # --- STEP 1: INJECT CSV HOSPITALS ---
        # We always want our high-quality CSV data to be candidates.
        # Logic: If it's a SUPER TIER hospital (Prestige >= 0.9), inject it even if far away
        # for specific specialties. Otherwise, use the standard radius.
        csv_candidates = []
        for ch in self.csv_hospitals:
            dist = self.calculate_distance(latitude, longitude, ch['lat'], ch['lng'])
            
            # SUPER TIER CHECK: Always include these regardless of distance if they match specialty keywords
            is_super_tier = ch.get('reputation_score', 0) >= 0.9
            
            # Always include Southern Giants if specialty matches or if they are SUPER TIER
            force_include = False
            if specialty:
                ch_specs = remove_accents(ch.get('specialties', '').lower())
                spec_norm = remove_accents(specialty.lower())
                if spec_norm in ch_specs or any(kw in ch_specs for kw in search_keywords):
                    target_giants = [
                        'Bệnh viện Chợ Rẫy', 'Bệnh viện Đại học Y Dược TP.HCM', 
                        'Bệnh viện Nhân Dân 115', 'Bệnh viện Ung Bướu TP.HCM',
                        'Bệnh viện Từ Dũ', 'Bệnh viện Nhi Đồng 1', 'Bệnh viện Nhi Đồng 2',
                        'Bệnh viện Bình Dân', 'Bệnh viện Hùng Vương'
                    ]
                    if is_super_tier or any(giant in ch['name'] for giant in target_giants):
                        force_include = True

            if dist <= (radius / 1000.0) or force_include:
                csv_candidates.append({
                    'lat': ch['lat'],
                    'lon': ch['lng'],
                    'tags': {
                        'name': ch['name'],
                        'addr:full': ch['address'],
                        'website': ch['booking_url'],
                        'phone': ch.get('phone'),
                        'source': 'csv_database'
                    },
                    'csv_data': ch
                })

        # Merge elements: CSV candidates first to ensure they are the ones "seen" if there are duplicates
        elements = csv_candidates + elements

        # Heuristic for Public Hospitals (Cheapest)
        PUBLIC_HOSPITAL_KEYWORDS = ['cong cong', 'quan', 'huyen', 'thanh pho', 'trung uong', 'chinh phu', 'dan lap', 'nhan dan']
        PRIVATE_HOSPITAL_KEYWORDS = ['quoc te', 'international', 'tu nhan', 'private', 'gia dinh', 'hanh phuc', 'vinmec', 'tam anh', 'fv', 'hoan my']
        BLACKLIST_KEYWORDS = ['yoga', 'spa', 'massage', 'gym', 'the hinh', 'tiem thuoc', 'hieu thuoc', 'thuoc tay', 'kinh thuoc', 'mat kinh', 'kinh mat', 'tham my vien', 'beauty', 'skin clinic', 'da lieu']

        for element in elements:
            tags = element.get('tags', {})
            name = tags.get('name', tags.get('name:vi', ''))
            if not name: continue
            
            name_normalized = remove_accents(name.lower())
            
            # Use unique ID or name to avoid duplicates
            if name_normalized in seen_names: continue
            seen_names.add(name_normalized)
            
            # Filter out non-medical or inappropriate results
            if any(kw in name_normalized for kw in BLACKLIST_KEYWORDS):
                continue
            
            # Special case: If specialty is NOT dermatology, blacklist skin clinics
            current_is_dermatology = specialty and any(kw in remove_accents(specialty.lower()) for kw in ['da lieu', 'mun', 'da'])
            if not current_is_dermatology:
                if any(kw in name_normalized for kw in ['skin', 'da lieu', 'tham my']):
                     continue

            lat = element.get('lat') or element.get('center', {}).get('lat')
            lon = element.get('lon') or element.get('center', {}).get('lon')
            if not lat or not lon: continue
            
            distance = self.calculate_distance(latitude, longitude, lat, lon)
            
            # Check for CSV match (if not already injected)
            csv_data = element.get('csv_data')
            if not csv_data:
                for ch in self.csv_hospitals:
                    if name_normalized == remove_accents(ch['name'].lower()):
                        csv_data = ch
                        break

            # Classification
            is_public = any(kw in name_normalized for kw in PUBLIC_HOSPITAL_KEYWORDS)
            if 'phong kham' in name_normalized or 'tram y te' in name_normalized or 'bac si' in name_normalized:
                is_public = False # Small clinics aren't the intended "public hospital" option
            
            if any(kw in name_normalized for kw in ['quan ', 'huyen ', 'tinh ', 'trung uong']):
                is_public = True

            # Match Specialty keywords for priority
            is_specialty_match = False
            match_reason = []
            priority_score = 0
            
            if specialty:
                # 1. CSV Specialty Match (Highest Priority)
                if csv_data and csv_data.get('specialties'):
                    csv_specs = [remove_accents(s.strip().lower()) for s in csv_data['specialties'].split(',')]
                    normalized_specialty_search = remove_accents(specialty.lower())
                    for spec_kw in csv_specs:
                        if normalized_specialty_search in spec_kw or spec_kw in normalized_specialty_search:
                            priority_score += 5000 
                            match_reason.append("⭐ Đặc biệt phù hợp (Dữ liệu uy tín)")
                            is_specialty_match = True
                            break

                # 2. AI RAG Match
                if not is_specialty_match:
                    for kw in rag_keywords:
                        if kw in name_normalized:
                            priority_score += 2000 
                            match_reason.append("⭐ Phù hợp chuyên khoa")
                            is_specialty_match = True
                            break
                # 3. Knowledge Base Match
                if not is_specialty_match:
                    for kw in search_keywords:
                        # Use word boundary or stricter check for short keywords like "nhi"
                        if len(kw) <= 3:
                            # Match whole word only
                            pattern = rf"\b{re.escape(kw)}\b"
                            if re.search(pattern, name_normalized):
                                priority_score += 1500
                                match_reason.append(f"✅ Khớp chuyên khoa ({kw})")
                                is_specialty_match = True
                                break
                        elif kw in name_normalized:
                            priority_score += 1500
                            match_reason.append(f"✅ Khớp chuyên khoa ({kw})")
                            is_specialty_match = True
                            break
                
                # SPECIAL RULE FOR PEDIATRICS (NHI)
                # If searching for "nhi", and hospital is NOT known for nhi, penalize heavily
                is_pediatric_search = any(k in normalized_specialty for k in ['nhi', 'tre em', 'be', 'so sinh'])
                if is_pediatric_search:
                    is_pediatric_hospital = any(k in name_normalized for k in ['nhi dong', 'tu du', 'hung vuong', 'nhi khoa'])
                    if is_pediatric_hospital:
                        priority_score += 10000 # Massive boost for real pediatric hospitals
                        match_reason.append("👶 Chuyên khoa Nhi tiêu chuẩn")
                        is_specialty_match = True
                    elif not is_specialty_match:
                         # Non-pediatric hospitals get a huge penalty for pediatric queries
                         priority_score -= 10000
                         match_reason.append("❌ Không chuyên về Nhi")
            
            # Prestige Scoring
            is_top_tier = False
            if csv_data:
                # Use reputation score from CSV
                if csv_data['reputation_score'] >= 0.8:
                    is_top_tier = True
            else:
                # STRICT HEURISTIC for non-CSV data
                # Only trust Bệnh viện (Hospitals), never clinics or stations
                if 'benh vien' in name_normalized and any(top in name_normalized for top in self.TOP_TIER_HOSPITALS):
                    is_top_tier = True
            
            if is_top_tier:
                prestige_boost = 5000 if is_specialty_match else 2000
                priority_score += prestige_boost
                match_reason.append("🏛️ Bệnh viện lớn, uy tín đầu ngành")
                
                # Special "Southern Giant" Boost
                target_giants = [
                    'Chợ Rẫy', 'Đại học Y Dược', 'Nhân Dân 115', 'Ung Bướu',
                    'Từ Dũ', 'Nhi Đồng', 'Bình Dân', 'Hùng Vương'
                ]
                if any(giant in name for giant in target_giants):
                    # Nếu là Giant nhưng KHÔNG khớp chuyên khoa, giảm boost để tránh "Ung Bướu" chiếm chỗ "Nhi"
                    giant_boost = 3000 if is_specialty_match else 500
                    priority_score += giant_boost
                    if is_specialty_match:
                        match_reason.append("🌟 Tuyến cuối trung ương/thành phố")
            
            # Penalize small clinics/stations to prevent them ranking as "Top Tier" unless match
            if 'phong kham' in name_normalized or 'tram y te' in name_normalized:
                priority_score -= 1500
                    
            priority_score -= (distance * 5) # Reduced distance penalty even further for specialists
            
            address = tags.get('addr:full') or ', '.join([tags.get(f'addr:{k}', '') for k in ['housenumber', 'street', 'district'] if tags.get(f'addr:{k}')]) or 'Đang cập nhật'
            if csv_data: address = csv_data['address']

            website = tags.get('website', tags.get('contact:website', ''))
            if csv_data: website = csv_data['booking_url']
            if not website:
                for k, v in self.KNOWN_HOSPITAL_URLS.items():
                    if k in name_normalized:
                        website = v
                        break

            # === Weighted Scoring (Revised with User Weights 0.5 / 0.3 / 0.2) ===
            dist_score = 1.0 / (1.0 + distance)
            
            if csv_data:
                prestige_val = csv_data['reputation_score']
                cheapest_val = csv_data['avg_cost_score']
            else:
                # Estimate for unknown
                prestige_val = 1.0 if is_top_tier else 0.0
                cheapest_val = 0.85 if is_public else 0.4
                # Small clinics get very low prestige
                if 'phong kham' in name_normalized or 'tram y te' in name_normalized:
                    prestige_val = 0.1
            
            # If specialty is mentioned but NO MATCH, kill the prestige and nerf distance
            if specialty and not is_specialty_match:
                prestige_val = 0.0
                dist_score = dist_score * 0.001 # Extremely aggressive nerf

            total_weighted_score = (prestige_val * 0.5) + (dist_score * 0.3) + (cheapest_val * 0.2)

            hospitals.append({
                'name': name,
                'address': address,
                'distance': distance,
                'priority_score': priority_score,
                'total_weighted_score': total_weighted_score,
                'match_reasons': match_reason,
                'phone': tags.get('phone', tags.get('contact:phone')),
                'website': website,
                'latitude': lat,
                'longitude': lon,
                'is_public': is_public,
                'is_top_tier': is_top_tier,
                'csv_id': csv_data.get('hospital_id') if csv_data else None
            })
        
        hospitals.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Select Recommendation set
        prestigious = next((h for h in hospitals if h['is_top_tier']), None)
        nearest = min(hospitals, key=lambda x: x['distance']) if hospitals else None
        cheapest = next((h for h in hospitals if h['is_public'] and h['priority_score'] > -500), None)
        # fallback cheapest to just public if scoring too low
        if not cheapest:
            cheapest = next((h for h in hospitals if h['is_public']), None)

        recommendations = {
            'best_prestige': prestigious,
            'nearest': nearest,
            'cheapest': cheapest,
            'best_overall': max(hospitals, key=lambda x: x['total_weighted_score']) if hospitals else None
        }
        
        return {
            'success': True,
            'hospitals': hospitals[:limit],
            'recommendations': recommendations,
            'search_info': {
                'specialty': specialty,
                'latitude': latitude,
                'longitude': longitude
            }
        }

    def format_hospitals_for_chatbot(self, search_result: Dict) -> str:
        hospitals = search_result.get('hospitals', [])
        recs = search_result.get('recommendations', {})
        
        if not hospitals:
            return "Không tìm thấy bệnh viện phù hợp trong khu vực này."
            
        result = "🏥 **KẾT QUẢ GỢI Ý BỆNH VIỆN TỐT NHẤT**\n\n"
        
        # PHẦN : KHUYÊN DÙNG HÀNG ĐẦU (Dựa trên trọng số 0.5 Uy tín - 0.35 Gần - 0.15 Rẻ)
        best_overall = recs.get('best_overall')
        if best_overall:
            result += f"� **GỢI Ý HÀNG ĐẦU: {best_overall['name']}**\n"
            
            lat, lon = best_overall.get('latitude'), best_overall.get('longitude')
            map_link = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}" if lat and lon else f"https://www.google.com/maps/search/?api=1&query={best_overall['name'].replace(' ', '+')}"
            website = best_overall.get('website')
            
            result += f"� [Xem bản đồ chỉ đường]({map_link})"
            if website:
                result += f" | [Đặt lịch / Website]({website})"
            else:
                search_query = f"dat lich kham {best_overall['name']}".replace(" ", "+")
                result += f" | [Tìm đặt lịch (Google)](https://www.google.com/search?q={search_query})"
            
            result += f"\n*(Lý do: Đây là cơ sở có điểm đánh giá tổng hợp cao nhất về uy tín, vị trí và chi phí)*\n"
            # Hidden diagnostic info for developer
            result += f"<!-- DBG: User({search_result.get('latitude')},{search_result.get('longitude')}) Target({lat},{lon}) -->\n\n---\n\n"

        # PHẦN 1: 3 Gợi ý Ưu tiên theo tiêu chí
        if any(recs.values()):
            result += "📍 **3 Lựa chọn tiêu biểu theo tiêu chí của bạn:**\n"
            
            # Kiểm tra xem best_prestige có khớp chuyên khoa không
            requested_specialty = search_result.get('search_info', {}).get('specialty', '')
            best_prestige = recs.get('best_prestige')
            
            if best_prestige:
                # Nếu có yêu cầu chuyên khoa, nhưng thằng "Uy tín nhất" lại không có label "Khớp chuyên khoa"
                # thì ta cảnh báo hoặc ẩn nó đi nếu nó quá lạc quẻ
                is_match = any("Khớp" in r or "phù hợp" in r.lower() for r in best_prestige.get('match_reasons', []))
                
                if requested_specialty and not is_match:
                    # Nếu không khớp, không đưa vào làm "Uy tín nhất" cho chuyên khoa đó
                    pass
                else:
                    result += f"- 🏆 **Uy tín nhất :** {best_prestige['name']} ({best_prestige['distance']}km)\n"
            
            if recs.get('nearest'):
                h = recs['nearest']
                if h != recs.get('best_prestige'):
                    result += f"- 📍 **Gần bạn nhất :** {h['name']} ({h['distance']}km)\n"
                else:
                    result += f"- 📍 **Lựa chọn trên cũng là nơi gần bạn nhất.**\n"
            
            if recs.get('cheapest'):
                h = recs['cheapest']
                if h != recs.get('best_prestige') and h != recs.get('nearest'):
                    result += f"- 💰 **Chi phí hợp lí:** {h['name']} ({h['distance']}km)\n"
            
            result += "\n---\n\n"

        # Phần 2: Chi tiết danh sách
        result += "🔍 **Chi tiết các cơ sở y tế gần đây:**\n\n"
        
        KNOWN_PHONES = {
            'cho ray': '028 3855 4137', 'bach mai': '024 3869 3731', '115': '028 3950 7506',
            'nhi dong 1': '028 3829 5723', 'nhi dong 2': '028 3899 3498', 'tu du': '028 3829 5024',
            'hung vuong': '028 3855 8532', 'viet duc': '024 3825 3531', 'da lieu': '028 3930 8131'
        }
        
        for i, h in enumerate(hospitals[:5], 1): # Chỉ show top 5 chi tiết để tránh quá dài
            icon = "🏥"
            if h.get('is_top_tier'): icon = "🏛️"
            
            result += f"**{i}. {icon} {h['name']}**\n"
            if h.get('match_reasons'):
                result += f"   ✅ {', '.join(h['match_reasons'])}\n"
            
            result += f"   📍 Khoảng cách: ~{h['distance']}km\n"
            result += f"   🏠 Địa chỉ: {h['address']}\n"
            
            phone = h.get('phone')
            if not phone:
                 for k, v in KNOWN_PHONES.items():
                     if k in remove_accents(h['name'].lower()):
                         phone = v
                         break
            if phone: result += f"   📞 {phone}\n"
            
            website = h.get('website')
            if website:
                 result += f"   🌐 [Đặt lịch / Website]({website})\n"
            else:
                 search_query = f"dat lich kham {h['name']}".replace(" ", "+")
                 result += f"   🌐 [Tìm đặt lịch (Google)](https://www.google.com/search?q={search_query})\n"
            
            lat, lon = h.get('latitude'), h.get('longitude')
            map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else f"https://www.google.com/maps/search/?api=1&query={h['name'].replace(' ', '+')}"
            result += f"   🗺️ [Xem bản đồ chỉ đường]({map_link})\n\n"
        
        return result


hospital_finder_service = HospitalFinderService()
