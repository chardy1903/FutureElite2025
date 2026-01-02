"""
Player Resume Report Generator

Comprehensive career document, multi-page allowed.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfgen import canvas
from typing import List

from .base_generator import BasePDFGenerator
from .types import Player
from .metrics import calculate_metrics, calculate_match_results
from .formatters import (
    format_date_iso_to_display,
    format_per_60,
    format_per_match,
    format_percentage,
    format_minutes_per,
    format_height_cm,
    format_weight_kg,
    format_bmi,
    format_predicted_height_cm,
    calculate_age
)


class PlayerResumeGenerator(BasePDFGenerator):
    """Generator for Player Resume reports"""
    
    def generate(self, output_path: str) -> str:
        """
        Generate Player Resume PDF report.
        
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
        
        # 1. Identity & snapshot
        story.extend(self._create_identity_snapshot())
        story.append(PageBreak())
        
        # 2. Season performance summary
        story.extend(self._create_performance_summary())
        story.append(Spacer(1, 16))
        
        # 3. Match contribution overview
        story.extend(self._create_contribution_overview())
        story.append(PageBreak())
        
        # 4. Achievements & awards
        story.extend(self._create_achievements())
        story.append(Spacer(1, 16))
        
        # 5. Physical development and growth
        story.extend(self._create_physical_development())
        story.append(Spacer(1, 16))
        
        # 6. Club history
        story.extend(self._create_club_history())
        story.append(PageBreak())
        
        # 7. Training & development exposure
        story.extend(self._create_training_camps())
        story.append(Spacer(1, 16))
        
        # 8. References
        story.extend(self._create_references())
        
        # Build PDF with header/footer
        def on_each_page(canvas_obj, doc_obj):
            self._create_header_footer(canvas_obj, doc_obj, "Player Resume")
        
        doc.build(story, onFirstPage=on_each_page, onLaterPages=on_each_page)
        return output_path
    
    def _create_identity_snapshot(self) -> List:
        """Create identity & snapshot section"""
        elements = []
        
        elements.append(Paragraph("Identity & Snapshot", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        # Calculate age
        age = calculate_age(self.player.dob)
        age_text = f"{age:.1f} years" if age else "Not recorded"
        
        identity_data = []
        identity_data.append(["Full Name", self.player.fullName])
        
        if self.player.dob:
            dob_display = format_date_iso_to_display(self.player.dob)
            identity_data.append(["Date of Birth", f"{dob_display} (Age: {age_text})"])
        
        if self.player.nationality:
            identity_data.append(["Nationality", self.player.nationality])
        
        identity_data.append(["Current Club", self.player.currentClub])
        identity_data.append(["Team", self.player.team])
        identity_data.append(["Season", self.player.seasonLabel])
        
        position_text = self.player.positionPrimary
        if self.player.positionSecondary:
            position_text += f" / {', '.join(self.player.positionSecondary)}"
        identity_data.append(["Position", position_text])
        
        if self.player.dominantFoot:
            identity_data.append(["Dominant Foot", self.player.dominantFoot])
        
        if self.player.heightCm:
            identity_data.append(["Height", format_height_cm(self.player.heightCm)])
        
        if self.player.weightKg:
            identity_data.append(["Weight", format_weight_kg(self.player.weightKg)])
        
        if self.player.bmi:
            identity_data.append(["BMI", format_bmi(self.player.bmi)])
        
        # PHV summary and predicted adult height
        if self.player.phv:
            phv_text = ""
            if self.player.phv.status:
                phv_text = f"Status: {self.player.phv.status}"
            if self.player.phv.phvAgeYears:
                phv_text += f" (Age: {self.player.phv.phvAgeYears:.1f} years)" if phv_text else f"Age: {self.player.phv.phvAgeYears:.1f} years"
            if phv_text:
                identity_data.append(["PHV Status", phv_text])
            
            if self.player.phv.predictedAdultHeightCm:
                height_text = format_predicted_height_cm(self.player.phv.predictedAdultHeightCm)
                if self.player.phv.predictedAdultHeightConfidence:
                    height_text += f" (Confidence: {self.player.phv.predictedAdultHeightConfidence})"
                identity_data.append(["Predicted Adult Height", height_text])
        
        table = self._create_table(identity_data, col_widths=[self.content_width * 0.35, self.content_width * 0.65])
        elements.append(table)
        
        return elements
    
    def _create_performance_summary(self) -> List:
        """Create season performance summary"""
        elements = []
        
        elements.append(Paragraph("Season Performance Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        metrics = calculate_metrics(self.player.matches)
        
        # Standardized metrics
        perf_data = [
            ['Metric', 'Value'],
            ['Total Matches', str(metrics.totalMatches)],
            ['Total Minutes', str(metrics.totalMinutes)],
            ['Total Goals', str(metrics.totalGoals)],
            ['Total Assists', str(metrics.totalAssists)],
            ['Total Contributions', str(metrics.totalContributions)],
            ['Goals per 60', format_per_60(metrics.goalsPer60)],
            ['Assists per 60', format_per_60(metrics.assistsPer60)],
            ['Contributions per 60', format_per_60(metrics.contributionsPer60)],
            ['Goals per Match', format_per_match(metrics.goalsPerMatch)],
            ['Assists per Match', format_per_match(metrics.assistsPerMatch)],
            ['Contributions per Match', format_per_match(metrics.contributionsPerMatch)],
            ['Minutes per Goal', format_minutes_per(metrics.minutesPerGoal)],
            ['Minutes per Contribution', format_minutes_per(metrics.minutesPerContribution)],
        ]
        
        # Add wins/draws/losses if available
        results = calculate_match_results(self.player.matches)
        if results['total'] > 0:
            perf_data.append(['Wins', str(results['wins'])])
            perf_data.append(['Draws', str(results['draws'])])
            perf_data.append(['Losses', str(results['losses'])])
        
        table = self._create_table(perf_data, col_widths=[self.content_width * 0.6, self.content_width * 0.4])
        elements.append(table)
        
        return elements
    
    def _create_contribution_overview(self) -> List:
        """Create match contribution overview"""
        elements = []
        
        elements.append(Paragraph("Match Contribution Overview", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        metrics = calculate_metrics(self.player.matches)
        
        contrib_data = [
            ['Metric', 'Value'],
            ['Goal Involvement Rate', format_percentage(metrics.goalInvolvementRate)],
            ['Matches with Goal', str(metrics.matchesWithGoal)],
            ['Matches with Assist', str(metrics.matchesWithAssist)],
            ['Matches with Contribution', str(metrics.matchesWithContribution)],
            ['Contributions per 60', format_per_60(metrics.contributionsPer60)],
        ]
        
        table = self._create_table(contrib_data, col_widths=[self.content_width * 0.6, self.content_width * 0.4])
        elements.append(table)
        
        return elements
    
    def _create_achievements(self) -> List:
        """Create achievements & awards section"""
        elements = []
        
        elements.append(Paragraph("Achievements & Awards", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        if self.player.awards:
            # Sort by date descending
            sorted_awards = sorted(
                self.player.awards,
                key=lambda a: a.date,
                reverse=True
            )
            
            awards_data = [['Date', 'Title', 'Category', 'Description']]
            for award in sorted_awards:
                awards_data.append([
                    format_date_iso_to_display(award.date),
                    award.title,
                    award.category,
                    award.description or ""
                ])
            
            table = self._create_table(awards_data)
            elements.append(table)
        else:
            elements.append(Paragraph("No achievements recorded.", self.styles['Normal']))
        
        return elements
    
    def _create_physical_development(self) -> List:
        """Create physical development and growth section"""
        elements = []
        
        elements.append(Paragraph("Physical Development and Growth", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        # Growth history table
        if self.player.growthHistory:
            # Sort by date ascending
            sorted_growth = sorted(self.player.growthHistory, key=lambda g: g.date)
            
            growth_data = [['Date', 'Height (cm)', 'Weight (kg)', 'Notes']]
            for entry in sorted_growth:
                growth_data.append([
                    format_date_iso_to_display(entry.date),
                    format_height_cm(entry.heightCm) if entry.heightCm else "Not recorded",
                    format_weight_kg(entry.weightKg) if entry.weightKg else "Not recorded",
                    entry.notes or ""
                ])
            
            table = self._create_table(growth_data)
            elements.append(table)
            elements.append(Spacer(1, 12))
        
        # PHV detail block
        if self.player.phv:
            phv_elements = []
            phv_elements.append(Paragraph("PHV Details", ParagraphStyle(
                name='SubHeader',
                parent=self.styles['Normal'],
                fontSize=10,
                fontName='Helvetica-Bold',
                spaceAfter=8
            )))
            
            phv_data = []
            if self.player.phv.phvDate:
                phv_data.append(["PHV Date", format_date_iso_to_display(self.player.phv.phvDate)])
            if self.player.phv.phvAgeYears is not None:
                phv_data.append(["PHV Age", f"{self.player.phv.phvAgeYears:.1f} years"])
            if self.player.phv.status:
                phv_data.append(["PHV Status", self.player.phv.status])
            if self.player.phv.peakGrowthVelocityCmPerYear is not None:
                phv_data.append(["Peak Growth Velocity", f"{self.player.phv.peakGrowthVelocityCmPerYear:.1f} cm/year"])
            if self.player.phv.predictedAdultHeightCm is not None:
                phv_data.append(["Predicted Adult Height", format_predicted_height_cm(self.player.phv.predictedAdultHeightCm)])
            if self.player.phv.predictedAdultHeightConfidence:
                phv_data.append(["Prediction Confidence", self.player.phv.predictedAdultHeightConfidence])
            
            if phv_data:
                table = self._create_table(phv_data, col_widths=[self.content_width * 0.4, self.content_width * 0.6])
                phv_elements.append(table)
            
            elements.extend(phv_elements)
        else:
            if not self.player.growthHistory:
                elements.append(Paragraph("No physical development data recorded.", self.styles['Normal']))
        
        return elements
    
    def _create_club_history(self) -> List:
        """Create club history section"""
        elements = []
        
        elements.append(Paragraph("Club History", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        if self.player.clubHistory:
            # Sort by season descending
            sorted_clubs = sorted(
                self.player.clubHistory,
                key=lambda c: c.season,
                reverse=True
            )
            
            club_data = [['Club Name', 'Season', 'Age Group', 'Position', 'Achievements']]
            for club in sorted_clubs:
                club_data.append([
                    club.clubName,
                    club.season,
                    club.ageGroup or "Not recorded",
                    club.position or "Not recorded",
                    club.achievements or ""
                ])
            
            table = self._create_table(club_data)
            elements.append(table)
        else:
            elements.append(Paragraph("No club history recorded.", self.styles['Normal']))
        
        return elements
    
    def _create_training_camps(self) -> List:
        """Create training & development exposure section"""
        elements = []
        
        elements.append(Paragraph("Training & Development Exposure", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        if self.player.camps:
            # Sort by endDate descending
            sorted_camps = sorted(
                self.player.camps,
                key=lambda c: c.endDate,
                reverse=True
            )
            
            camps_data = [['Camp Name', 'Organizer', 'Location', 'Start Date', 'End Date', 'Age Group', 'Focus Area']]
            for camp in sorted_camps:
                camps_data.append([
                    camp.name,
                    camp.organizer or "Not recorded",
                    camp.location or "Not recorded",
                    format_date_iso_to_display(camp.startDate),
                    format_date_iso_to_display(camp.endDate),
                    camp.ageGroup or "Not recorded",
                    camp.focusArea or "Not recorded"
                ])
            
            table = self._create_table(camps_data)
            elements.append(table)
        else:
            elements.append(Paragraph("No training camps recorded.", self.styles['Normal']))
        
        return elements
    
    def _create_references(self) -> List:
        """Create references section"""
        elements = []
        
        elements.append(Paragraph("References", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        if self.player.references:
            ref_data = [['Name', 'Role', 'Club', 'Email', 'Phone', 'Notes']]
            for ref in self.player.references:
                ref_data.append([
                    ref.name,
                    ref.role or "Not recorded",
                    ref.club or "Not recorded",
                    ref.email or "Not recorded",
                    ref.phone or "Not recorded",
                    ref.notes or ""
                ])
            
            table = self._create_table(ref_data)
            elements.append(table)
        else:
            elements.append(Paragraph("No references recorded.", self.styles['Normal']))
        
        return elements


def generate_player_resume(player: Player, output_dir: str = "output") -> str:
    """
    Generate Player Resume PDF report.
    
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
    filename = f"{safe_club}_{safe_name}_Player_Resume_{safe_season}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    # Generate PDF
    generator = PlayerResumeGenerator(player)
    return generator.generate(output_path)

