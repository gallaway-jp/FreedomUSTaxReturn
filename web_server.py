"""
Web Server for Freedom US Tax Return
Provides mobile-responsive web interface for tax preparation
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import json
from datetime import datetime
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.app_config import AppConfig
from services.tax_calculation_service import TaxCalculationService
from services.tax_analytics_service import TaxAnalyticsService
from services.receipt_scanning_service import ReceiptScanningService
from models.tax_data import TaxData
from services.encryption_service import EncryptionService
from utils.error_tracker import ErrorTracker

class TaxWebServer:
    """Web server for mobile-responsive tax application"""

    def __init__(self):
        self.app = Flask(__name__,
                        template_folder=os.path.join(os.path.dirname(__file__), 'web', 'templates'),
                        static_folder=os.path.join(os.path.dirname(__file__), 'web', 'static'))

        # Configure Flask
        self.app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
        self.app.config['SESSION_TYPE'] = 'filesystem'
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

        # Enable CORS for mobile app integration
        CORS(self.app)

        # Initialize services
        self.config = AppConfig()
        self.encryption = EncryptionService(self.config.key_file)
        self.error_tracker = ErrorTracker(self.config.log_dir)
        self.tax_service = TaxCalculationService()
        self.analytics_service = TaxAnalyticsService(self.config, self.tax_service)
        self.receipt_scanner = ReceiptScanningService(self.config)

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Register routes
        self._register_routes()

        # Initialize session data
        self._init_session_data()

    def _init_session_data(self):
        """Initialize session data structure"""
        if 'tax_data' not in self.app.config:
            self.app.config['tax_data'] = TaxData()
        if 'current_step' not in self.app.config:
            self.app.config['current_step'] = 0

    def _register_routes(self):
        """Register all web routes"""

        @self.app.route('/')
        def index():
            """Main dashboard"""
            return render_template('index.html',
                                 current_year=self.config.get_current_tax_year(),
                                 user_agent=request.headers.get('User-Agent', ''))

        @self.app.route('/start')
        def start_return():
            """Start new tax return"""
            session.clear()
            session['tax_data'] = TaxData().to_dict()
            session['current_step'] = 0
            return redirect(url_for('personal_info'))

        @self.app.route('/personal-info', methods=['GET', 'POST'])
        def personal_info():
            """Personal information entry"""
            if request.method == 'POST':
                # Save personal info
                data = request.get_json()
                tax_data = self._get_tax_data()
                tax_data.set('personal_info', data)
                session['tax_data'] = tax_data.to_dict()
                session['current_step'] = 1
                return jsonify({'success': True})

            tax_data = self._get_tax_data()
            personal_info = tax_data.get('personal_info', {})
            return render_template('personal_info.html',
                                 personal_info=personal_info,
                                 is_mobile=self._is_mobile_device())

        @self.app.route('/filing-status', methods=['GET', 'POST'])
        def filing_status():
            """Filing status selection"""
            if request.method == 'POST':
                data = request.get_json()
                tax_data = self._get_tax_data()
                tax_data.set('filing_status', data.get('filing_status'))
                session['tax_data'] = tax_data.to_dict()
                session['current_step'] = 2
                return jsonify({'success': True})

            tax_data = self._get_tax_data()
            filing_status = tax_data.get('filing_status')
            return render_template('filing_status.html',
                                 filing_status=filing_status,
                                 is_mobile=self._is_mobile_device())

        @self.app.route('/income', methods=['GET', 'POST'])
        def income():
            """Income entry"""
            if request.method == 'POST':
                data = request.get_json()
                tax_data = self._get_tax_data()
                tax_data.set('income', data)
                session['tax_data'] = tax_data.to_dict()
                session['current_step'] = 3
                return jsonify({'success': True})

            tax_data = self._get_tax_data()
            income_data = tax_data.get('income', {})
            return render_template('income.html',
                                 income_data=income_data,
                                 is_mobile=self._is_mobile_device())

        @self.app.route('/deductions', methods=['GET', 'POST'])
        def deductions():
            """Deductions entry"""
            if request.method == 'POST':
                data = request.get_json()
                tax_data = self._get_tax_data()
                tax_data.set('deductions', data)
                session['tax_data'] = tax_data.to_dict()
                session['current_step'] = 4
                return jsonify({'success': True})

            tax_data = self._get_tax_data()
            deductions_data = tax_data.get('deductions', {})
            return render_template('deductions.html',
                                 deductions_data=deductions_data,
                                 is_mobile=self._is_mobile_device())

        @self.app.route('/credits', methods=['GET', 'POST'])
        def credits():
            """Tax credits entry"""
            if request.method == 'POST':
                data = request.get_json()
                tax_data = self._get_tax_data()
                tax_data.set('credits', data)
                session['tax_data'] = tax_data.to_dict()
                session['current_step'] = 5
                return jsonify({'success': True})

            tax_data = self._get_tax_data()
            credits_data = tax_data.get('credits', {})
            return render_template('credits.html',
                                 credits_data=credits_data,
                                 is_mobile=self._is_mobile_device())

        @self.app.route('/payments', methods=['GET', 'POST'])
        def payments():
            """Payments entry"""
            if request.method == 'POST':
                data = request.get_json()
                tax_data = self._get_tax_data()
                tax_data.set('payments', data)
                session['tax_data'] = tax_data.to_dict()
                session['current_step'] = 6
                return jsonify({'success': True})

            tax_data = self._get_tax_data()
            payments_data = tax_data.get('payments', {})
            return render_template('payments.html',
                                 payments_data=payments_data,
                                 is_mobile=self._is_mobile_device())

        @self.app.route('/review')
        def review():
            """Review and calculate taxes"""
            tax_data = self._get_tax_data()
            try:
                result = self.tax_service.calculate_tax(tax_data)
                analytics = self.analytics_service.analyze_tax_data(tax_data, result)
                session['current_step'] = 7
                return render_template('review.html',
                                     tax_data=tax_data,
                                     result=result,
                                     analytics=analytics,
                                     is_mobile=self._is_mobile_device())
            except Exception as e:
                self.error_tracker.log_error(e, "Tax calculation failed")
                return render_template('error.html',
                                     error=str(e),
                                     is_mobile=self._is_mobile_device())

        @self.app.route('/analytics')
        def analytics():
            """Tax analytics dashboard"""
            tax_data = self._get_tax_data()
            try:
                result = self.tax_service.calculate_tax(tax_data)
                analytics_data = self.analytics_service.analyze_tax_data(tax_data, result)
                return render_template('analytics.html',
                                     analytics=analytics_data,
                                     is_mobile=self._is_mobile_device())
            except Exception as e:
                self.error_tracker.log_error(e, "Analytics calculation failed")
                return render_template('error.html',
                                     error=str(e),
                                     is_mobile=self._is_mobile_device())

        @self.app.route('/api/calculate', methods=['POST'])
        def api_calculate():
            """API endpoint for tax calculation"""
            try:
                data = request.get_json()
                tax_data = TaxData.from_dict(data)
                result = self.tax_service.calculate_tax(tax_data)
                return jsonify({
                    'success': True,
                    'result': result.to_dict()
                })
            except Exception as e:
                self.error_tracker.log_error(e, "API calculation failed")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400

        @self.app.route('/api/save', methods=['POST'])
        def api_save():
            """API endpoint for saving tax data"""
            try:
                data = request.get_json()
                tax_data = TaxData.from_dict(data)

                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tax_return_{timestamp}.json"

                # Encrypt and save
                encrypted_data = self.encryption.encrypt(json.dumps(data))
                filepath = os.path.join(self.config.get_data_directory(), filename)

                with open(filepath, 'wb') as f:
                    f.write(encrypted_data)

                return jsonify({
                    'success': True,
                    'filename': filename
                })
            except Exception as e:
                self.error_tracker.log_error(e, "Save failed")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/load/<filename>', methods=['GET'])
        def api_load(filename):
            """API endpoint for loading tax data"""
            try:
                filepath = os.path.join(self.config.get_data_directory(), filename)

                with open(filepath, 'rb') as f:
                    encrypted_data = f.read()

                decrypted_data = self.encryption.decrypt(encrypted_data)
                data = json.loads(decrypted_data)

                return jsonify({
                    'success': True,
                    'data': data
                })
            except Exception as e:
                self.error_tracker.log_error(e, "Load failed")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/scan-document', methods=['POST'])
        def scan_document():
            """Mobile document scanning endpoint"""
            try:
                if 'file' not in request.files:
                    return jsonify({'success': False, 'error': 'No file provided'}), 400

                file = request.files['file']
                if file.filename == '':
                    return jsonify({'success': False, 'error': 'No file selected'}), 400

                # Save uploaded file
                upload_dir = os.path.join(self.config.get_data_directory(), 'uploads')
                os.makedirs(upload_dir, exist_ok=True)

                filename = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)

                # Implement OCR processing using receipt scanning service
                try:
                    scan_result = self.receipt_scanner.scan_receipt(filepath)
                    
                    return jsonify({
                        'success': True,
                        'filename': filename,
                        'scan_result': {
                            'vendor_name': scan_result.vendor_name,
                            'total_amount': str(scan_result.total_amount),
                            'tax_amount': str(scan_result.tax_amount) if scan_result.tax_amount else None,
                            'date': scan_result.date.isoformat() if scan_result.date else None,
                            'category': scan_result.category,
                            'confidence': scan_result.confidence_score,
                            'line_items': [
                                {
                                    'description': item.description,
                                    'amount': str(item.amount),
                                    'category': item.category
                                } for item in scan_result.line_items
                            ] if scan_result.line_items else []
                        },
                        'message': 'Document scanned and processed successfully'
                    })
                except Exception as ocr_error:
                    self.logger.warning(f"OCR processing failed: {ocr_error}")
                    # Fall back to basic upload acknowledgment
                    return jsonify({
                        'success': True,
                        'filename': filename,
                        'message': 'Document uploaded successfully (OCR processing unavailable)',
                        'warning': 'OCR processing failed, but document was saved'
                    })
            except Exception as e:
                self.error_tracker.log_error(e, "Document scan failed")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/load-data', methods=['POST'])
        def api_load_data():
            """API endpoint for loading tax data directly from client"""
            try:
                data = request.get_json()

                # Validate the data structure
                if not isinstance(data, dict):
                    return jsonify({
                        'success': False,
                        'error': 'Invalid data format'
                    }), 400

                # Create TaxData object to validate
                tax_data = TaxData.from_dict(data)

                # Store in session
                session['tax_data'] = data
                session['current_step'] = 1  # Mark as having data loaded

                return jsonify({
                    'success': True,
                    'message': 'Tax data loaded successfully'
                })
            except Exception as e:
                self.error_tracker.log_error(e, "Load data failed")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

    def _get_tax_data(self):
        """Get tax data from session"""
        data = session.get('tax_data', TaxData().to_dict())
        return TaxData.from_dict(data)

    def _is_mobile_device(self):
        """Check if request is from mobile device"""
        user_agent = request.headers.get('User-Agent', '').lower()
        mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'windows phone']
        return any(keyword in user_agent for keyword in mobile_keywords)

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the web server"""
        self.logger.info(f"Starting Tax Web Server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    server = TaxWebServer()
    server.run(debug=True)