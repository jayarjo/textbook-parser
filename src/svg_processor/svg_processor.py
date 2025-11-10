"""
SVG Text Processor

Extracts text directly from SVG/SVGZ files without OCR.
Much faster and more accurate for vector-based pages.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import gzip
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from loguru import logger


@dataclass
class TextElement:
    """Represents a text element from SVG with position info."""
    text: str
    x: float
    y: float
    font_size: Optional[float] = None
    font_family: Optional[str] = None


class SVGTextProcessor:
    """
    Processes SVG/SVGZ files to extract text content.

    Handles both regular SVG and compressed SVGZ formats.
    Extracts text elements while preserving layout information.
    """

    def __init__(self):
        """Initialize the SVG processor."""
        self.namespaces = {
            'svg': 'http://www.w3.org/2000/svg',
            'xlink': 'http://www.w3.org/1999/xlink'
        }

    def process_file(self, svg_path: Path) -> Dict[str, Any]:
        """
        Extract text from an SVG or SVGZ file.

        Args:
            svg_path: Path to SVG or SVGZ file

        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Read and decompress if SVGZ
            if svg_path.suffix.lower() == '.svgz':
                logger.info(f"Processing compressed SVG: {svg_path}")
                with gzip.open(svg_path, 'rb') as f:
                    content = f.read()
            else:
                logger.info(f"Processing SVG: {svg_path}")
                with open(svg_path, 'rb') as f:
                    content = f.read()

            # Parse XML
            root = ET.fromstring(content)

            # Extract text elements
            text_elements = self._extract_text_elements(root)

            # Sort by position (top to bottom, left to right)
            text_elements.sort(key=lambda t: (t.y, t.x))

            # Combine into full text
            full_text = '\n'.join(elem.text for elem in text_elements if elem.text.strip())

            logger.info(f"Extracted {len(text_elements)} text elements ({len(full_text)} characters)")

            return {
                'success': True,
                'file': str(svg_path),
                'text': full_text,
                'text_elements': len(text_elements),
                'characters': len(full_text),
                'has_content': bool(full_text.strip())
            }

        except Exception as e:
            logger.error(f"Failed to process {svg_path}: {e}")
            return {
                'success': False,
                'file': str(svg_path),
                'error': str(e),
                'text': ''
            }

    def _extract_text_elements(self, root: ET.Element) -> List[TextElement]:
        """
        Extract all text elements from SVG root.

        Args:
            root: XML root element

        Returns:
            List of TextElement objects
        """
        text_elements = []

        # Find all text elements (with and without namespace)
        for text_elem in root.iter():
            tag_name = text_elem.tag.split('}')[-1] if '}' in text_elem.tag else text_elem.tag

            if tag_name in ('text', 'tspan'):
                text_content = self._get_text_content(text_elem)
                if text_content:
                    x, y = self._get_position(text_elem)
                    font_size = self._get_font_size(text_elem)
                    font_family = text_elem.get('font-family')

                    text_elements.append(TextElement(
                        text=text_content,
                        x=x,
                        y=y,
                        font_size=font_size,
                        font_family=font_family
                    ))

        return text_elements

    def _get_text_content(self, elem: ET.Element) -> str:
        """Get all text content from element and children."""
        text_parts = []

        # Get direct text
        if elem.text:
            text_parts.append(elem.text)

        # Get text from children
        for child in elem:
            child_text = self._get_text_content(child)
            if child_text:
                text_parts.append(child_text)
            if child.tail:
                text_parts.append(child.tail)

        return ''.join(text_parts).strip()

    def _get_position(self, elem: ET.Element) -> tuple[float, float]:
        """Extract x, y position from element."""
        try:
            x = float(elem.get('x', 0))
            y = float(elem.get('y', 0))

            # Check for transform attribute
            transform = elem.get('transform', '')
            if 'translate' in transform:
                # Simple translate parsing: translate(x,y) or translate(x y)
                import re
                match = re.search(r'translate\(([-\d.]+)[,\s]+([-\d.]+)\)', transform)
                if match:
                    x += float(match.group(1))
                    y += float(match.group(2))

            return x, y
        except (ValueError, AttributeError):
            return 0.0, 0.0

    def _get_font_size(self, elem: ET.Element) -> Optional[float]:
        """Extract font size from element."""
        font_size = elem.get('font-size')
        if font_size:
            try:
                # Remove 'px' or other units
                return float(font_size.rstrip('pxemptcm'))
            except ValueError:
                return None
        return None

    def process_batch(
        self,
        svg_dir: Path,
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Process all SVG/SVGZ files in a directory.

        Args:
            svg_dir: Directory containing SVG/SVGZ files
            output_path: Optional path to save combined text output

        Returns:
            Dictionary with batch processing results
        """
        svg_files = list(svg_dir.glob('*.svg')) + list(svg_dir.glob('*.svgz'))
        svg_files.sort()

        logger.info(f"Processing {len(svg_files)} SVG files from {svg_dir}")

        results = []
        all_text = []

        for svg_file in svg_files:
            result = self.process_file(svg_file)
            results.append(result)

            if result['success'] and result['text']:
                all_text.append(f"--- {svg_file.name} ---")
                all_text.append(result['text'])
                all_text.append('')  # Empty line between pages

        # Combine all text
        combined_text = '\n'.join(all_text)

        # Save if output path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(combined_text, encoding='utf-8')
            logger.info(f"Saved combined text to {output_path}")

        return {
            'success': True,
            'files_processed': len(svg_files),
            'files_succeeded': sum(1 for r in results if r['success']),
            'total_characters': len(combined_text),
            'output_path': str(output_path) if output_path else None,
            'results': results
        }
