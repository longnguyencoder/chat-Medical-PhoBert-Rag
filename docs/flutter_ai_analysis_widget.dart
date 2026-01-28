import 'package:flutter/material.dart';

// Widget để hiển thị phân tích AI trong Health Profile
class AIAnalysisCard extends StatelessWidget {
  final String? aiAnalysis;
  final VoidCallback? onRefresh;

  const AIAnalysisCard({
    Key? key,
    this.aiAnalysis,
    this.onRefresh,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                const Icon(
                  Icons.psychology,
                  color: Colors.blue,
                  size: 28,
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Text(
                    '🤖 Phân tích từ Bác sĩ AI',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                if (onRefresh != null)
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    onPressed: onRefresh,
                    tooltip: 'Làm mới phân tích',
                  ),
              ],
            ),
            const Divider(height: 24),
            
            // Content
            if (aiAnalysis != null && aiAnalysis!.isNotEmpty)
              _buildAnalysisContent(aiAnalysis!)
            else
              _buildEmptyState(),
            
            // Disclaimer
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.orange.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.orange.shade200),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline, 
                    color: Colors.orange.shade700,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Lời khuyên trên chỉ mang tính chất tham khảo. '
                      'Vui lòng tham khảo ý kiến bác sĩ chuyên khoa.',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.orange.shade900,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnalysisContent(String analysis) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            analysis,
            style: const TextStyle(
              fontSize: 14,
              height: 1.6,
              color: Colors.black87,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Icon(
            Icons.analytics_outlined,
            size: 64,
            color: Colors.grey.shade400,
          ),
          const SizedBox(height: 16),
          Text(
            'Chưa có phân tích',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
              color: Colors.grey.shade600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Cập nhật chiều cao và cân nặng để nhận phân tích từ AI',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey.shade500,
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================================
// VÍ DỤ SỬ DỤNG TRONG HEALTH PROFILE SCREEN
// ============================================================================

/*
class HealthProfileScreen extends StatelessWidget {
  final HealthProfile profile;

  const HealthProfileScreen({Key? key, required this.profile}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Hồ sơ Sức khỏe'),
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Thông tin cơ bản
            Card(
              margin: const EdgeInsets.all(16),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildInfoRow('Chiều cao', '${profile.height} cm'),
                    _buildInfoRow('Cân nặng', '${profile.weight} kg'),
                    _buildInfoRow('BMI', '${profile.bmi}'),
                    if (profile.chronicConditions.isNotEmpty)
                      _buildInfoRow('Bệnh mãn tính', 
                        profile.chronicConditions.join(', ')),
                    if (profile.allergies.isNotEmpty)
                      _buildInfoRow('Dị ứng', 
                        profile.allergies.join(', ')),
                  ],
                ),
              ),
            ),
            
            // PHÂN TÍCH TỪ AI - WIDGET MỚI
            AIAnalysisCard(
              aiAnalysis: profile.aiAnalysis,
              onRefresh: () async {
                // Gọi API để cập nhật lại hồ sơ
                // Profile sẽ tự động được phân tích lại
                await _refreshProfile();
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _refreshProfile() async {
    // TODO: Implement refresh logic
  }
}
*/
