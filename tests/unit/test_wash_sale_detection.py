import pytest
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestWashSaleDetection:
    """Test cases for wash sale detection functionality"""

    @pytest.fixture
    def tax_data(self):
        """Create a TaxData instance for testing"""
        config = AppConfig.from_env()
        return TaxData(config)

    def test_no_wash_sales_when_no_losses(self, tax_data):
        """Test that no wash sales are detected when there are no losses"""
        # Add capital gains with only profits
        tax_data.data['income']['capital_gains'] = [
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '01/01/2024',
                'date_sold': '01/01/2025',
                'gain_loss': 1000.00
            },
            {
                'description': 'Microsoft Corp Common Stock',
                'date_acquired': '01/01/2024',
                'date_sold': '01/01/2025',
                'gain_loss': 2000.00
            }
        ]

        wash_sales = tax_data.detect_wash_sales()
        assert len(wash_sales) == 0

    def test_wash_sale_detected_within_30_days(self, tax_data):
        """Test that wash sales are detected when purchase occurs within 30 days of sale"""
        # Add a loss followed by a purchase of similar security within 30 days
        tax_data.data['income']['capital_gains'] = [
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '01/01/2024',
                'date_sold': '02/01/2025',  # Sale at a loss
                'gain_loss': -1000.00
            },
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '02/15/2025',  # Purchase within 30 days
                'date_sold': '',
                'gain_loss': 0.00
            }
        ]

        wash_sales = tax_data.detect_wash_sales()
        assert len(wash_sales) == 1
        assert wash_sales[0]['sale_index'] == 0
        assert wash_sales[0]['purchase_index'] == 1
        assert wash_sales[0]['loss_amount'] == 1000.00
        assert wash_sales[0]['days_between'] == 14  # Feb 1 to Feb 15

    def test_wash_sale_detected_purchase_before_sale(self, tax_data):
        """Test that wash sales are detected when purchase occurs before sale within 30 days"""
        tax_data.data['income']['capital_gains'] = [
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '01/20/2025',  # Purchase 10 days before sale
                'date_sold': '',
                'gain_loss': 0.00
            },
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '01/01/2024',
                'date_sold': '01/30/2025',  # Sale at a loss
                'gain_loss': -500.00
            }
        ]

        wash_sales = tax_data.detect_wash_sales()
        assert len(wash_sales) == 1
        assert wash_sales[0]['sale_index'] == 1
        assert wash_sales[0]['purchase_index'] == 0
        assert wash_sales[0]['loss_amount'] == 500.00
        assert wash_sales[0]['days_between'] == 10

    def test_no_wash_sale_outside_30_days(self, tax_data):
        """Test that wash sales are not detected when purchase is outside 30-day window"""
        tax_data.data['income']['capital_gains'] = [
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '01/01/2024',
                'date_sold': '02/01/2025',  # Sale at a loss
                'gain_loss': -1000.00
            },
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '04/01/2025',  # Purchase 59 days after sale (outside 30-day window)
                'date_sold': '',
                'gain_loss': 0.00
            }
        ]

        wash_sales = tax_data.detect_wash_sales()
        assert len(wash_sales) == 0

    def test_no_wash_sale_different_securities(self, tax_data):
        """Test that wash sales are not detected for different securities"""
        tax_data.data['income']['capital_gains'] = [
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '01/01/2024',
                'date_sold': '02/01/2025',
                'gain_loss': -1000.00
            },
            {
                'description': 'Microsoft Corp Common Stock',  # Different security
                'date_acquired': '02/15/2025',
                'date_sold': '',
                'gain_loss': 0.00
            }
        ]

        wash_sales = tax_data.detect_wash_sales()
        assert len(wash_sales) == 0

    def test_wash_sale_similar_security_names(self, tax_data):
        """Test that wash sales are detected for similar but not identical security names"""
        tax_data.data['income']['capital_gains'] = [
            {
                'description': 'Apple Inc. Common Stock',
                'date_acquired': '01/01/2024',
                'date_sold': '02/01/2025',
                'gain_loss': -1000.00
            },
            {
                'description': 'Apple Inc Common Stock',  # Slightly different formatting
                'date_acquired': '02/15/2025',
                'date_sold': '',
                'gain_loss': 0.00
            }
        ]

        wash_sales = tax_data.detect_wash_sales()
        assert len(wash_sales) == 1

    def test_multiple_wash_sales(self, tax_data):
        """Test detection of multiple wash sales"""
        tax_data.data['income']['capital_gains'] = [
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '01/01/2024',
                'date_sold': '02/01/2025',
                'gain_loss': -1000.00
            },
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '02/15/2025',
                'date_sold': '',
                'gain_loss': 0.00
            },
            {
                'description': 'Microsoft Corp Common Stock',
                'date_acquired': '01/01/2024',
                'date_sold': '03/01/2025',
                'gain_loss': -500.00
            },
            {
                'description': 'Microsoft Corp Common Stock',
                'date_acquired': '03/15/2025',
                'date_sold': '',
                'gain_loss': 0.00
            }
        ]

        wash_sales = tax_data.detect_wash_sales()
        assert len(wash_sales) == 2

    def test_wash_sale_with_invalid_dates(self, tax_data):
        """Test that invalid dates are handled gracefully"""
        tax_data.data['income']['capital_gains'] = [
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '01/01/2024',
                'date_sold': 'invalid_date',  # Invalid sale date
                'gain_loss': -1000.00
            },
            {
                'description': 'Apple Inc Common Stock',
                'date_acquired': '02/15/2025',
                'date_sold': '',
                'gain_loss': 0.00
            }
        ]

        wash_sales = tax_data.detect_wash_sales()
        assert len(wash_sales) == 0  # Should not crash, just return empty list

    def test_similar_securities_detection(self, tax_data):
        """Test the security similarity detection logic"""
        # Test identical securities
        assert tax_data._are_similar_securities('Apple Inc Common Stock', 'Apple Inc Common Stock') == True

        # Test similar securities
        assert tax_data._are_similar_securities('Apple Inc. Common Stock', 'Apple Inc Common Stock') == True

        # Test different securities
        assert tax_data._are_similar_securities('Apple Inc Common Stock', 'Microsoft Corp Common Stock') == False

        # Test very similar securities
        assert tax_data._are_similar_securities('Apple Inc Common Stock Class A', 'Apple Inc Common Stock Class B') == True

    def test_date_parsing(self, tax_data):
        """Test date parsing functionality"""
        # Test MM/DD/YYYY format
        date1 = tax_data._parse_date('02/15/2025')
        assert date1 is not None
        assert date1.month == 2
        assert date1.day == 15
        assert date1.year == 2025

        # Test invalid date
        assert tax_data._parse_date('invalid') is None
        assert tax_data._parse_date('') is None
        assert tax_data._parse_date(None) is None