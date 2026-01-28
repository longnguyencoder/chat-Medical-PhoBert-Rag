// UPDATED: Health Profile Model với AI Analysis
class HealthProfile {
  final int userId;
  final String? dateOfBirth;
  final int? age;
  final String? gender;
  final String? bloodType;
  final double? height;
  final double? weight;
  final double? bmi;
  final List<String> allergies;
  final List<String> chronicConditions;
  final List<String> medications;
  final String? familyHistory;
  final String? aiAnalysis;  // ← TRƯỜNG MỚI: Phân tích từ AI
  final String? createdAt;
  final String? updatedAt;

  HealthProfile({
    required this.userId,
    this.dateOfBirth,
    this.age,
    this.gender,
    this.bloodType,
    this.height,
    this.weight,
    this.bmi,
    this.allergies = const [],
    this.chronicConditions = const [],
    this.medications = const [],
    this.familyHistory,
    this.aiAnalysis,  // ← THÊM VÀO CONSTRUCTOR
    this.createdAt,
    this.updatedAt,
  });

  factory HealthProfile.fromJson(Map<String, dynamic> json) {
    return HealthProfile(
      userId: json['user_id'] ?? 0,
      dateOfBirth: json['date_of_birth'],
      age: json['age'],
      gender: json['gender'],
      bloodType: json['blood_type'],
      height: json['height']?.toDouble(),
      weight: json['weight']?.toDouble(),
      bmi: json['bmi']?.toDouble(),
      allergies: List<String>.from(json['allergies'] ?? []),
      chronicConditions: List<String>.from(json['chronic_conditions'] ?? []),
      medications: List<String>.from(json['medications'] ?? []),
      familyHistory: json['family_history'],
      aiAnalysis: json['ai_analysis'],  // ← PARSE TRƯỜNG MỚI
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'date_of_birth': dateOfBirth,
      'gender': gender,
      'blood_type': bloodType,
      'height': height,
      'weight': weight,
      'allergies': allergies,
      'chronic_conditions': chronicConditions,
      'medications': medications,
      'family_history': familyHistory,
      // Không gửi ai_analysis lên server vì nó được tạo tự động
    };
  }
}
