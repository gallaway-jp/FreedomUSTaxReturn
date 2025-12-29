import pytest
import asyncio
from pathlib import Path
from utils.async_pdf import AsyncPDFGenerator, PDFGenerationTask, generate_pdf_async_wrapper, generate_multiple_pdfs_wrapper

class DummyPDFFormFiller:
    def export_form_1040(self, tax_data, output_path):
        # Simulate PDF export
        with open(output_path, 'w') as f:
            f.write('PDF content')

@pytest.fixture(autouse=True)
def patch_pdf_form_filler(monkeypatch):
    monkeypatch.setattr('utils.async_pdf.PDFFormFiller', DummyPDFFormFiller)

@pytest.mark.asyncio
async def test_generate_pdf_async_success(tmp_path):
    generator = AsyncPDFGenerator()
    task = PDFGenerationTask(
        form_name="Form 1040",
        tax_data={"name": "John Doe"},
        output_path=tmp_path / "Form_1040.pdf"
    )
    result = await generator.generate_pdf_async(task)
    assert result.success
    assert result.output_path.exists()
    generator.shutdown()

@pytest.mark.asyncio
async def test_generate_pdf_async_unknown_form(tmp_path):
    generator = AsyncPDFGenerator()
    task = PDFGenerationTask(
        form_name="Unknown Form",
        tax_data={},
        output_path=tmp_path / "Unknown.pdf"
    )
    result = await generator.generate_pdf_async(task)
    assert not result.success
    assert "Unknown form" in result.error
    generator.shutdown()

@pytest.mark.asyncio
async def test_generate_multiple_pdfs(tmp_path):
    generator = AsyncPDFGenerator()
    tasks = [
        PDFGenerationTask(
            form_name="Form 1040",
            tax_data={"name": f"User {i}"},
            output_path=tmp_path / f"Form_1040_{i}.pdf"
        ) for i in range(3)
    ]
    results = await generator.generate_multiple_pdfs(tasks)
    assert all(r.success for r in results)
    generator.shutdown()

def test_generate_pdf_async_wrapper(tmp_path):
    result = generate_pdf_async_wrapper(
        form_name="Form 1040",
        tax_data={"name": "Jane"},
        output_path=tmp_path / "Form_1040.pdf"
    )
    assert result.success
    assert result.output_path.exists()

def test_generate_multiple_pdfs_wrapper(tmp_path):
    tasks = [
        PDFGenerationTask(
            form_name="Form 1040",
            tax_data={"name": f"User {i}"},
            output_path=tmp_path / f"Form_1040_{i}.pdf"
        ) for i in range(2)
    ]
    results = generate_multiple_pdfs_wrapper(tasks)
    assert all(r.success for r in results)

def test_shutdown_idempotent():
    generator = AsyncPDFGenerator()
    generator.shutdown()
    generator.shutdown()  # Should not raise
