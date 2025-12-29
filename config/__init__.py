"""Configuration package for tax application"""

from .app_config import AppConfig
from .tax_year_config import TaxYearConfig, get_tax_year_config

__all__ = ['AppConfig', 'TaxYearConfig', 'get_tax_year_config']
