"""
Scout Report Generator

One to two pages maximum, fastest possible scout-read, high signal only.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas
from typing import List

from .base_generator import BasePDFGenerator
from .types import Player
from .metrics import calculate_metrics, get_top_performances
from .formatters import (
    format_date_iso_to_display,
    format_per_60,
    format_percentage,
    format_minutes_per,
    format_height_cm,
    format_weight_kg,
    format_bmi,
    calculate_age,
    truncate_text
)


class ScoutReportGenerator(BasePDFGenerator):
    """Generator for Scout Report (1-2 pages max)"""
    
    def generate(self, output_path: str) -> str:
        """
        Generate Scout Report PDF (1-2 pages maximum).
        
        Args:
            output_path: Path to save the PDF
            
        Returns:
            Path to generated PDF
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        story = []
        
        # Player snapshot (top of page)
        story.extend(self._create_player_snapshot())
        story.append(Spacer(1, 16))
        
        # Key performance indicators (compact grid)
        story.extend(self._create_kpi_grid())
        story.append(Spacer(1, 16))
        
        # Standout performances
        story.extend(self._create_standout_performances())
        story.append(Spacer(1, 16))
        
        # Playing profile (only if supported by input fields)
        # Note: We don't have structured "strengths" fields in the current model,
        # so we'll check for playing_profile in settings if available
        # For now, we'll omit this section as per requirements
        
        # Media and contact (small block at bottom)
        story.extend(self._create_media_contact())
        
        # Build PDF with header/footer
        def on_each_page(canvas_obj, doc_obj):
            self._create_header_footer(canvas_obj, doc_obj, "Scout Report")
        
        doc.build(story, onFirstPage=on_each_page, onLaterPages=on_each_page)
        return output_path
    
    def _create_player_snapshot(self) -> List:
        """Create player snapshot section"""
        elements = []
        
        elements.append(Paragraph("Player Snapshot", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        # Calculate age
        age = calculate_age(self.player.dob)
        age_text = f"{age:.1f} years" if age else "Not recorded"
        
        # Build snapshot data
        snapshot_data = []
        snapshot_data.append(["Full Name", self.player.fullName])
        
        if self.player.dob:
            dob_display = format_date_iso_to_display(self.player.dob)
            snapshot_data.append(["Date of Birth", f"{dob_display} (Age: {age_text})"])
        
        if self.player.nationality:
            snapshot_data.append(["Nationality", self.player.nationality])
        
        position_text = self.player.positionPrimary
        if self.player.positionSecondary:
            position_text += f" / {', '.join(self.player.positionSecondary)}"
        snapshot_data.append(["Position", position_text])
        
        if self.player.dominantFoot:
            snapshot_data.append(["Dominant Foot", self.player.dominantFoot])
        
        snapshot_data.append(["Current Club", self.player.currentClub])
        snapshot_data.append(["Team", self.player.team])
        snapshot_data.append(["Season", self.player.seasonLabel])
        
        if self.player.heightCm:
            snapshot_data.append(["Height", format_height_cm(self.player.heightCm)])
        
        if self.player.weightKg:
            snapshot_data.append(["Weight", format_weight_kg(self.player.weightKg)])
        
        if self.player.bmi:
            snapshot_data.append(["BMI", format_bmi(self.player.bmi)])
        
        # PHV status (short line only)
        if self.player.phv and self.player.phv.status:
            phv_text = f"PHV Status: {self.player.phv.status}"
            if self.player.phv.phvAgeYears:
                phv_text += f" (Age: {self.player.phv.phvAgeYears:.1f} years)"
            snapshot_data.append(["PHV", phv_text])
        
        # Create compact table
        table = self._create_table(snapshot_data, col_widths=[self.content_width * 0.35, self.content_width * 0.65])
        elements.append(table)
        
        return elements
    
    def _create_kpi_grid(self) -> List:
        """Create key performance indicators in compact grid"""
        elements = []
        
        elements.append(Paragraph("Key Performance Indicators", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        metrics = calculate_metrics(self.player.matches)
        
        # Create compact KPI grid
        kpi_data = [
            ['Metric', 'Value'],
            ['Total Matches', str(metrics.totalMatches)],
            ['Total Minutes', str(metrics.totalMinutes)],
            ['Total Goals', str(metrics.totalGoals)],
            ['Total Assists', str(metrics.totalAssists)],
            ['Total Contributions', str(metrics.totalContributions)],
            ['Goals per 60', format_per_60(metrics.goalsPer60)],
            ['Contributions per 60', format_per_60(metrics.contributionsPer60)],
            ['Goal Involvement Rate', format_percentage(metrics.goalInvolvementRate)],
            ['Minutes per Contribution', format_minutes_per(metrics.minutesPerContribution)],
        ]
        
        table = self._create_table(kpi_data, col_widths=[self.content_width * 0.6, self.content_width * 0.4])
        elements.append(table)
        
        return elements
    
    def _create_standout_performances(self) -> List:
        """Create standout performances section (top 3)"""
        elements = []
        
        elements.append(Paragraph("Standout Performances", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        top_performances = get_top_performances(self.player.matches, top_n=3)
        
        if top_performances:
            perf_data = [['Date', 'Opponent', 'Contributions', 'Note']]
            for match in top_performances:
                note = truncate_text(match.notes, max_length=40) if match.notes else ""
                perf_data.append([
                    format_date_iso_to_display(match.date),
                    match.opponent or "N/A",
                    str(match.goals + match.assists),
                    note
                ])
            
            table = self._create_table(perf_data)
            elements.append(table)
        else:
            elements.append(Paragraph("No standout performances recorded.", self.styles['Normal']))
        
        return elements
    
    def _create_media_contact(self) -> List:
        """Create media and contact section (small block at bottom)"""
        elements = []
        
        elements.append(Paragraph("Media & Contact", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        contact_data = []
        
        if self.player.highlightReelUrl:
            contact_data.append(["Highlight Reel", self.player.highlightReelUrl])
        
        if self.player.socialLinks:
            for link in self.player.socialLinks:
                contact_data.append([link.platform, link.url])
        
        if self.player.contactEmail:
            contact_data.append(["Contact Email", self.player.contactEmail])
        
        if contact_data:
            table = self._create_table(contact_data, col_widths=[self.content_width * 0.3, self.content_width * 0.7])
            elements.append(table)
        else:
            elements.append(Paragraph("No media or contact information recorded.", self.styles['Normal']))
        
        return elements


def generate_scout_report(player: Player, output_dir: str = "output") -> str:
    """
    Generate Scout Report PDF (1-2 pages maximum).
    
    Args:
        player: Player object with match data
        output_dir: Output directory for PDF
        
    Returns:
        Path to generated PDF file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    from datetime import datetime
    safe_name = player.fullName.replace(' ', '_')
    safe_club = player.currentClub.replace(' ', '_')
    safe_season = player.seasonLabel.replace('/', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_club}_{safe_name}_Scout_Report_{safe_season}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    # Generate PDF
    generator = ScoutReportGenerator(player)
    return generator.generate(output_path)

