
from flask import request
from flask_restx import Namespace, Resource
import logging
import os
from src.services.pdf_analysis_service import pdf_analysis_service
from src.utils.auth_middleware import token_required
from werkzeug.utils import secure_filename
import io

logger = logging.getLogger(__name__)

medical_report_ns = Namespace('medical-report', description='Medical report analysis from PDF files')

@medical_report_ns.route('/analyze')
class MedicalReportAnalysis(Resource):
    @medical_report_ns.doc('analyze_pdf_report', security='Bearer')
    @token_required
    def post(self, current_user):
        """
        Upload and analyze a medical PDF report.
        """
        try:
            if 'file' not in request.files:
                return {'success': False, 'message': 'No file part in the request'}, 400
            
            file = request.files['file']
            
            if file.filename == '':
                return {'success': False, 'message': 'No file selected'}, 400
            
            ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            if file_ext not in ALLOWED_EXTENSIONS:
                return {'success': False, 'message': f'Unsupported file type: {file_ext}. Supported: {", ".join(ALLOWED_EXTENSIONS)}'}, 400

            # Read file into memory
            file_bytes = file.read()
            
            if not file_bytes:
                return {'success': False, 'message': 'File is empty'}, 400

            logger.info(f"Analyzing {file_ext} report: {file.filename} for user: {current_user['full_name']}")
            
            # Call analysis service
            result = pdf_analysis_service.analyze_medical_report(file_bytes, filename=file.filename)
            
            if result['success']:
                return result, 200
            else:
                return result, 500

        except Exception as e:
            logger.error(f"Error in MedicalReportAnalysis.post: {e}", exc_info=True)
            return {'success': False, 'message': f"Internal server error: {str(e)}"}, 500
