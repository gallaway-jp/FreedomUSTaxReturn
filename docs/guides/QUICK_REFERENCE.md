# Quick Reference: Using New Features

This guide provides quick code snippets for using the new architectural features.

## Event Bus

### Subscribe to Events
```python
from utils.event_bus import EventBus, Event, EventType

def on_data_changed(event: Event):
    print(f"Data changed: {event.data['path']} = {event.data['new_value']}")

event_bus = EventBus.get_instance()
event_bus.subscribe(EventType.TAX_DATA_CHANGED, on_data_changed)
```

### Publish Events
```python
from utils.event_bus import EventBus, Event, EventType

event_bus = EventBus.get_instance()
event_bus.publish(Event(
    type=EventType.CALCULATION_COMPLETED,
    source='TaxCalculator',
    data={'total_tax': 5432.10, 'refund': 1234.56}
))
```

### Unsubscribe
```python
event_bus.unsubscribe(EventType.TAX_DATA_CHANGED, on_data_changed)
```

### Get Event History
```python
history = event_bus.get_history()
for event in history:
    print(f"{event.timestamp}: {event.type.value} from {event.source}")
```

---

## Command Pattern (Undo/Redo)

### Initialize Command History
```python
from utils.commands import CommandHistory

history = CommandHistory(max_history=100)
```

### Execute Commands
```python
from utils.commands import SetValueCommand, AddW2Command

# Set a value
command = SetValueCommand(tax_data, "personal_info.first_name", "John")
if history.execute_command(command):
    print("Command executed successfully")

# Add W2
w2_data = {
    'employer_name': 'Acme Corp',
    'wages': 50000,
    'withholding': 5000
}
command = AddW2Command(tax_data, w2_data)
history.execute_command(command)
```

### Undo/Redo
```python
# Check if undo is available
if history.can_undo():
    description = history.get_undo_description()
    print(f"Can undo: {description}")
    history.undo()

# Check if redo is available
if history.can_redo():
    description = history.get_redo_description()
    print(f"Can redo: {description}")
    history.redo()
```

### GUI Integration
```python
from PyQt6.QtWidgets import QAction, QMenu

# Create Edit menu
edit_menu = QMenu("Edit", self)

# Undo action
undo_action = QAction("Undo", self)
undo_action.setShortcut("Ctrl+Z")
undo_action.triggered.connect(self.undo)
undo_action.setEnabled(history.can_undo())
edit_menu.addAction(undo_action)

# Redo action
redo_action = QAction("Redo", self)
redo_action.setShortcut("Ctrl+Y")
redo_action.triggered.connect(self.redo)
redo_action.setEnabled(history.can_redo())
edit_menu.addAction(redo_action)

def undo(self):
    if description := history.undo():
        self.statusBar().showMessage(f"Undone: {description}")
        self.update_undo_redo_actions()

def redo(self):
    if description := history.redo():
        self.statusBar().showMessage(f"Redone: {description}")
        self.update_undo_redo_actions()
```

---

## Plugin System

### Load Plugins
```python
from utils.plugins import get_plugin_registry, PluginLoader
from pathlib import Path

# Get global registry
registry = get_plugin_registry()

# Load all plugins from directory
loader = PluginLoader(registry)
loader.load_from_directory(Path("utils/plugins"))
```

### Use Plugins
```python
# Get all applicable plugins
applicable_plugins = registry.get_applicable_plugins(tax_data)

for plugin in applicable_plugins:
    metadata = plugin.get_metadata()
    print(f"Processing {metadata.schedule_name}")
    
    # Validate
    is_valid, error = plugin.validate_data(tax_data)
    if not is_valid:
        print(f"Validation error: {error}")
        continue
    
    # Calculate
    calculated_data = plugin.calculate(tax_data)
    
    # Map to PDF fields
    pdf_fields = plugin.map_to_pdf_fields(tax_data, calculated_data)
    
    # Export PDF
    # ... use pdf_fields to fill PDF form ...
```

