
import math

def calculate_distance(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return round(6371 * c, 2)

# Binh Loi to Hanh Phuc
print(f"Binh Loi to Hanh Phuc: {calculate_distance(10.825, 106.705, 10.8934, 106.7112)} km")

# Binh Loi to An Binh
print(f"Binh Loi to An Binh: {calculate_distance(10.825, 106.705, 10.8211, 106.7011)} km")

# Binh Loi to Quan y 4
print(f"Binh Loi to Quan y 4: {calculate_distance(10.825, 106.705, 10.825, 10.697)} km")
