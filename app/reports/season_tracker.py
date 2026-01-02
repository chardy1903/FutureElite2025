"""
Season Tracker Report Generator

Detailed match-by-match log for the current season.
"""

import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from typing import List

from .base_generator import BasePDFGenerator
from .types import Player
from .metrics import calculate_metrics, get_top_performances, get_recent_form
from .formatters import (
    format_date_iso_to_display,
    format_per_60,
    format_per_match,
    format_minutes_per,
    truncate_text
)


class SeasonTrackerGenerator(BasePDFGenerator):
    """Generator for Season Tracker reports"""
    
    def generate(self, output_path: str) -> str:
        """
        Generate Season Tracker PDF report.
        
        Args:
            output_path: Path to save the PDF
            
        Returns:
            Path to generated PDF
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        story = []
        
        # Cover header block
        story.extend(self._create_cover_header())
        story.append(Spacer(1, 20))
        
        # Season summary metrics
        story.extend(self._create_season_summary())
        story.append(Spacer(1, 20))
        
        # Performance highlights
        story.extend(self._create_performance_highlights())
        story.append(PageBreak())
        
        # Season match data table
        story.extend(self._create_match_table())
        
        # Build PDF with header/footer
        def on_each_page(canvas_obj, doc_obj):
            self._create_header_footer(canvas_obj, doc_obj, "Season Tracker")
        
        doc.build(story, onFirstPage=on_each_page, onLaterPages=on_each_page)
        return output_path
    
    def _create_cover_header(self) -> List:
        """Create cover header block"""
        elements = []
        
        # Title
        title = Paragraph("Season Tracker", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Player info
        player_info = f"{self.player.fullName} | {self.player.currentClub} | {self.player.team} | {self.player.seasonLabel}"
        elements.append(Paragraph(player_info, self.styles['Normal']))
        elements.append(Spacer(1, 16))
        
        # Big summary line
        metrics = calculate_metrics(self.player.matches)
        summary = f"{metrics.totalMatches} Matches | {metrics.totalGoals} Goals | {metrics.totalAssists} Assists | {metrics.totalContributions} Goal Contributions"
        summary_para = Paragraph(summary, ParagraphStyle(
            name='Summary',
            parent=self.styles['Normal'],
            fontSize=14,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            textColor=self.primary_color
        ))
        elements.append(summary_para)
        
        return elements
    
    def _create_season_summary(self) -> List:
        """Create season summary metrics table"""
        elements = []
        
        elements.append(Paragraph("Season Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        metrics = calculate_metrics(self.player.matches)
        
        # Create summary table
        data = [
            ['Metric', 'Value'],
            ['Total Matches', str(metrics.totalMatches)],
            ['Total Minutes', str(metrics.totalMinutes)],
            ['Total Goals', str(metrics.totalGoals)],
            ['Total Assists', str(metrics.totalAssists)],
            ['Total Contributions', str(metrics.totalContributions)],
            ['Goals per 60', format_per_60(metrics.goalsPer60)],
            ['Assists per 60', format_per_60(metrics.assistsPer60)],
            ['Contributions per 60', format_per_60(metrics.contributionsPer60)],
            ['Contributions per Match', format_per_match(metrics.contributionsPerMatch)],
            ['Minutes per Contribution', format_minutes_per(metrics.minutesPerContribution)],
        ]
        
        table = self._create_table(data, col_widths=[self.content_width * 0.6, self.content_width * 0.4])
        elements.append(table)
        
        return elements
    
    def _create_performance_highlights(self) -> List:
        """Create performance highlights section"""
        elements = []
        
        elements.append(Paragraph("Performance Highlights", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        metrics = calculate_metrics(self.player.matches)
        
        # Top Performances
        top_performances = get_top_performances(self.player.matches, top_n=3)
        if top_performances:
            elements.append(Paragraph("Top Performances", ParagraphStyle(
                name='SubHeader',
                parent=self.styles['Normal'],
                fontSize=10,
                fontName='Helvetica-Bold',
                spaceAfter=8
            )))
            
            perf_data = [['Date', 'Opponent', 'Contributions', 'Goals', 'Assists', 'Minutes']]
            for match in top_performances:
                perf_data.append([
                    format_date_iso_to_display(match.date),
                    match.opponent or "N/A",
                    str(match.goals + match.assists),
                    str(match.goals),
                    str(match.assists),
                    str(match.minutesPlayed)
                ])
            
            table = self._create_table(perf_data)
            elements.append(table)
            elements.append(Spacer(1, 12))
        
        # Goal scoring consistency
        if metrics.totalMatches > 0:
            consistency_rate = (metrics.matchesWithGoal / metrics.totalMatches) * 100
            consistency_text = f"Goal Scoring Consistency: {metrics.matchesWithGoal} matches with goals out of {metrics.totalMatches} total matches ({consistency_rate:.1f}%)"
            elements.append(Paragraph(consistency_text, self.styles['Normal']))
            elements.append(Spacer(1, 8))
        
        # Recent form
        recent = get_recent_form(self.player.matches, last_n=5)
        if recent['matches'] > 0:
            form_text = f"Recent Form (Last {recent['matches']} matches): {recent['goals']} goals, {recent['assists']} assists"
            elements.append(Paragraph(form_text, self.styles['Normal']))
        
        return elements
    
    def _create_match_table(self) -> List:
        """Create full season match data table"""
        elements = []
        
        elements.append(Paragraph("Season Match Data", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        # Sort matches by date
        sorted_matches = sorted(self.player.matches, key=lambda m: m.date)
        
        # Create table data
        table_data = [['MD', 'Opponent', 'Location', 'Date', 'Category', 'Score', 'G', 'A', 'Min', 'Notes']]
        
        for i, match in enumerate(sorted_matches, 1):
            # Truncate notes to avoid layout issues
            notes = truncate_text(match.notes, max_length=30)
            
            # Format score
            if match.scoreFor is not None and match.scoreAgainst is not None:
                score = f"{match.scoreFor} - {match.scoreAgainst}"
            else:
                score = "Not recorded"
            
            table_data.append([
                str(match.matchDay) if match.matchDay else str(i),
                match.opponent or "N/A",
                match.location or "N/A",
                format_date_iso_to_display(match.date),
                match.category or "N/A",
                score,
                str(match.goals),
                str(match.assists),
                str(match.minutesPlayed),
                notes
            ])
        
        # Calculate column widths (landscape A4)
        col_widths = [
            self.content_width * 0.05,  # MD
            self.content_width * 0.15,  # Opponent
            self.content_width * 0.12,  # Location
            self.content_width * 0.10,  # Date
            self.content_width * 0.10,  # Category
            self.content_width * 0.08,  # Score
            self.content_width * 0.05,  # G
            self.content_width * 0.05,  # A
            self.content_width * 0.05,  # Min
            self.content_width * 0.25,  # Notes
        ]
        
        table = self._create_table(table_data, col_widths=col_widths)
        elements.append(table)
        
        return elements


def generate_season_tracker(player: Player, output_dir: str = "output") -> str:
    """
    Generate Season Tracker PDF report.
    
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
    filename = f"{safe_club}_{safe_name}_Season_Tracker_{safe_season}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    # Generate PDF
    generator = SeasonTrackerGenerator(player)
    return generator.generate(output_path)

