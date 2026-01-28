import 'package:http/http.dart' as http;
import 'dart:convert';
// Import các models từ file flutter_models_health_analysis.dart

class HealthAnalysisService {
  final String baseUrl;
  final String? authToken;

  HealthAnalysisService({
    required this.baseUrl,
    this.authToken,
  });

  // Headers chung cho tất cả requests
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (authToken != null) 'Authorization': 'Bearer $authToken',
  };

  /// Lấy phân tích sức khỏe tổng quan
  /// 
  /// Returns: HealthAnalysisResponse hoặc null nếu có lỗi
  Future<HealthAnalysisResponse?> getHealthAnalysis() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/health-profile/analysis'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final jsonData = json.decode(utf8.decode(response.bodyBytes));
        return HealthAnalysisResponse.fromJson(jsonData);
      } else if (response.statusCode == 404) {
        // Chưa có hồ sơ sức khỏe
        print('Health profile not found');
        return null;
      } else {
        print('Error: ${response.statusCode} - ${response.body}');
        return null;
      }
    } catch (e) {
      print('Exception getting health analysis: $e');
      return null;
    }
  }

  /// Lấy lời khuyên chi tiết về sức khỏe
  /// 
  /// Returns: HealthRecommendationsResponse hoặc null nếu có lỗi
  Future<HealthRecommendationsResponse?> getHealthRecommendations() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/health-profile/recommendations'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final jsonData = json.decode(utf8.decode(response.bodyBytes));
        return HealthRecommendationsResponse.fromJson(jsonData);
      } else if (response.statusCode == 404) {
        // Chưa có hồ sơ sức khỏe
        print('Health profile not found');
        return null;
      } else {
        print('Error: ${response.statusCode} - ${response.body}');
        return null;
      }
    } catch (e) {
      print('Exception getting health recommendations: $e');
      return null;
    }
  }
}

// ============================================================================
// VÍ DỤ SỬ DỤNG
// ============================================================================

/*
// 1. Khởi tạo service
final healthService = HealthAnalysisService(
  baseUrl: 'http://localhost:5000',
  authToken: 'your_jwt_token_here',
);

// 2. Lấy phân tích sức khỏe
final analysis = await healthService.getHealthAnalysis();
if (analysis != null) {
  print('BMI: ${analysis.bmi.value}');
  print('Phân loại: ${analysis.bmi.categoryLabel}');
  print('Đánh giá: ${analysis.bmi.assessment}');
  print('Tình trạng tổng quan: ${analysis.overallHealthStatus}');
  
  // Hiển thị lời khuyên BMI
  for (var rec in analysis.bmi.recommendations) {
    print('- $rec');
  }
  
  // Hiển thị phân tích bệnh mãn tính
  for (var condition in analysis.chronicConditionsAnalysis) {
    print('\nBệnh: ${condition.condition}');
    print('Lời khuyên ăn uống:');
    for (var diet in condition.dietRecommendations) {
      print('  - $diet');
    }
  }
}

// 3. Lấy lời khuyên chi tiết
final recommendations = await healthService.getHealthRecommendations();
if (recommendations != null) {
  // Lời khuyên về chế độ ăn
  print('\n=== CHẾ ĐỘ ĂN UỐNG ===');
  print(recommendations.diet.summary);
  print('\nNên ăn:');
  for (var food in recommendations.diet.foodsToInclude) {
    print('✓ $food');
  }
  print('\nNên tránh:');
  for (var food in recommendations.diet.foodsToAvoid) {
    print('✗ $food');
  }
  
  // Lời khuyên về nghỉ ngơi
  print('\n=== NGHỈ NGƠI ===');
  print('Số giờ ngủ: ${recommendations.rest.sleepHours}');
  for (var rec in recommendations.rest.recommendations) {
    print('- $rec');
  }
  
  // Lời khuyên về tập luyện
  print('\n=== TẬP LUYỆN ===');
  print('Tần suất: ${recommendations.exercise.frequency}');
  print('Thời lượng: ${recommendations.exercise.duration}');
  print('Các loại hình:');
  for (var type in recommendations.exercise.types) {
    print('- $type');
  }
  
  // AI Insights
  if (recommendations.aiInsights != null) {
    print('\n=== PHÂN TÍCH TỪ AI ===');
    print(recommendations.aiInsights);
  }
}
*/
