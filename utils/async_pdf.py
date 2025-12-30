"""
Async PDF Generation

This module provides asynchronous PDF generation capabilities for better
performance when generating multiple forms or large tax returns.
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

from utils.pdf.form_filler import PDFFormFiller
from utils.event_bus import EventBus, Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class PDFGenerationTask:
    """Represents a single PDF generation task"""
    form_name: str
    tax_data: Dict[str, Any]
    output_path: Path
    task_id: str = None
    
    def __post_init__(self):
        if self.task_id is None:
            self.task_id = f"{self.form_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


@dataclass
class PDFGenerationResult:
    """Result of a PDF generation task"""
    task_id: str
    form_name: str
    success: bool
    output_path: Optional[Path] = None
    error: Optional[str] = None
    duration: float = 0.0


class AsyncPDFGenerator:
    """
    Async PDF generator that can generate multiple PDFs concurrently
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize the async PDF generator
        
        Args:
            max_workers: Maximum number of concurrent PDF generation tasks
        """
        self.max_workers = max_workers
        self.event_bus = EventBus.get_instance()
        self._executor = None
    
    def _get_executor(self) -> ThreadPoolExecutor:
        """Get or create thread pool executor"""
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self._executor
    
    async def generate_pdf_async(
        self,
        task: PDFGenerationTask,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> PDFGenerationResult:
        """
        Generate a single PDF asynchronously
        
        Args:
            task: PDF generation task
            progress_callback: Optional callback function(task_id, progress_percent)
        
        Returns:
            PDFGenerationResult with success status and output path or error
        """
        start_time = datetime.now()
        
        # Publish start event
        self.event_bus.publish(Event(
            type=EventType.PDF_EXPORT_STARTED,
            source='AsyncPDFGenerator',
            data={'task_id': task.task_id, 'form_name': task.form_name}
        ))
        
        if progress_callback:
            progress_callback(task.task_id, 0.0)
        
        try:
            # Run PDF generation in thread pool
            loop = asyncio.get_event_loop()
            executor = self._get_executor()
            
            # Update progress
            if progress_callback:
                progress_callback(task.task_id, 25.0)
            
            # Execute PDF generation in thread pool
            await loop.run_in_executor(
                executor,
                self._generate_pdf_sync,
                task
            )
            
            if progress_callback:
                progress_callback(task.task_id, 100.0)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Publish completion event
            self.event_bus.publish(Event(
                type=EventType.PDF_EXPORT_COMPLETED,
                source='AsyncPDFGenerator',
                data={
                    'task_id': task.task_id,
                    'form_name': task.form_name,
                    'output_path': str(task.output_path),
                    'duration': duration
                }
            ))
            
            return PDFGenerationResult(
                task_id=task.task_id,
                form_name=task.form_name,
                success=True,
                output_path=task.output_path,
                duration=duration
            )
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            logger.error(f"PDF generation failed for {task.form_name}: {error_msg}")
            
            # Publish error event
            self.event_bus.publish(Event(
                type=EventType.PDF_EXPORT_FAILED,
                source='AsyncPDFGenerator',
                data={
                    'task_id': task.task_id,
                    'form_name': task.form_name,
                    'error': error_msg
                }
            ))
            
            return PDFGenerationResult(
                task_id=task.task_id,
                form_name=task.form_name,
                success=False,
                error=error_msg,
                duration=duration
            )
    
    def _generate_pdf_sync(self, task: PDFGenerationTask):
        """
        Synchronous PDF generation (called in thread pool)
        """
        filler = PDFFormFiller()
        
        if task.form_name == "Form 1040":
            filler.export_form_1040(task.tax_data, task.output_path)
        elif task.form_name == "Schedule C":
            self._generate_schedule_c(task)
        elif task.form_name == "Form 8949":
            self._generate_form_8949(task)
        elif task.form_name == "Schedule A":
            self._generate_schedule_a(task)
        elif task.form_name == "Schedule E":
            self._generate_schedule_e(task)
        else:
            raise ValueError(f"Unknown form: {task.form_name}")
        
        logger.info(f"Generated PDF: {task.output_path}")
    
    def _generate_schedule_c(self, task: PDFGenerationTask) -> None:
        """
        Generate Schedule C PDF using the plugin system
        """
        from utils.plugins import get_plugin_registry
        registry = get_plugin_registry()
        plugin = registry.get_plugin("Schedule C")
        
        if not plugin:
            raise ValueError("Schedule C plugin not found")
        
        # Get field mappings from plugin
        calculated_data = plugin.calculate_schedule_data(task.tax_data)
        field_mappings = plugin.map_to_pdf_fields(task.tax_data, calculated_data)
        
        # Generate PDF
        filler = PDFFormFiller()
        filler.fill_form("Form 1040 (Schedule C)", field_mappings, str(task.output_path))
    
    def _generate_form_8949(self, task: PDFGenerationTask) -> None:
        """
        Generate Form 8949 PDF for capital gains/losses
        """
        from utils.pdf.form_mappers import Form8949Mapper
        
        # Get field mappings from Form8949Mapper
        field_mappings = Form8949Mapper.get_all_fields(task.tax_data)
        
        # Generate PDF
        filler = PDFFormFiller()
        filler.fill_form("f8949.pdf", field_mappings, str(task.output_path))
    
    def _generate_schedule_a(self, task: PDFGenerationTask) -> None:
        """
        Generate Schedule A PDF for itemized deductions
        """
        # Placeholder for Schedule A generation
        filler = PDFFormFiller()
        fields = {}  # Would need proper field mappings
        filler.fill_form("f1040sa.pdf", fields, str(task.output_path))
    
    def _generate_schedule_e(self, task: PDFGenerationTask) -> None:
        """
        Generate Schedule E PDF for rental income
        """
        # Placeholder for Schedule E generation
        filler = PDFFormFiller()
        fields = {}  # Would need proper field mappings
        filler.fill_form("f1040se.pdf", fields, str(task.output_path))
    
    async def generate_multiple_pdfs(
        self,
        tasks: List[PDFGenerationTask],
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> List[PDFGenerationResult]:
        """
        Generate multiple PDFs concurrently
        
        Args:
            tasks: List of PDF generation tasks
            progress_callback: Optional callback for progress updates
        
        Returns:
            List of PDFGenerationResult objects
        """
        logger.info(f"Starting generation of {len(tasks)} PDFs")
        
        # Create tasks
        coroutines = [
            self.generate_pdf_async(task, progress_callback)
            for task in tasks
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Convert any exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(PDFGenerationResult(
                    task_id=tasks[i].task_id,
                    form_name=tasks[i].form_name,
                    success=False,
                    error=str(result)
                ))
            else:
                final_results.append(result)
        
        # Log summary
        successful = sum(1 for r in final_results if r.success)
        failed = len(final_results) - successful
        logger.info(f"PDF generation complete: {successful} successful, {failed} failed")
        
        return final_results
    
    async def generate_complete_return(
        self,
        tax_data: Dict[str, Any],
        output_dir: Path,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> List[PDFGenerationResult]:
        """
        Generate all applicable forms for a complete tax return
        
        Args:
            tax_data: Tax data dictionary
            output_dir: Directory to save PDFs
            progress_callback: Optional progress callback
        
        Returns:
            List of generation results
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        tasks = []
        
        # Always generate Form 1040
        tasks.append(PDFGenerationTask(
            form_name="Form 1040",
            tax_data=tax_data,
            output_path=output_dir / "Form_1040.pdf"
        ))
        
        # TODO: Add other forms based on tax data
        # Example: Schedule C if business income exists
        # if tax_data.get('schedules', {}).get('schedule_c'):
        #     tasks.append(PDFGenerationTask(
        #         form_name="Schedule C",
        #         tax_data=tax_data,
        #         output_path=output_dir / "Schedule_C.pdf"
        #     ))
        
        return await self.generate_multiple_pdfs(tasks, progress_callback)
    
    def shutdown(self):
        """Shutdown the thread pool executor"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
            logger.info("AsyncPDFGenerator executor shutdown")


# Convenience function for synchronous code
def generate_pdf_async_wrapper(
    form_name: str,
    tax_data: Dict[str, Any],
    output_path: Path,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> PDFGenerationResult:
    """
    Wrapper function to run async PDF generation from synchronous code
    
    Args:
        form_name: Name of the form to generate
        tax_data: Tax data dictionary
        output_path: Path to save the PDF
        progress_callback: Optional progress callback
    
    Returns:
        PDFGenerationResult
    """
    generator = AsyncPDFGenerator()
    task = PDFGenerationTask(
        form_name=form_name,
        tax_data=tax_data,
        output_path=output_path
    )
    
    try:
        # Run async function in new event loop
        result = asyncio.run(generator.generate_pdf_async(task, progress_callback))
        return result
    finally:
        generator.shutdown()


def generate_multiple_pdfs_wrapper(
    tasks: List[PDFGenerationTask],
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> List[PDFGenerationResult]:
    """
    Wrapper to generate multiple PDFs from synchronous code
    
    Args:
        tasks: List of PDF generation tasks
        progress_callback: Optional progress callback
    
    Returns:
        List of PDFGenerationResult objects
    """
    generator = AsyncPDFGenerator()
    try:
        results = asyncio.run(generator.generate_multiple_pdfs(tasks, progress_callback))
        return results
    finally:
        generator.shutdown()
