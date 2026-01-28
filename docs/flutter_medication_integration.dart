import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';

// ============================================================================
// MODELS
// ============================================================================

class MedicationSchedule {
  final int scheduleId;
  final int userId;
  final String medicationName;
  final String dosage;
  final String frequency;
  final List<String> timeOfDay;
  final DateTime? startDate;
  final DateTime? endDate;
  final String notes;
  final bool isActive;

  MedicationSchedule({
    required this.scheduleId,
    required this.userId,
    required this.medicationName,
    required this.dosage,
    required this.frequency,
    required this.timeOfDay,
    this.startDate,
    this.endDate,
    required this.notes,
    required this.isActive,
  });

  factory MedicationSchedule.fromJson(Map<String, dynamic> json) {
    return MedicationSchedule(
      scheduleId: json['schedule_id'],
      userId: json['user_id'],
      medicationName: json['medication_name'],
      dosage: json['dosage'] ?? '',
      frequency: json['frequency'] ?? 'daily',
      timeOfDay: List<String>.from(json['time_of_day'] ?? []),
      startDate: json['start_date'] != null ? DateTime.parse(json['start_date']) : null,
      endDate: json['end_date'] != null ? DateTime.parse(json['end_date']) : null,
      notes: json['notes'] ?? '',
      isActive: json['is_active'] ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'medication_name': medicationName,
      'dosage': dosage,
      'frequency': frequency,
      'time_of_day': timeOfDay,
      'start_date': startDate?.toIso8601String().split('T')[0],
      'end_date': endDate?.toIso8601String().split('T')[0],
      'notes': notes,
      'is_active': isActive,
    };
  }
}

class MedicationLog {
  final int logId;
  final int scheduleId;
  final int userId;
  final DateTime scheduledTime;
  final DateTime? actualTime;
  final String status; // 'pending', 'taken', 'skipped'
  final String? note;
  final bool isOverdue;

  MedicationLog({
    required this.logId,
    required this.scheduleId,
    required this.userId,
    required this.scheduledTime,
    this.actualTime,
    required this.status,
    this.note,
    required this.isOverdue,
  });

  factory MedicationLog.fromJson(Map<String, dynamic> json) {
    return MedicationLog(
      logId: json['log_id'],
      scheduleId: json['schedule_id'],
      userId: json['user_id'],
      // Lưu ý: Backend trả về ISO string, cần parse cẩn thận
      scheduledTime: DateTime.parse(json['scheduled_time']).toLocal(), 
      actualTime: json['actual_time'] != null ? DateTime.parse(json['actual_time']).toLocal() : null,
      status: json['status'],
      note: json['note'],
      isOverdue: json['is_overdue'] ?? false,
    );
  }
}

class ComplianceStats {
  final int total;
  final int taken;
  final int skipped;
  final int pending;
  final double complianceRate;

  ComplianceStats({
    required this.total,
    required this.taken,
    required this.skipped,
    required this.pending,
    required this.complianceRate,
  });

  factory ComplianceStats.fromJson(Map<String, dynamic> json) {
    return ComplianceStats(
      total: json['total'],
      taken: json['taken'],
      skipped: json['skipped'],
      pending: json['pending'],
      complianceRate: (json['compliance_rate'] ?? 0.0).toDouble(),
    );
  }
}

// ============================================================================
// SERVICE
// ============================================================================

class MedicationService {
  final String baseUrl; // Ví dụ: "http://10.0.2.2:5000/api"
  final String token;   // JWT Token

  MedicationService({required this.baseUrl, required this.token});

  // 1. Lấy danh sách lịch thuốc
  Future<List<MedicationSchedule>> getSchedules() async {
    final response = await http.get(
      Uri.parse('$baseUrl/medication/schedules'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      final List<dynamic> schedulesJson = data['schedules'];
      return schedulesJson.map((json) => MedicationSchedule.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load schedules: ${response.body}');
    }
  }

  // 2. Tạo lịch thuốc mới
  Future<MedicationSchedule> createSchedule(MedicationSchedule schedule) async {
    final response = await http.post(
      Uri.parse('$baseUrl/medication/schedules'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: json.encode(schedule.toJson()),
    );

    if (response.statusCode == 201) {
      final data = json.decode(response.body);
      return MedicationSchedule.fromJson(data['schedule']);
    } else {
      throw Exception('Failed to create schedule: ${response.body}');
    }
  }

  // 3. Lấy danh sách log (lịch sử/lịch hôm nay)
  Future<List<MedicationLog>> getLogs({DateTime? startDate, DateTime? endDate}) async {
    String query = '';
    if (startDate != null) query += 'start_date=${startDate.toIso8601String().split('T')[0]}&';
    if (endDate != null) query += 'end_date=${endDate.toIso8601String().split('T')[0]}';

    final response = await http.get(
      Uri.parse('$baseUrl/medication/logs?$query'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      final List<dynamic> logsJson = data['logs'];
      return logsJson.map((json) => MedicationLog.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load logs: ${response.body}');
    }
  }

  // 4. Update trạng thái uống thuốc (Check-in)
  Future<MedicationLog> updateLogStatus(int logId, String status) async {
    final response = await http.post(
      Uri.parse('$baseUrl/medication/logs'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: json.encode({
        'log_id': logId,
        'status': status, // 'taken' or 'skipped'
      }),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return MedicationLog.fromJson(data['log']);
    } else {
      throw Exception('Failed to update log: ${response.body}');
    }
  }
}