### Create a Custom Plugin
```python
from utils.plugins import ISchedulePlugin, PluginMetadata
from typing import Dict, Any, Optional

class MySchedulePlugin(ISchedulePlugin):
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="My Schedule Plugin",
            version="1.0.0",
            description="Custom schedule for special cases",
            schedule_name="Schedule X",
            irs_form="f1040sx.pdf",
            author="Your Name"
        )
    
    def validate_data(self, tax_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        # Check if data is valid
        if not tax_data.get('my_schedule_data'):
            return False, "Missing schedule data"
        return True, None
    
    def calculate(self, tax_data: Dict[str, Any]) -> Dict[str, Any]:
        # Perform calculations
        data = tax_data['my_schedule_data']
        result = data['amount'] * 0.15
        return {'calculated_amount': result}
    
    def map_to_pdf_fields(self, tax_data: Dict[str, Any], 
                          calculated_data: Dict[str, Any]) -> Dict[str, Any]:
        # Map to PDF fields
        return {
            'field_1': tax_data['my_schedule_data']['amount'],
            'field_2': calculated_data['calculated_amount']
        }
    
    def is_applicable(self, tax_data: Dict[str, Any]) -> bool:
        # Determine if this schedule applies
        return bool(tax_data.get('my_schedule_data'))
```

Save as `utils/plugins/my_schedule_plugin.py` and it will be auto-loaded.

---

## Async PDF Generation

### Generate Single PDF (Async)
```python
from utils.async_pdf import AsyncPDFGenerator, PDFGenerationTask
from pathlib import Path
import asyncio

async def generate_pdf():
    generator = AsyncPDFGenerator(max_workers=4)
    
    task = PDFGenerationTask(
        form_name="Form 1040",
        tax_data=my_tax_data,
        output_path=Path("output/form_1040.pdf")
    )
    
    def progress_callback(task_id: str, percent: float):
        print(f"Progress: {percent:.1f}%")
    
    result = await generator.generate_pdf_async(task, progress_callback)
    
    if result.success:
        print(f"PDF generated: {result.output_path}")
        print(f"Duration: {result.duration:.2f}s")
    else:
        print(f"Error: {result.error}")
    
    generator.shutdown()

# Run async function
asyncio.run(generate_pdf())
```

### Generate Multiple PDFs Concurrently
```python
async def generate_multiple():
    generator = AsyncPDFGenerator(max_workers=4)
    
    tasks = [
        PDFGenerationTask("Form 1040", tax_data, Path("output/1040.pdf")),
        PDFGenerationTask("Schedule C", tax_data, Path("output/schedule_c.pdf")),
        PDFGenerationTask("Schedule A", tax_data, Path("output/schedule_a.pdf")),
    ]
    
    results = await generator.generate_multiple_pdfs(tasks)
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    print(f"Generated {len(successful)} PDFs successfully")
    for result in failed:
        print(f"Failed: {result.form_name} - {result.error}")
    
    generator.shutdown()

asyncio.run(generate_multiple())
```

### Synchronous Wrapper (for non-async code)
```python
from utils.async_pdf import generate_pdf_async_wrapper, PDFGenerationTask
from pathlib import Path

# Use in regular synchronous code
task = PDFGenerationTask(
    form_name="Form 1040",
    tax_data=my_tax_data,
    output_path=Path("output/form_1040.pdf")
)

result = generate_pdf_async_wrapper(
    task.form_name,
    task.tax_data,
    task.output_path,
    progress_callback=lambda tid, pct: print(f"{pct:.0f}%")
)

if result.success:
    print(f"PDF saved to {result.output_path}")
```

### GUI Integration with Progress Bar
```python
from PyQt6.QtWidgets import QProgressDialog
from PyQt6.QtCore import QThread, pyqtSignal
import asyncio

class PDFGeneratorThread(QThread):
    progress = pyqtSignal(str, float)
    finished = pyqtSignal(list)
    
    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks
    
    def run(self):
        generator = AsyncPDFGenerator()
        
        def progress_callback(task_id: str, percent: float):
            self.progress.emit(task_id, percent)
        
        results = asyncio.run(
            generator.generate_multiple_pdfs(self.tasks, progress_callback)
        )
        
        generator.shutdown()
        self.finished.emit(results)

# In your GUI code
def export_pdfs(self):
    tasks = [...]  # Your PDF generation tasks
    
    # Create progress dialog
    progress = QProgressDialog("Generating PDFs...", "Cancel", 0, 100, self)
    progress.setWindowModality(Qt.WindowModal)
    
    # Create and start thread
    thread = PDFGeneratorThread(tasks)
    thread.progress.connect(lambda tid, pct: progress.setValue(int(pct)))
    thread.finished.connect(lambda results: self.on_pdfs_generated(results))
    thread.start()
```

---

## Encryption Service

