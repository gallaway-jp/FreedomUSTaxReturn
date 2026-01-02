# Tax Interview & Forms Selection - Visual Overview

## User Interface Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN APPLICATION WINDOW                      │
├─────────────────────────┬───────────────────────────────────────┤
│   SIDEBAR               │   CONTENT AREA                        │
│   ─────────────────     │   ─────────────────────────────────   │
│                         │                                       │
│  🚀 Start Tax          │  ┌─────────────────────────────────┐  │
│     Interview          │  │  WELCOME SCREEN                 │  │
│                         │  │  ─────────────────────────────  │  │
│  📋 Skip to Tax        │  │  Choose your path:              │  │
│     Forms              │  │                                 │  │
│                         │  │  • Start Interview (guided)    │  │
│  ──────────────────    │  │  • Skip to Forms (manual)      │  │
│  📄 TAX FORMS          │  │                                 │  │
│  (hidden initially)    │  │                                 │  │
│                         │  └─────────────────────────────────┘  │
└─────────────────────────┴───────────────────────────────────────┘

                              ↓
                              
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ↓                                           ↓
    
┌────────────────────────┐           ┌────────────────────────┐
│  TAX INTERVIEW PAGE    │           │  TAX FORMS PAGE        │
│  ─────────────────     │           │  ─────────────────     │
│                        │           │                        │
│  Progress: [████░░]    │           │  Search: [____________]│
│                        │           │                        │
│  Question: Are you     │           │  Categories:           │
│  married?              │           │  ☑ Core (1040)         │
│                        │           │  ☑ Deductions (Sch A)  │
│  ○ Yes  ○ No           │           │  ☐ Income (Sch B)      │
│                        │           │  ☐ Business (Sch C)    │
│  [← Back] [Next →]     │           │  ☐ Investments (Sch D) │
│  ⊗ Skip Interview      │           │                        │
│                        │           │  [Select All] [Clear]  │
│                        │           │  [Continue →]          │
└────────────────────────┘           └────────────────────────┘
        │                                           │
        │ (Continue answering questions)            │
        │ (Finish when all answered)                │
        │                                           │
        ↓                                           │
                                                    │
┌────────────────────────────────────────────────┐  │
│  RECOMMENDATIONS SCREEN                        │  │
│  ─────────────────────────────────────────     │  │
│                                                │  │
│  Interview Complete!                          │  │
│  Based on your answers, we recommend:         │  │
│                                                │  │
│  ✓ Form 1040 (Required)                       │  │
│  ✓ Schedule A (Itemized Deductions)           │  │
│  ✓ Schedule D (Capital Gains)                 │  │
│  ○ Schedule C (Business Income)               │  │
│                                                │  │
│  Estimated time: 2 hours 15 minutes           │  │
│                                                │  │
│  [← Back] [Continue to Forms →]              │  │
└────────────────────────────────────────────────┘  │
        │                                           │
        └─────────────────────┬─────────────────────┘
                              │
                              ↓
                              
┌────────────────────────────────────────────────┐
│  FORMS SELECTION PAGE (WITH RECOMMENDATIONS)  │
│  ─────────────────────────────────────────     │
│                                                │
│  Search: [____________]                       │
│  Selected: 3 forms                            │
│                                                │
│  Core:                                         │
│  ✓ 1040 (U.S. Individual Income Tax Return)   │
│                                                │
│  Deductions:                                   │
│  ✓ Schedule A (Itemized Deductions)           │
│                                                │
│  Investments:                                  │
│  ✓ Schedule D (Capital Gains and Losses)      │
│  ☐ Form 8949 (Sales of Securities)            │
│                                                │
│  [Select All] [Clear All]                     │
│  [Continue →]                                 │
└────────────────────────────────────────────────┘
                              │
                              ↓
                              
┌────────────────────────────────────────────────┐
│  FORM COMPLETION PAGES (INC.HOME, DEDUCTIONS) │
│  ─────────────────────────────────────────     │
│                                                │
│  Sidebar shows selected forms:                │
│  ✓ 1040                                        │
│  ✓ Schedule A                                  │
│  ✓ Schedule D                                  │
│                                                │
│  Click any form to complete it                │
│  Or click forms selection to modify            │
└────────────────────────────────────────────────┘
```

## Interview Page Details

### Question Types
```
1. YES/NO QUESTION
   Are you married?
   ○ Yes  ○ No

2. MULTIPLE CHOICE
   What is your filing status?
   ○ Single
   ○ Married Filing Jointly
   ○ Married Filing Separately
   ○ Head of Household
   ○ Qualifying Widow(er)

3. NUMERIC INPUT
   How many dependents do you have?
   [____]

4. TEXT INPUT
   What is your business name?
   [________________]

5. DATE INPUT
   What is your date of birth?
   [YYYY-MM-DD]
```

### Navigation Features
```
Interview Progress Bar
├─ Shows completion percentage
├─ Updates after each question
└─ Shows how many questions remain

Navigation Buttons
├─ ← Back (enabled after first question)
├─ Next → (moves to next question)
└─ ⊗ Skip Interview (available anytime)

