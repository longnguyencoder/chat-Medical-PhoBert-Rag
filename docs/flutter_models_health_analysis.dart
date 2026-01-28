// Model cho BMI Analysis
class BmiAnalysis {
  final double? value;
  final String category;
  final String categoryLabel;
  final String assessment;
  final List<String> recommendations;

  BmiAnalysis({
    this.value,
    required this.category,
    required this.categoryLabel,
    required this.assessment,
    required this.recommendations,
  });

  factory BmiAnalysis.fromJson(Map<String, dynamic> json) {
    return BmiAnalysis(
      value: json['value']?.toDouble(),
      category: json['category'] ?? 'unknown',
      categoryLabel: json['category_label'] ?? '',
      assessment: json['assessment'] ?? '',
      recommendations: List<String>.from(json['recommendations'] ?? []),
    );
  }
}

// Model cho Chronic Condition Analysis
class ChronicConditionAnalysis {
  final String condition;
  final String type;
  final List<String> dietRecommendations;
  final List<String> exerciseRecommendations;
  final List<String> monitoring;

  ChronicConditionAnalysis({
    required this.condition,
    required this.type,
    required this.dietRecommendations,
    required this.exerciseRecommendations,
    required this.monitoring,
  });

  factory ChronicConditionAnalysis.fromJson(Map<String, dynamic> json) {
    return ChronicConditionAnalysis(
      condition: json['condition'] ?? '',
      type: json['type'] ?? '',
      dietRecommendations: List<String>.from(json['diet_recommendations'] ?? []),
      exerciseRecommendations: List<String>.from(json['exercise_recommendations'] ?? []),
      monitoring: List<String>.from(json['monitoring'] ?? []),
    );
  }
}

// Model cho Health Analysis Response
class HealthAnalysisResponse {
  final int userId;
  final BmiAnalysis bmi;
  final List<ChronicConditionAnalysis> chronicConditionsAnalysis;
  final String overallHealthStatus;
  final String message;

  HealthAnalysisResponse({
    required this.userId,
    required this.bmi,
    required this.chronicConditionsAnalysis,
    required this.overallHealthStatus,
    required this.message,
  });

  factory HealthAnalysisResponse.fromJson(Map<String, dynamic> json) {
    return HealthAnalysisResponse(
      userId: json['user_id'] ?? 0,
      bmi: BmiAnalysis.fromJson(json['bmi'] ?? {}),
      chronicConditionsAnalysis: (json['chronic_conditions_analysis'] as List?)
          ?.map((item) => ChronicConditionAnalysis.fromJson(item))
          .toList() ?? [],
      overallHealthStatus: json['overall_health_status'] ?? 'unknown',
      message: json['message'] ?? '',
    );
  }
}

// Model cho Diet Recommendations
class DietRecommendations {
  final String summary;
  final List<String> recommendations;
  final List<String> foodsToAvoid;
  final List<String> foodsToInclude;

  DietRecommendations({
    required this.summary,
    required this.recommendations,
    required this.foodsToAvoid,
    required this.foodsToInclude,
  });

  factory DietRecommendations.fromJson(Map<String, dynamic> json) {
    return DietRecommendations(
      summary: json['summary'] ?? '',
      recommendations: List<String>.from(json['recommendations'] ?? []),
      foodsToAvoid: List<String>.from(json['foods_to_avoid'] ?? []),
      foodsToInclude: List<String>.from(json['foods_to_include'] ?? []),
    );
  }
}

// Model cho Rest Recommendations
class RestRecommendations {
  final String sleepHours;
  final String ageGroup;
  final List<String> recommendations;

  RestRecommendations({
    required this.sleepHours,
    required this.ageGroup,
    required this.recommendations,
  });

  factory RestRecommendations.fromJson(Map<String, dynamic> json) {
    return RestRecommendations(
      sleepHours: json['sleep_hours'] ?? '',
      ageGroup: json['age_group'] ?? '',
      recommendations: List<String>.from(json['recommendations'] ?? []),
    );
  }
}

// Model cho Exercise Recommendations
class ExerciseRecommendations {
  final String frequency;
  final String duration;
  final List<String> types;
  final List<String> recommendations;

  ExerciseRecommendations({
    required this.frequency,
    required this.duration,
    required this.types,
    required this.recommendations,
  });

  factory ExerciseRecommendations.fromJson(Map<String, dynamic> json) {
    return ExerciseRecommendations(
      frequency: json['frequency'] ?? '',
      duration: json['duration'] ?? '',
      types: List<String>.from(json['types'] ?? []),
      recommendations: List<String>.from(json['recommendations'] ?? []),
    );
  }
}

// Model cho Health Recommendations Response
class HealthRecommendationsResponse {
  final int userId;
  final DietRecommendations diet;
  final RestRecommendations rest;
  final ExerciseRecommendations exercise;
  final String? aiInsights;
  final String message;

  HealthRecommendationsResponse({
    required this.userId,
    required this.diet,
    required this.rest,
    required this.exercise,
    this.aiInsights,
    required this.message,
  });

  factory HealthRecommendationsResponse.fromJson(Map<String, dynamic> json) {
    return HealthRecommendationsResponse(
      userId: json['user_id'] ?? 0,
      diet: DietRecommendations.fromJson(json['diet'] ?? {}),
      rest: RestRecommendations.fromJson(json['rest'] ?? {}),
      exercise: ExerciseRecommendations.fromJson(json['exercise'] ?? {}),
      aiInsights: json['ai_insights'],
      message: json['message'] ?? '',
    );
  }
}
