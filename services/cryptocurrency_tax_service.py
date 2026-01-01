"""
Cryptocurrency Tax Reporting Service

Handles cryptocurrency transaction tracking and tax reporting for Form 8949 and Schedule D.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from config.app_config import AppConfig
from models.tax_data import TaxData
from utils.error_tracker import get_error_tracker
from services.exceptions import (
    InvalidInputException,
    DataValidationException,
    ServiceExecutionException
)
from services.error_logger import get_error_logger

logger = logging.getLogger(__name__)


class CryptoTransactionType(Enum):
    """Types of cryptocurrency transactions"""
    BUY = "buy"
    SELL = "sell"
    TRADE = "trade"
    TRANSFER = "transfer"
    MINING = "mining"
    AIRDROP = "airdrop"
    FORK = "fork"
    STAKING = "staking"


class HoldingMethod(Enum):
    """IRS holding period methods"""
    FIFO = "fifo"  # First In, First Out
    LIFO = "lifo"  # Last In, First Out
    SPECIFIC_ID = "specific_id"  # Specific lot identification


@dataclass
class CryptoTransaction:
    """A cryptocurrency transaction"""

    date: date
    type: CryptoTransactionType
    cryptocurrency: str
    amount: Decimal
    price_per_unit: Decimal
    total_value: Decimal
    fees: Decimal
    exchange: str
    transaction_id: str
    description: Optional[str] = None
    related_transaction_id: Optional[str] = None  # For trades

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'date': self.date.isoformat(),
            'type': self.type.value,
            'cryptocurrency': self.cryptocurrency,
            'amount': str(self.amount),
            'price_per_unit': str(self.price_per_unit),
            'total_value': str(self.total_value),
            'fees': str(self.fees),
            'exchange': self.exchange,
            'transaction_id': self.transaction_id,
            'description': self.description,
            'related_transaction_id': self.related_transaction_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CryptoTransaction':
        """Create from dictionary"""
        return cls(
            date=date.fromisoformat(data['date']),
            type=CryptoTransactionType(data['type']),
            cryptocurrency=data['cryptocurrency'],
            amount=Decimal(data['amount']),
            price_per_unit=Decimal(data['price_per_unit']),
            total_value=Decimal(data['total_value']),
            fees=Decimal(data['fees']),
            exchange=data['exchange'],
            transaction_id=data['transaction_id'],
            description=data.get('description'),
            related_transaction_id=data.get('related_transaction_id'),
        )


@dataclass
class CapitalGainLoss:
    """Capital gain/loss from cryptocurrency transaction"""

    description: str
    date_acquired: date
    date_sold: date
    sales_price: Decimal
    cost_basis: Decimal
    gain_loss: Decimal
    holding_period: str  # "short" or "long"
    cryptocurrency: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'description': self.description,
            'date_acquired': self.date_acquired.isoformat(),
            'date_sold': self.date_sold.isoformat(),
            'sales_price': str(self.sales_price),
            'cost_basis': str(self.cost_basis),
            'gain_loss': str(self.gain_loss),
            'holding_period': self.holding_period,
            'cryptocurrency': self.cryptocurrency,
        }


class CryptocurrencyTaxService:
    """
    Service for handling cryptocurrency tax reporting.

    Features:
    - Transaction tracking and storage
    - Cost basis calculation (FIFO method)
    - Capital gains/losses calculation
    - Form 8949 generation data
    - Tax liability estimation
    """

    def __init__(self, config: AppConfig):
        """
        Initialize cryptocurrency tax service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.error_tracker = get_error_tracker()

    def add_transaction(self, tax_data: TaxData, transaction: CryptoTransaction) -> bool:
        """
        Add a cryptocurrency transaction to the tax data.

        Args:
            tax_data: Tax data model
            transaction: Transaction to add

        Returns:
            bool: True if successful
        """
        try:
            # Get existing transactions
            transactions = self.get_transactions(tax_data)

            # Check for duplicate transaction ID
            if any(t.transaction_id == transaction.transaction_id for t in transactions):
                logger.warning(f"Duplicate transaction ID: {transaction.transaction_id}")
                return False

            # Add transaction
            transactions.append(transaction)

            # Save back to tax data
            transaction_dicts = [t.to_dict() for t in transactions]
            tax_data.set("cryptocurrency.transactions", transaction_dicts)

            logger.info(f"Added crypto transaction: {transaction.transaction_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add crypto transaction: {e}")
            self.error_tracker.log_error("crypto_add_transaction", str(e))
            return False

    def get_transactions(self, tax_data: TaxData) -> List[CryptoTransaction]:
        """
        Get all cryptocurrency transactions from tax data.

        Args:
            tax_data: Tax data model

        Returns:
            List[CryptoTransaction]: List of transactions
        """
        try:
            transaction_dicts = tax_data.get("cryptocurrency.transactions", [])
            return [CryptoTransaction.from_dict(t) for t in transaction_dicts]
        except Exception as e:
            logger.error(f"Failed to load crypto transactions: {e}")
            return []

    def calculate_capital_gains_losses(self, tax_data: TaxData, tax_year: int) -> List[CapitalGainLoss]:
        """
        Calculate capital gains and losses for the tax year using FIFO method.

        Args:
            tax_data: Tax data model
            tax_year: Tax year to calculate for

        Returns:
            List[CapitalGainLoss]: List of capital gains/losses
        """
        try:
            transactions = self.get_transactions(tax_data)

            # Filter transactions for the tax year
            year_transactions = [t for t in transactions if t.date.year == tax_year]

            # Group by cryptocurrency
            crypto_holdings = {}  # crypto -> list of (date, amount, cost_basis) tuples

            gains_losses = []

            for transaction in sorted(year_transactions, key=lambda t: t.date):
                crypto = transaction.cryptocurrency

                if crypto not in crypto_holdings:
                    crypto_holdings[crypto] = []

                if transaction.type in [CryptoTransactionType.BUY, CryptoTransactionType.MINING,
                                      CryptoTransactionType.AIRDROP, CryptoTransactionType.FORK,
                                      CryptoTransactionType.STAKING]:
                    # Add to holdings
                    cost_basis_per_unit = transaction.total_value / transaction.amount
                    crypto_holdings[crypto].append({
                        'date': transaction.date,
                        'amount': transaction.amount,
                        'cost_basis_per_unit': cost_basis_per_unit,
                        'remaining': transaction.amount
                    })

                elif transaction.type in [CryptoTransactionType.SELL, CryptoTransactionType.TRADE]:
                    # Remove from holdings using FIFO
                    amount_to_sell = transaction.amount
                    total_cost_basis = Decimal('0')

                    while amount_to_sell > 0 and crypto_holdings[crypto]:
                        holding = crypto_holdings[crypto][0]

                        if holding['remaining'] <= amount_to_sell:
                            # Use entire holding
                            amount_used = holding['remaining']
                            cost_basis_used = amount_used * holding['cost_basis_per_unit']
                            crypto_holdings[crypto].pop(0)
                        else:
                            # Use partial holding
                            amount_used = amount_to_sell
                            cost_basis_used = amount_used * holding['cost_basis_per_unit']
                            holding['remaining'] -= amount_used

                        total_cost_basis += cost_basis_used
                        amount_to_sell -= amount_used

                    # Calculate gain/loss
                    if amount_to_sell == 0:  # All amount was covered by holdings
                        sales_price = transaction.total_value
                        gain_loss = sales_price - total_cost_basis

                        # Determine holding period
                        if crypto_holdings[crypto]:
                            earliest_holding_date = crypto_holdings[crypto][0]['date']
                            holding_period_days = (transaction.date - earliest_holding_date).days
                            holding_period = "long" if holding_period_days > 365 else "short"
                        else:
                            holding_period = "short"  # Default if no holdings remain

                        gains_losses.append(CapitalGainLoss(
                            description=f"{crypto} - {transaction.description or transaction.transaction_id}",
                            date_acquired=crypto_holdings[crypto][0]['date'] if crypto_holdings[crypto] else transaction.date,
                            date_sold=transaction.date,
                            sales_price=sales_price,
                            cost_basis=total_cost_basis,
                            gain_loss=gain_loss,
                            holding_period=holding_period,
                            cryptocurrency=crypto
                        ))

            return gains_losses

        except Exception as e:
            logger.error(f"Failed to calculate crypto gains/losses: {e}")
            self.error_tracker.log_error("crypto_calculate_gains", str(e))
            return []

    def get_tax_liability_estimate(self, tax_data: TaxData, tax_year: int) -> Dict[str, Any]:
        """
        Estimate tax liability from cryptocurrency transactions.

        Args:
            tax_data: Tax data model
            tax_year: Tax year to estimate for

        Returns:
            Dict containing tax estimates
        """
        try:
            gains_losses = self.calculate_capital_gains_losses(tax_data, tax_year)

            short_term_gains = sum(gl.gain_loss for gl in gains_losses if gl.gain_loss > 0 and gl.holding_period == "short")
            short_term_losses = sum(abs(gl.gain_loss) for gl in gains_losses if gl.gain_loss < 0 and gl.holding_period == "short")
            long_term_gains = sum(gl.gain_loss for gl in gains_losses if gl.gain_loss > 0 and gl.holding_period == "long")
            long_term_losses = sum(abs(gl.gain_loss) for gl in gains_losses if gl.gain_loss < 0 and gl.holding_period == "long")

            # Net capital gains (short-term + long-term)
            net_short_term = short_term_gains - short_term_losses
            net_long_term = long_term_gains - long_term_losses
            total_net_capital_gains = net_short_term + net_long_term

            # Estimate tax rates (simplified - would need full tax calculation)
            federal_tax_estimate = self._estimate_federal_tax(total_net_capital_gains, tax_data)

            return {
                'short_term_gains': short_term_gains,
                'short_term_losses': short_term_losses,
                'long_term_gains': long_term_gains,
                'long_term_losses': long_term_losses,
                'net_short_term': net_short_term,
                'net_long_term': net_long_term,
                'total_net_capital_gains': total_net_capital_gains,
                'estimated_federal_tax': federal_tax_estimate,
                'tax_year': tax_year
            }

        except Exception as e:
            logger.error(f"Failed to estimate crypto tax liability: {e}")
            return {}

    def _estimate_federal_tax(self, net_gains: Decimal, tax_data: TaxData) -> Decimal:
        """
        Estimate federal tax on capital gains (simplified calculation).

        Args:
            net_gains: Net capital gains
            tax_data: Tax data model

        Returns:
            Estimated federal tax
        """
        if net_gains <= 0:
            return Decimal('0')

        # Simplified tax brackets for capital gains (2025 rates)
        # Long-term capital gains rates
        if net_gains <= 50000:
            return net_gains * Decimal('0.15')  # 15% bracket
        elif net_gains <= 500000:
            return 50000 * Decimal('0.15') + (net_gains - 50000) * Decimal('0.20')  # 20% bracket
        else:
            return 50000 * Decimal('0.15') + 450000 * Decimal('0.20') + (net_gains - 500000) * Decimal('0.25')  # 25% bracket

    def import_from_csv(self, tax_data: TaxData, csv_path: str) -> Tuple[int, int]:
        """
        Import cryptocurrency transactions from CSV file.

        Args:
            tax_data: Tax data model
            csv_path: Path to CSV file

        Returns:
            Tuple of (successful_imports, failed_imports)
        """
        # This would implement CSV import functionality
        # For now, return placeholder
        return 0, 0

    def export_for_turbotax(self, tax_data: TaxData, tax_year: int) -> str:
        """
        Export cryptocurrency data in format suitable for TurboTax or other tax software.

        Args:
            tax_data: Tax data model
            tax_year: Tax year to export

        Returns:
            CSV formatted string
        """
        try:
            gains_losses = self.calculate_capital_gains_losses(tax_data, tax_year)

            # Create CSV header
            csv_lines = ["Description,Date Acquired,Date Sold,Sales Price,Cost Basis,Gain/Loss,Holding Period,Cryptocurrency"]

            # Add each gain/loss
            for gl in gains_losses:
                line = ",".join([
                    gl.description,
                    gl.date_acquired.isoformat(),
                    gl.date_sold.isoformat(),
                    f"{gl.sales_price:.2f}",
                    f"{gl.cost_basis:.2f}",
                    f"{gl.gain_loss:.2f}",
                    gl.holding_period,
                    gl.cryptocurrency
                ])
                csv_lines.append(line)

            return "\n".join(csv_lines)

        except Exception as e:
            logger.error(f"Failed to export crypto data: {e}")
            return ""