Interview Flow
├─ Start: Question 1
├─ Progress: Questions 2-N with Back/Next
├─ End: Recommendations screen
└─ Continue: Go to Forms Selection
```

## Forms Selection Page Details

### Form Categories (Pre-defined)
```
CORE
├─ 1040 (Required - always selected)

DEDUCTIONS
├─ Schedule A (Itemized Deductions)

INCOME
├─ Schedule B (Interest & Dividends)
├─ Schedule C (Business Income)
├─ Schedule E (Rental Income)

INVESTMENTS
├─ Schedule D (Capital Gains)
├─ Form 8949 (Securities Sales)

CREDITS
├─ Schedule EIC (Earned Income Credit)
├─ Form 2441 (Child Care Credit)
├─ Form 3468 (Investment Credit)
├─ Form 5695 (Energy Credits)

FOREIGN
├─ Form 1116 (Foreign Tax Credit)

GIFTS
├─ Form 3520 (Gift Tax)

CRYPTO
├─ Form 8801 (Crypto & Digital Assets)

EMPLOYMENT
├─ Schedule H (Household Employment)
```

### Form Information Display
```
Form Item
├─ Checkbox (enabled/disabled based on requirements)
├─ Form Code (e.g., "1040", "Schedule A")
├─ Form Name (e.g., "U.S. Individual Income Tax Return")
├─ Description (brief explanation)
└─ Estimated Time (e.g., "~45 minutes")

Example:
┌─────────────────────────────────────────┐
│ ☑ Schedule A                            │
│   Itemized Deductions instead of       │
│   standard deduction (~30 minutes)      │
└─────────────────────────────────────────┘
```

### Search & Filter Features
```
Search Box
└─ Real-time filtering by:
   ├─ Form number (1040, Schedule A, etc.)
   ├─ Form name (Income Tax Return, etc.)
   └─ Description keywords

Results: Organized by category
└─ Only matching forms shown

Action Buttons
├─ Select All (selects all non-required)
└─ Clear All (deselects all non-required)
```

## State Transitions

### Interview Path
```
START
  ↓
INTERVIEW PAGE 1
  ├─ ← Back (disabled)
  ├─ Next → (to Q2)
  └─ ⊗ Skip (to FORMS PAGE)
  ↓
INTERVIEW PAGE 2-N
  ├─ ← Back (to previous)
  ├─ Next → (to next or recommendations)
  └─ ⊗ Skip (to FORMS PAGE)
  ↓
RECOMMENDATIONS SCREEN
  ├─ ← Back (to previous question)
  ├─ Continue (to FORMS PAGE with recommendations)
  └─ ⊗ Skip (to FORMS PAGE)
  ↓
FORMS PAGE (with pre-selected recommendations)
  ├─ Add/remove forms
  ├─ Continue (to FORM COMPLETION)
  └─ Search/filter forms
  ↓
FORM COMPLETION PAGES
```

### Skip Path
```
START
  ↓
MAIN WINDOW
  ↓
📋 Skip to Tax Forms button
  ↓
FORMS PAGE (empty selection)
  ├─ Select forms
  ├─ Search/filter
  ├─ Select All / Clear All
  └─ Continue (to FORM COMPLETION)
  ↓
FORM COMPLETION PAGES
```

## Sidebar State Changes

### Initial State
```
🚀 Start Tax Interview       [Primary button]
📋 Skip to Tax Forms          [Secondary button]
──────────────────────────
📄 TAX FORMS
  (empty - hidden)
```

### After Interview/Forms Selection
```
🚀 Start Tax Interview       [Hidden]
📋 Skip to Tax Forms          [Hidden]
──────────────────────────
📄 TAX FORMS
  ✓ 1040
  ✓ Schedule A
  ✓ Schedule D
  [click to open form]
```

## Data Flow

```
User Input (Interview Answers)
  ↓
Interview Service
  ├─ Process answers
  ├─ Apply conditional logic
  └─ Generate recommendations
  ↓
Recommendations List
  ├─ Form 1040
  ├─ Schedule A
  └─ Schedule D
  ↓
Forms Selection Page
  ├─ Pre-select recommended forms
  ├─ Show all available forms
  └─ Allow user to modify
  ↓
Selected Forms List
  ├─ Form 1040
  ├─ Schedule A
  └─ Schedule D
  ↓
Update Sidebar
  ├─ Show selected forms
  └─ Hide interview buttons
  ↓
Form Completion Pages
  ├─ User fills out forms
  └─ Calculates totals/recommendations
```

## Key Improvements

1. **Non-Modal Navigation**: Users can navigate forward/backward without being locked in a modal dialog

2. **Skip Option**: Users who prefer manual form selection don't have to answer all interview questions

3. **Form Management**: Dedicated page for viewing, selecting, and modifying forms

4. **Search & Filter**: Users can quickly find specific forms by name or number

5. **Time Estimates**: Each form shows estimated completion time for planning

6. **Form Organization**: Forms grouped by category for easier navigation

7. **Recommendations Integration**: Interview results feed directly into form selection

8. **Flexibility**: Users can modify form selections anytime without restarting interview

9. **Accessibility**: Page-based design is more accessible than modal dialogs

10. **Consistency**: Aligns with existing page-based navigation architecture
