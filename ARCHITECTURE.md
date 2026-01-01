# System Architecture Documentation

**Freedom US Tax Return Application**  
**Version**: 2.0.0  
**Last Updated**: January 2026  
**Maintainability Score**: 8.0/10 (Target: 9.0)

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Architecture Diagram](#system-architecture-diagram)
3. [Core Components](#core-components)
4. [Service Layer](#service-layer)
5. [Data Layer](#data-layer)
6. [User Interface Layer](#user-interface-layer)
7. [Configuration & Constants](#configuration--constants)
8. [Utilities](#utilities)
9. [Integration Points](#integration-points)
10. [Data Flow](#data-flow)
11. [Technology Stack](#technology-stack)
12. [Design Patterns](#design-patterns)
13. [Security Architecture](#security-architecture)
14. [Error Handling Architecture](#error-handling-architecture)
15. [Deployment Architecture](#deployment-architecture)

---

## Architecture Overview

The Freedom US Tax Return application follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  (CustomTkinter GUI, Web Interface, CLI)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Business Logic Layer                       │
│  (24 Services: Tax Calculation, Filing, Analysis, etc.)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Data Layer                                │
│  (Models, Serialization, External API Integration)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Infrastructure Layer                            │
│  (File System, Database, Encryption, Logging)               │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Service-Oriented Architecture**: Business logic encapsulated in 24 specialized services
2. **Layered Design**: Clear separation between UI, business logic, data, and infrastructure
3. **Dependency Injection**: Services receive dependencies through constructor
4. **Error Handling**: Centralized exception hierarchy with comprehensive logging
5. **Configuration Management**: Environment-specific configurations with sensible defaults
6. **Encryption-First**: Sensitive data encrypted at rest and in transit
7. **Audit Logging**: All data changes tracked for compliance

---

## System Architecture Diagram

### High-Level Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                   GUI Layer                                      │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐   │
│  │ Main Window  │  Form Pages  │  Widgets     │  Dialog      │   │
│  │ (Sidebar Nav)│ (Interview)  │ (Input Fields)│ (Settings)   │   │
│  └──────────────┴──────────────┴──────────────┴──────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    Event Handlers & Commands
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                   Service Orchestration Layer                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Service Factory / Container                  │   │
│  │              (Dependency Injection)                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                               │                                   │
│  ┌────────────────────────────┼────────────────────────────┐    │
│  │                            │                            │    │
│  ▼                            ▼                            ▼    │
│ ┌────────────────────┐ ┌─────────────────┐ ┌──────────────┐   │
│ │ Tax Services (5)   │ │ Data Services   │ │ UI Services  │   │
│ │ - Calculation      │ │ - Interview     │ │ - Analytics  │   │
│ │ - Planning         │ │ - Recommendation│ │ - Planning   │   │
│ │ - Analytics        │ │ - Form Mapper   │ │ - Reporting  │   │
│ │ - Filing           │ │ - Validation    │ │              │   │
│ │ - Reporting        │ └─────────────────┘ └──────────────┘   │
│ └────────────────────┘                                          │
│                                                                  │
│  ┌────────────────────┐ ┌──────────────────┐ ┌──────────────┐ │
│  │ Integration (6)    │ │ Entity Services  │ │Util Services │ │
│  │ - E-Filing         │ │ - Partnership    │ │- Encryption  │ │
│  │ - Bank Linking     │ │ - S-Corp         │ │- Audit Trail │ │
│  │ - State Tax        │ │ - Estate/Trust   │ │- Backup      │ │
│  │ - QuickBooks       │ │ - Crypto         │ │- Collab.     │ │
│  │ - Receipt Scanning │ │ - FBAR/Foreign   │ └──────────────┘ │
│  │ - Cloud Backup     │ └──────────────────┘                   │
│  └────────────────────┘                                          │
└─────────────────────────┬──────────────────────────────────────┘
                          │
         Data Models & Serialization
                          │
┌─────────────────────────▼──────────────────────────────────────┐
│                  Data Layer                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ TaxData Model                                            │  │
│  │ ├─ Personal Info    ├─ Income          ├─ Deductions   │  │
│  │ ├─ Filing Status    ├─ Credits         ├─ Adjustments  │  │
│  │ ├─ Dependents       ├─ Investments     ├─ Payments     │  │
│  │ └─ Address          └─ Business Income └─ Carryovers   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│  ┌────────────────────────┼────────────────────────────────┐   │
│  │                        │                                │   │
│  ▼                        ▼                                ▼   │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│ │ JSON Serializ│ │ File Storage  │ │ External APIs    │   │
│ │ (Encrypted)  │ │ (Encrypted)   │ │ (Bank, IRS, etc.)│   │
│ └──────────────┘ └──────────────┘ └──────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────────┐
│            Infrastructure / Persistence Layer                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ File System │ Encryption │ Audit Logging │ Error Logging │  │
│  │             │ (Fernet)   │ (SQL/JSON)    │ (File-based)  │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Models (`/models`)

**Purpose**: Data structure definitions for tax return entities

**Key Files**:
- `tax_data.py` - Main TaxData class (central data container)
- Individual entity models for income, deductions, credits

**Characteristics**:
- Dataclass-based structures with type hints
- Support for nested objects (income, deductions, credits)
- Serialization to/from JSON
- Validation on creation

**Example Structure**:
```python
@dataclass
class TaxData:
    tax_year: int
    personal_info: PersonalInfo
    filing_status: FilingStatus
    dependents: List[Dependent]
    income: Income
    deductions: Deductions
    credits: Credits
    payments: Payments
    # ... many more fields
```

### 2. Configuration (`/config`)

**Purpose**: Application configuration management

**Key Files**:
- `app_config.py` - Main application configuration
- `tax_year_config.py` - Tax year-specific configurations
- `dependencies.py` - Service dependency definitions

**Configuration Types**:
- **Tax Year**: Standard deductions, tax brackets, limits (2024-2026)
- **Application**: File paths, logging levels, feature flags
- **Feature Flags**: Beta features, experimental functionality

**Access Pattern**:
```python
from config.app_config import AppConfig

config = AppConfig()
standard_deduction = config.standard_deductions['single']
```

### 3. Constants (`/constants`)

**Purpose**: Application-wide constants and enumerations

**Key Files**:
- `pdf_fields.py` - Tax form PDF field mappings (Form 1040, etc.)

**Data**:
- Form field positions and names
- Enumeration constants
- Validation rules

---

## Service Layer

### Service Organization

**24 Total Services** organized into 6 functional groups:

#### Group 1: Tax Calculation Services (5)

1. **tax_calculation_service.py**
   - Complete tax return calculation
   - Income aggregation
   - Deduction selection (standard vs. itemized)
   - Tax bracket calculations
   - Withholding vs. actual tax

2. **tax_planning_service.py**
   - What-if scenario analysis
   - Tax projections
   - Estimated tax payment calculations
   - Withholding optimization
   - Retirement contribution planning

3. **tax_analytics_service.py**
   - Effective tax rate analysis
   - Tax burden analysis
   - Deduction utilization analysis
   - Multi-year trend analysis
   - Income vs. tax comparisons

4. **state_tax_service.py**
   - State-specific calculations
   - Multi-state filing logic
   - State tax credits
   - State-specific forms (41 states + DC)

5. **tax_year_service.py**
   - Multi-year tax return management
   - Year-over-year comparison
   - Carryover tracking (losses, credits)
   - Prior year data migration

#### Group 2: Interview & Recommendation Services (3)

1. **tax_interview_service.py**
   - Question-based tax form guidance
   - Conversational interview flow
   - Data collection and validation
   - Form requirement determination

2. **form_recommendation_service.py**
   - Intelligent form suggestions
   - Priority-based recommendations
   - Required vs. optional form determination
   - Interconnected form analysis

3. **ai_deduction_finder_service.py**
   - AI-powered deduction discovery
   - Pattern matching on income/expenses
   - Missed deduction identification
   - Confidence scoring

#### Group 3: Integration Services (6)

1. **e_filing_service.py**
   - IRS electronic filing integration
   - XMLS generation for e-filing
   - Validation against IRS requirements
   - Filing status tracking

2. **bank_account_linking_service.py**
   - Bank account authentication (OAuth 2.0)
   - Transaction data retrieval
   - Automatic categorization
   - Interest/dividend extraction

3. **state_tax_integration_service.py**
   - Multi-state e-filing
   - State-specific requirements
   - Form generation per state
   - Filing deadline tracking

4. **quickbooks_integration_service.py**
   - QuickBooks Online/Desktop sync
   - Chart of accounts mapping
   - Transaction import
   - Accounting category to tax category mapping

5. **receipt_scanning_service.py**
   - OCR for receipt scanning
   - Expense extraction
   - Category classification
   - Confidence scoring

6. **cloud_backup_service.py**
   - Encrypted cloud backup
   - Multi-provider support
   - Automatic backup scheduling
   - Version control

#### Group 4: Entity Services (4)

1. **partnership_s_corp_service.py**
   - Form 1065 (partnerships)
   - Form 1120-S (S-Corps)
   - K-1 generation
   - Pass-through income distribution

2. **estate_trust_service.py**
   - Form 1041 (estates/trusts)
   - Beneficiary income allocation
   - Distributed vs. undistributed income

3. **cryptocurrency_tax_service.py**
   - Crypto transaction tracking
   - Capital gains/losses calculation
   - Form 8949 support
   - Multiple holding methods (FIFO, LIFO, specific)

4. **foreign_income_fbar_service.py**
   - Form 1116 (foreign tax credit)
   - FBAR (Form 114) requirements
   - Foreign account reporting
   - FATCA compliance

#### Group 5: Infrastructure Services (4)

1. **authentication_service.py**
   - User authentication
   - Master password management
   - Session management
   - PTIN/ERO authentication

2. **encryption_service.py**
   - Data encryption/decryption (Fernet)
   - Key management
   - Secure password hashing

3. **audit_trail_service.py**
   - Change tracking
   - User action logging
   - Compliance documentation
   - Data modification history

4. **collaboration_service.py**
   - Sharing tax returns
   - Comment/annotation system
   - Review mode
   - Access control (read/edit permissions)

#### Group 6: Utility Services (2)

1. **accessibility_service.py**
   - Section 508 compliance
   - WCAG 2.1 AA standards
   - Screen reader support
   - Keyboard navigation

2. **ptin_ero_service.py**
   - PTIN (Preparer Tax ID) validation
   - ERO (Electronic Return Originator) credentials
   - Professional authentication
   - IRS compliance verification

### Service Communication Pattern

**All services follow this pattern**:

```python
from services.exceptions import *
from services.error_logger import get_error_logger

class MyService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.error_logger = get_error_logger()
    
    def process_data(self, data: InputType) -> OutputType:
        """
        Process data with comprehensive error handling.
        
        Raises:
            InvalidInputException: If input is invalid
            ServiceExecutionException: If processing fails
        """
        try:
            # Validate input
            if not data:
                raise InvalidInputException("data")
            
            # Process
            result = self._process(data)
            
            # Validate output
            if not result:
                raise DataValidationException("Result is invalid")
            
            return result
        except (InvalidInputException, DataValidationException) as e:
            self.error_logger.log_exception(e, context=f"{self.__class__.__name__}.process_data")
            raise
        except Exception as e:
            self.error_logger.log_exception(e, context=f"{self.__class__.__name__}.process_data")
            raise ServiceExecutionException(
                service_name=self.__class__.__name__,
                operation="process_data",
                details={"error": str(e)}
            ) from e
```

---

## Data Layer

### TaxData Model

The `TaxData` class is the central data container for all tax return information:

```
TaxData (Root)
├─ tax_year: int
├─ personal_info: PersonalInfo
│  ├─ first_name, last_name
│  ├─ ssn, dob, address
│  └─ contact_info
├─ filing_status: FilingStatus
│  ├─ status (Single, MFJ, MFS, HOH, QW)
│  ├─ spouse_name, spouse_ssn
│  └─ marriage_date
├─ dependents: List[Dependent]
│  ├─ name, ssn, dob
│  ├─ relationship, qualification_code
│  └─ months_lived_with
├─ income: Income
│  ├─ w2_forms: List[W2]
│  ├─ interest_income: List[InterestIncome]
│  ├─ dividend_income: List[DividendIncome]
│  ├─ business_income: List[BusinessIncome]
│  ├─ capital_gains_losses: List[CapitalGain]
│  ├─ rental_income: List[RentalIncome]
│  ├─ foreign_income: List[ForeignIncome]
│  └─ other_income: Dict[str, float]
├─ deductions: Deductions
│  ├─ medical_expenses: float
│  ├─ state_local_taxes: float
│  ├─ mortgage_interest: float
│  ├─ charitable_contributions: float
│  ├─ casualty_losses: float
│  └─ business_expenses: Dict[str, float]
├─ credits: Credits
│  ├─ child_tax_credit: float
│  ├─ earned_income_credit: float
│  ├─ education_credits: float
│  ├─ energy_credits: float
│  └─ other_credits: Dict[str, float]
├─ payments: Payments
│  ├─ federal_withholding: float
│  ├─ estimated_tax_payments: List[Payment]
│  └─ other_payments: Dict[str, float]
└─ metadata: Dict[str, Any]
   ├─ last_modified: datetime
   ├─ created: datetime
   ├─ version: str
   └─ notes: str
```

### Data Serialization

**Format**: JSON (encrypted at rest)

**Serialization Pattern**:
```python
# Save
tax_data_dict = dataclasses.asdict(tax_data)
encrypted_json = encryption_service.encrypt(json.dumps(tax_data_dict))
# Save to file

# Load
encrypted_json = read_from_file()
decrypted_json = encryption_service.decrypt(encrypted_json)
tax_data_dict = json.loads(decrypted_json)
tax_data = TaxData(**tax_data_dict)
```

### Multi-Year Data Structure

**Purpose**: Support multiple tax years in single file

**Structure**:
```python
{
    "metadata": {
        "app_version": "2.0.0",
        "current_year": 2025,
        "created": "2024-01-15T10:30:00Z"
    },
    "years": {
        "2024": { TaxData for 2024 },
        "2025": { TaxData for 2025 },
        "2026": { TaxData for 2026 }
    }
}
```

---

## User Interface Layer

### Architecture

**Technology**: CustomTkinter (modern Python UI framework)

**Pattern**: Model-View-Controller (MVC)
- **Model**: TaxData
- **View**: Window/Page/Widget classes
- **Controller**: Service layer

### UI Components Structure

```
/gui
├─ __init__.py
├─ main_window.py (MODERN - Sidebar-based navigation)
├─ main_window_legacy.py (Traditional menu bar)
├─ pages/ (Form pages for tax interview)
│  ├─ personal_info_page.py
│  ├─ income_page.py
│  ├─ deductions_page.py
│  └─ ... (more form pages)
├─ widgets/ (Reusable UI components)
│  ├─ text_input.py
│  ├─ numeric_input.py
│  ├─ date_picker.py
│  └─ ... (more widgets)
└─ dialogs/ (Dialog windows)
   ├─ settings_dialog.py
   ├─ about_dialog.py
   └─ ... (more dialogs)
```

### Main Window (Modern Implementation)

**Features**:
- Sidebar-based navigation (Discord/Slack style)
- Organized sections: Primary Actions, Tax Forms, View, File, Security, Help
- Scrollable content area
- Status bar with application status
- Theme support (light/dark)

**Navigation Structure**:
1. **Primary Actions**
   - New Return
   - Open Return
   - Quick Start Interview

2. **Tax Forms**
   - Form 1040 (Main return)
   - Schedules (A, B, C, D, etc.)
   - Supporting forms (8949, etc.)

3. **View**
   - Dashboard
   - Tax Summary
   - Forms Overview
   - Tax Planning

4. **File**
   - Save
   - Export (PDF, etc.)
   - Print
   - Recent Files

5. **Security**
   - Settings
   - Backup
   - Access Control

6. **Help**
   - Documentation
   - IRS Resources
   - Contact Support

---

## Configuration & Constants

### Tax Year Configuration

**Location**: `config/tax_year_config.py`

**Configurable by Year**:
```python
{
    "year": 2025,
    "standard_deductions": {
        "single": 14600,
        "mfj": 29200,
        "mfs": 14600,
        "hoh": 21900
    },
    "tax_brackets": {
        "single": [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            # ... more brackets
        ]
    },
    "other_limits": {
        "child_tax_credit": 2000,
        "earned_income_credit_max": 3733,
        # ... many more
    }
}
```

### Application Configuration

**Location**: `config/app_config.py`

**Settings**:
- Default file paths
- Logging configuration
- Feature flags
- UI theme
- Tax year list
- Supported states

---

## Utilities

### Core Utilities (`/utils`)

1. **tax_calculations.py**
   - Income tax calculation by bracket
   - Self-employment tax
   - Standard deduction selection
   - Tax credit calculations

2. **error_tracker.py**
   - Legacy error tracking (being replaced by error_logger)
   - Error categorization

3. **encryption.py**
   - Password hashing
   - Data encryption helpers

4. **validators.py**
   - Income validation
   - Address validation
   - Tax ID validation
   - Numeric range validation

5. **event_bus.py**
   - Application event system
   - Event subscription/publishing
   - Event types enumeration

---

## Integration Points

### External Service Integrations

#### 1. Banking APIs
- **Plaid**: Account linking, transaction retrieval
- **Bank of America**, **Chase**, **Fidelity**: Direct APIs
- **Pattern**: OAuth 2.0 authentication
- **Purpose**: Automatic transaction categorization

#### 2. IRS Systems
- **XMLS Validation**: IRS validation rules
- **e-Services**: Electronic filing
- **Pattern**: Secure XML submission
- **Purpose**: Tax return filing

#### 3. Accounting Systems
- **QuickBooks Online**: OAuth 2.0 API
- **QuickBooks Desktop**: Web Connect
- **Pattern**: Sync chart of accounts, import transactions
- **Purpose**: Automatic data import

#### 4. State Tax Agencies
- **SOAP/REST APIs**: State-specific submission
- **Pattern**: Varies by state
- **Purpose**: Multi-state filing

#### 5. Cloud Storage
- **AWS S3**: Encrypted backup
- **Google Drive**: Cloud backup option
- **Microsoft OneDrive**: Cloud backup option
- **Pattern**: AES-256 encryption, client-side encryption
- **Purpose**: Secure offsite backup

#### 6. Receipt Processing
- **OCR Engine**: Tesseract/AWS Textract
- **Pattern**: Image→Text→Extraction
- **Purpose**: Automated receipt scanning

### Integration Error Handling

All integrations use the exception hierarchy:
- `ServiceUnavailableException`: Service down or unreachable
- `ServiceExecutionException`: API call failed
- `DataImportException`: Data import failed
- `FileProcessingException`: File processing failed

---

## Data Flow

### 1. Tax Return Creation Flow

```
User selects "New Return"
    ↓
MainWindow.new_return()
    ↓
TaxYearService.create_return(year)
    ↓
TaxData instance created
    ↓
UI pages loaded with empty data
    ↓
User fills in data through interview
    ↓
ValidationService validates each field
    ↓
Data stored in TaxData model
    ↓
User clicks "Save"
    ↓
EncryptionService.encrypt(TaxData)
    ↓
AuditTrailService.log_change("save")
    ↓
File saved to disk with encryption
```

### 2. Tax Calculation Flow

```
User clicks "Calculate Tax"
    ↓
TaxCalculationService.calculate_complete_return(tax_data)
    ↓
[Income Aggregation]
    - Sum W-2 wages
    - Sum interest income
    - Sum dividend income
    - Sum business income
    ↓
[Deduction Selection]
    - Standard deduction: $14,600 (single 2024)
    - User itemized deductions: $18,000
    - Use larger: $18,000
    ↓
[Tax Calculation]
    - Taxable income: $100,000 - $18,000 = $82,000
    - Tax brackets lookup: $82,000 → $12,000 tax
    - Self-employment tax (if applicable): $2,000
    - Total tax: $14,000
    ↓
[Apply Credits]
    - Child Tax Credit: -$4,000
    - Total: $10,000
    ↓
[Withholding Comparison]
    - Federal withholding to date: $9,000
    - Estimated tax payments: $1,500
    - Total payments: $10,500
    - Tax owed: $10,000
    - Refund: $500
    ↓
TaxResult returned to UI
    ↓
UI displays results
```

### 3. E-Filing Flow

```
User clicks "File Electronically"
    ↓
EFilingService.prepare_return(tax_data)
    ↓
[XML Generation]
    - Form 1040 fields extracted
    - Schedules generated
    - Supporting forms included
    - IRS XMLS format applied
    ↓
[Validation]
    - IRSMefValidator.validate(xml)
    - Checks required fields
    - Validates calculations
    - Checks format compliance
    ↓
[Encryption]
    - EncryptionService.encrypt(xml)
    - Sign with PTIN certificate
    ↓
[Submission]
    - IRS e-Services endpoint
    - Confirmation received
    - Filing ID returned
    ↓
[Audit Trail]
    - AuditTrailService.log_filing(filing_id)
    - Confirmation stored
    ↓
UI confirms successful filing
```

### 4. Multi-Year Comparison Flow

```
User selects "Compare Years"
    ↓
TaxYearService.get_years()
    ↓
Loop through [2023, 2024, 2025]
    ↓
For each year:
    - Load TaxData for year
    - TaxCalculationService.calculate(tax_data)
    - Store results
    ↓
TaxAnalyticsService.compare_years(results)
    ↓
[Analysis Generation]
    - Effective tax rates by year
    - Income trend analysis
    - Deduction analysis
    - Tax savings opportunity identification
    ↓
TaxAnalyticsService.generate_report()
    ↓
Report displayed in UI
```

---

## Technology Stack

### Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Language** | Python | 3.13 | Primary development language |
| **UI Framework** | CustomTkinter | Latest | Modern desktop GUI |
| **Web Framework** | Flask | Latest | Web interface (optional) |
| **Encryption** | cryptography (Fernet) | Latest | Data encryption |
| **Database** | JSON Files | - | Data persistence |
| **Testing** | pytest | Latest | Unit/integration testing |
| **Type Hints** | typing | Built-in | Static type checking |

### Libraries & Dependencies

**Core Dependencies**:
- `customtkinter` - Modern UI framework
- `cryptography` - Encryption/decryption
- `requests` - HTTP requests (external APIs)
- `flask` - Web interface
- `pillow` - Image processing (receipt scanning)
- `pytesseract` - OCR for receipts

**Development Dependencies**:
- `pytest` - Unit testing
- `pytest-cov` - Code coverage
- `black` - Code formatting
- `pylint` - Linting
- `mypy` - Type checking

### File Storage

- **Format**: JSON (encrypted)
- **Location**: `~/.freedomustaxreturn/` or user-specified
- **Structure**: Multi-year support (2024-2026)
- **Encryption**: AES-256 via Fernet

### Logging

- **Framework**: Python logging
- **Handlers**:
  - File handler (debug log)
  - Console handler (warning+)
  - Audit trail handler (database/file)
- **Error Logging**: Centralized via ErrorLogger singleton

---

## Design Patterns

### 1. Singleton Pattern

**Used for**: Error Logger, Encryption Service key cache, Event Bus

```python
class ErrorLogger:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ErrorLogger()
        return cls._instance

# Usage
error_logger = get_error_logger()  # Always same instance
```

### 2. Factory Pattern

**Used for**: Service creation, UI widget creation

```python
class ServiceFactory:
    @staticmethod
    def create_tax_calculation_service(config):
        return TaxCalculationService(config)
```

### 3. Dependency Injection

**Used for**: All services receive dependencies through constructor

```python
class TaxCalculationService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.error_logger = get_error_logger()
```

### 4. Observer Pattern

**Used for**: Event bus system for UI updates

```python
event_bus.subscribe(EventType.DATA_CHANGED, on_data_changed)
event_bus.publish(EventType.DATA_CHANGED, data)
```

### 5. Strategy Pattern

**Used for**: Different deduction methods, tax calculation strategies

```python
class DeductionStrategy:
    def calculate(self, tax_data) -> float:
        pass

class StandardDeductionStrategy(DeductionStrategy):
    def calculate(self, tax_data) -> float:
        return get_standard_deduction(tax_data.filing_status)

class ItemizedDeductionStrategy(DeductionStrategy):
    def calculate(self, tax_data) -> float:
        return sum_itemized_deductions(tax_data)
```

### 6. Repository Pattern

**Used for**: Data persistence

```python
class TaxDataRepository:
    def save(self, tax_data: TaxData, file_path: str):
        encrypted_json = encryption_service.encrypt(asdict(tax_data))
        write_to_file(encrypted_json, file_path)
    
    def load(self, file_path: str) -> TaxData:
        encrypted_json = read_from_file(file_path)
        decrypted_json = encryption_service.decrypt(encrypted_json)
        return TaxData(**json.loads(decrypted_json))
```

---

## Security Architecture

### Data Protection Layers

```
┌─────────────────────────────────┐
│   User Input (Plain Text)       │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│  In-Memory (Encrypted Keys)     │
│  (Never plain in memory)        │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│  Encryption Key (Master Key)    │
│  (Encrypted with password)      │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│  Data Encryption (Fernet AES)   │
│  (At rest in files)             │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│  File System Storage            │
│  (OS-level file permissions)    │
└─────────────────────────────────┘
```

### Authentication & Authorization

**Authentication**:
- Master password (bcrypt hashing)
- PTIN/ERO credentials (encrypted storage)
- Session tokens (time-limited)

**Authorization**:
- Role-based access control (RBAC)
- Roles: Owner, Editor, Viewer
- Permissions: Read, Write, Delete, Share

### Sensitive Data Handling

**Data Redaction in Logs**:
- Passwords → `[REDACTED]`
- Social Security Numbers → `[REDACTED]`
- Credit card numbers → `[REDACTED]`
- Authentication tokens → `[REDACTED]`

**In-Transit Protection**:
- HTTPS for external API calls
- TLS 1.2+ required
- Certificate validation

**At-Rest Protection**:
- AES-256 encryption (Fernet)
- Master key derived from password
- Per-year data encryption

---

## Error Handling Architecture

### Exception Hierarchy

```
TaxReturnException (Base)
├─ AuthenticationException (4 subtypes)
├─ EncryptionException (3 subtypes)
├─ ValidationException (3 subtypes)
├─ DataProcessingException (4 subtypes)
├─ ConfigurationException (3 subtypes)
└─ ServiceException (3 subtypes)
   Total: 20+ specific exception types
```

### Error Logging Flow

```
Exception occurs in Service
    ↓
Caught by try-except block
    ↓
error_logger.log_exception(
    exception=e,
    context="service.method",
    severity="error",
    extra_details={...}
)
    ↓
Log Entry Created:
    - Timestamp
    - Exception type
    - Message
    - Stack trace
    - Context (service, method)
    - Severity level
    - Extra details
    - Sensitive data redacted
    ↓
Output to File (debug.log)
Output to Console (if WARNING+)
    ↓
Error added to History (100-entry rolling log)
    ↓
Exception re-raised for UI handling
```

### Service-Level Error Handling

All services follow this pattern:

```python
try:
    # Validate input
    # Process
    # Return result
except SpecificException as e:
    error_logger.log_exception(e, context="...")
    raise
except Exception as e:
    error_logger.log_exception(e, context="...")
    raise ServiceExecutionException(...) from e
```

---

## Deployment Architecture

### Development Environment

```
Developer Machine
├─ Python 3.13 venv
├─ CustomTkinter GUI (local)
├─ SQLite/JSON files (local)
└─ Git repository (local)
```

### Production Environment

```
User Machine
├─ Python 3.13 runtime
├─ CustomTkinter GUI (desktop application)
├─ Encrypted file storage
│  └─ ~/.freedomustaxreturn/
│     ├─ returns/
│     ├─ backups/
│     ├─ logs/
│     └─ config/
├─ Optional: Web interface (Flask)
│  └─ localhost:5000
└─ Optional: Cloud backup
   └─ AWS S3 / Google Drive / OneDrive
```

### Key Deployment Considerations

1. **Data Sovereignty**: All data stays on user's machine unless explicitly backed up to cloud
2. **No Cloud Dependency**: Application works 100% offline except for external integrations
3. **Easy Installation**: Single installer or pip package
4. **Auto-Updates**: Optional automatic update mechanism
5. **Backward Compatibility**: Support for previous year's data formats

### Scalability Considerations

Current architecture supports:
- Single user per installation
- Up to 7 years of multi-year returns
- JSON file storage (suitable for <100MB data)
- Future: Optional SQLite backend for larger datasets

---

## Summary

The Freedom US Tax Return application uses a **layered, service-oriented architecture** designed for:

- **Maintainability**: Clear separation of concerns, comprehensive documentation
- **Extensibility**: Easy to add new services and forms
- **Security**: Encryption-first design, comprehensive audit logging
- **Reliability**: Comprehensive error handling with centralized logging
- **Usability**: Modern UI with accessible design

**Key Architectural Strengths**:
1. ✅ 24 specialized services with clear responsibilities
2. ✅ Comprehensive exception hierarchy (20+ types)
3. ✅ Centralized error logging with history
4. ✅ Service-oriented with dependency injection
5. ✅ Multi-year tax return support
6. ✅ Extensive external integrations (banks, IRS, QuickBooks, etc.)
7. ✅ Encryption-first security approach
8. ✅ Audit trail for all changes

**Next Improvements**:
- Additional integration services (additional state tax agencies)
- Advanced tax planning AI
- Collaborative features enhancement
- Performance optimization for large returns
