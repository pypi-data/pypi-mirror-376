"""
PDF Stamper Module

Provides functionality to stamp PDF files with sequential numbers or custom text.
"""

from dataclasses import dataclass
from enum import Enum
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader, PdfWriter
import io
import os


class Position(Enum):
    """Predefined positions for text placement on PDF pages."""

    TOP_RIGHT = (512, 788)
    TOP_LEFT = (50, 788)
    BOTTOM_RIGHT = (512, 50)
    BOTTOM_LEFT = (50, 50)
    CENTER = (300, 400)


@dataclass
class StamperConfig:
    """Configuration for PDF stamping operations."""

    # Font configuration
    font_name: str = "Times-Roman"
    font_size: int = 13
    text_color: tuple = (0, 0, 0)  # RGB color tuple (0-1 range)

    # Position configuration
    position: tuple = Position.TOP_RIGHT.value  # (x, y) coordinates

    # Numbering configuration
    prefix: str = "Copy "
    number_format: str = "{:03d}"


class PDFStamper:
    """A class for stamping PDF files with text overlays."""

    def __init__(self, config: StamperConfig = None):
        """
        Initialize PDFStamper with configuration options.

        Args:
            config (StamperConfig): Configuration object. Uses defaults if None.
        """
        self.config = config or StamperConfig()

    def stamp_pdf(self, input_pdf_path: str, output_pdf_path: str, text: str) -> None:
        """Stamp a PDF file with the specified text."""
        overlay_stream = self._create_overlay_stream(text)
        overlay = PdfReader(overlay_stream).pages[0]

        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()

        for page in reader.pages:
            page.merge_page(overlay)
            writer.add_page(page)

        # Compress content streams for smaller file size
        for page in writer.pages:
            page.compress_content_streams()

        with open(output_pdf_path, "wb") as f:
            writer.write(f)

        overlay_stream.close()

    def stamp_multiple_copies(
        self, input_pdf_path: str, output_dir: str, num_copies: int
    ) -> list:
        """Create multiple stamped copies of a PDF with sequential numbering."""
        os.makedirs(output_dir, exist_ok=True)

        output_files = []

        for i in range(1, num_copies + 1):
            stamp_text = f"{self.config.prefix}{self.config.number_format.format(i)}"
            output_filename = (
                f"{os.path.splitext(os.path.basename(input_pdf_path))[0]}_{i:03d}.pdf"
            )
            output_path = os.path.join(output_dir, output_filename)

            self.stamp_pdf(input_pdf_path, output_path, stamp_text)
            output_files.append(output_path)

        return output_files

    def _create_overlay_stream(self, text: str) -> io.BytesIO:
        """Create a PDF overlay with the specified text."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        # Set font and color
        c.setFont(self.config.font_name, self.config.font_size)
        c.setFillColorRGB(*self.config.text_color)
        c.drawString(self.config.position[0], self.config.position[1], text)

        c.save()
        buffer.seek(0)
        return buffer
