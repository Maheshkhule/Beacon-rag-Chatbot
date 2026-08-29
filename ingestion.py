import os
import tempfile
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from llama_index.core.schema import Document


# Check if Tesseract is available
try:
    pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False
    print("⚠️ Tesseract not found – scanned pages will be skipped.")


def extract_text_with_ocr(pdf_path: str, dpi: int = 300) -> str:
    """Extract text; if a page has no text, run OCR (if Tesseract is available)."""
    doc = fitz.open(pdf_path)
    full_text = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            full_text.append(text)
        elif TESSERACT_AVAILABLE:
            # Scanned page – run OCR
            images = convert_from_path(
                pdf_path,
                first_page=page_num + 1,
                last_page=page_num + 1,
                dpi=dpi
            )
            for img in images:
                ocr_text = pytesseract.image_to_string(img)
                full_text.append(ocr_text)
        else:
            full_text.append("[OCR not available – scanned page skipped]")
    doc.close()
    return "\n".join(full_text)


class PDFWithOCRReader:
    def load_data(self, file_path: Path, extra_info: Optional[dict] = None) -> List[Document]:
        text = extract_text_with_ocr(str(file_path))
        metadata = {
            "file_name": file_path.name,
            "file_path": str(file_path),
        }
        if extra_info:
            metadata.update(extra_info)
        return [Document(text=text, metadata=metadata)]


def ingest_pdfs(pdf_folder: str) -> List[Document]:
    reader = PDFWithOCRReader()
    documents = []
    pdf_files = list(Path(pdf_folder).glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in '{pdf_folder}'.")
    print(f"📄 Found {len(pdf_files)} PDF files.")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"   [{i}/{len(pdf_files)}] Ingesting {pdf_file.name}...")
        docs = reader.load_data(pdf_file)
        documents.extend(docs)
        print(f"      → {len(docs)} document(s) extracted.")
    return documents