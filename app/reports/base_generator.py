"""
Base PDF generator class with common functionality for all reports.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from typing import List, Optional
from datetime import datetime

from .types import Player
from .formatters import get_report_generation_date


class BasePDFGenerator:
    """Base class for PDF report generators"""
    
    def __init__(self, player: Player, primary_color: str = "#B22222", header_color: str = "#1F2937"):
        self.player = player
        self.primary_color = colors.HexColor(primary_color)
        self.header_color = colors.HexColor(header_color)
        self.light_grey = colors.HexColor("#F3F4F6")
        self.dark_grey = colors.HexColor("#6B7280")
        
        # Page setup
        self.page_width, self.page_height = A4
        self.margin = 36  # 0.5 inch
        self.content_width = self.page_width - (2 * self.margin)
        
        # Create styles
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=self.primary_color,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=16,
            alignment=TA_LEFT,
            textColor=self.header_color,
            fontName='Helvetica-Bold'
        ))
        
        # Table header style
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.white,
            fontName='Helvetica-Bold'
        ))
        
        # Table cell style
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=10.5
        ))
        
        # Table cell center style
        self.styles.add(ParagraphStyle(
            name='TableCellCenter',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=10.5
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_RIGHT,
            textColor=self.dark_grey,
            fontName='Helvetica'
        ))
    
    def _create_header_footer(self, canvas_obj: canvas.Canvas, doc: SimpleDocTemplate, report_type: str):
        """Create header and footer on each page"""
        # Header
        header_text = f"{self.player.fullName} | {self.player.currentClub} | {self.player.seasonLabel} | {report_type}"
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(self.dark_grey)
        canvas_obj.drawString(self.margin, self.page_height - 20, header_text)
        
        # Footer
        gen_date = get_report_generation_date()
        footer_text = f"Page {canvas_obj.getPageNumber()} | Report Generated: {gen_date}"
        canvas_obj.drawString(self.margin, 20, footer_text)
    
    def _create_table(self, data: List[List], col_widths: Optional[List[float]] = None) -> Table:
        """Create a styled table"""
        table = Table(data, colWidths=col_widths)
        
        # Apply table style
        style = TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ])
        
        # Alternate row colors
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), self.light_grey)
        
        table.setStyle(style)
        return table