### Direct Use
```python
from services.encryption_service import EncryptionService
from pathlib import Path

# Initialize service
encryption = EncryptionService(Path("config/encryption.key"))

# Encrypt string
plaintext = "sensitive data"
encrypted = encryption.encrypt(plaintext)

# Decrypt
decrypted = encryption.decrypt(encrypted)
assert decrypted == plaintext

# Encrypt dictionary
data = {'ssn': '123-45-6789', 'income': 50000}
encrypted_dict = encryption.encrypt_dict(data)
decrypted_dict = encryption.decrypt_dict(encrypted_dict)
assert decrypted_dict == data
```

### Use in TaxData
```python
# TaxData automatically uses EncryptionService
tax_data = TaxData()

# Save (automatically encrypted)
tax_data.save_to_file(Path("data/return.enc"))

# Load (automatically decrypted)
loaded_data = TaxData.load_from_file(Path("data/return.enc"))
```

---

## Complete Example: Tax Return Workflow

```python
from models.tax_data import TaxData
from utils.commands import CommandHistory, SetValueCommand, AddW2Command
from utils.event_bus import EventBus, Event, EventType
from utils.plugins import get_plugin_registry, PluginLoader
from utils.async_pdf import AsyncPDFGenerator, PDFGenerationTask
from pathlib import Path
import asyncio

async def main():
    # Initialize
    tax_data = TaxData()
    command_history = CommandHistory()
    event_bus = EventBus.get_instance()
    
    # Subscribe to events
    def on_data_changed(event: Event):
        print(f"Data changed: {event.data['path']}")
    
    event_bus.subscribe(EventType.TAX_DATA_CHANGED, on_data_changed)
    
    # Enter data with undo support
    commands = [
        SetValueCommand(tax_data, "personal_info.first_name", "John"),
        SetValueCommand(tax_data, "personal_info.last_name", "Doe"),
        SetValueCommand(tax_data, "personal_info.ssn", "123-45-6789"),
        AddW2Command(tax_data, {
            'employer_name': 'Acme Corp',
            'wages': 50000,
            'withholding': 5000
        })
    ]
    
    for cmd in commands:
        command_history.execute_command(cmd)
    
    # Oops, made a mistake - undo last command
    if command_history.can_undo():
        command_history.undo()
        print("Undone last command")
    
    # Load plugins
    registry = get_plugin_registry()
    loader = PluginLoader(registry)
    loader.load_from_directory(Path("utils/plugins"))
    
    # Process applicable schedules
    plugins = registry.get_applicable_plugins(tax_data.to_dict())
    for plugin in plugins:
        metadata = plugin.get_metadata()
        print(f"Processing {metadata.schedule_name}")
        
        calculated = plugin.calculate(tax_data.to_dict())
        pdf_fields = plugin.map_to_pdf_fields(tax_data.to_dict(), calculated)
    
    # Generate PDFs asynchronously
    generator = AsyncPDFGenerator(max_workers=4)
    
    tasks = [
        PDFGenerationTask("Form 1040", tax_data.to_dict(), 
                         Path("output/form_1040.pdf"))
    ]
    
    results = await generator.generate_multiple_pdfs(tasks,
        progress_callback=lambda tid, pct: print(f"{tid}: {pct:.0f}%")
    )
    
    for result in results:
        if result.success:
            print(f"✓ {result.form_name} generated in {result.duration:.2f}s")
        else:
            print(f"✗ {result.form_name} failed: {result.error}")
    
    generator.shutdown()
    
    # Save tax data (automatically encrypted)
    tax_data.save_to_file(Path("data/tax_return.enc"))
    print("Tax return saved securely")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Tips and Best Practices

### Event Bus
- ✅ Always unsubscribe handlers when no longer needed
- ✅ Keep event handlers lightweight (avoid heavy processing)
- ✅ Use event history for debugging
- ❌ Don't publish events in event handlers (avoid loops)

### Command Pattern
- ✅ Set reasonable max_history (default 100 is good)
- ✅ Clear history when starting new tax return
- ✅ Show command descriptions in UI
- ❌ Don't execute commands directly on data (use CommandHistory)

### Plugins
- ✅ Validate plugin data thoroughly
- ✅ Handle calculation errors gracefully
- ✅ Version your plugins
- ❌ Don't modify core code for new schedules

### Async PDF
- ✅ Use progress callbacks for user feedback
- ✅ Set max_workers based on CPU cores
- ✅ Handle errors for each PDF individually
- ❌ Don't forget to call shutdown()

### Encryption
- ✅ Use EncryptionService for all encryption needs
- ✅ Protect encryption key file
- ✅ Implement key rotation policy
- ❌ Don't store plaintext sensitive data
