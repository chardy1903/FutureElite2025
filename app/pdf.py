from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
from typing import List, Dict, Any
import os

from .models import Match, AppSettings, PhysicalMeasurement, Achievement, ClubHistory, TrainingCamp, PhysicalMetrics, Reference
from .utils import sort_matches_by_date, filter_matches_by_period


class PDFGenerator:
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.page_width, self.page_height = landscape(A4)
        self.margin = 36  # 36 points = 0.5 inch
        self.content_width = self.page_width - (2 * self.margin)
        
        # Define colors
        self.primary_color = colors.HexColor(settings.primary_color)  # Qadsiah red
        self.header_color = colors.HexColor(settings.header_color)    # Header grey
        self.light_grey = colors.HexColor("#F3F4F6")
        self.dark_grey = colors.HexColor("#6B7280")
        
        # Create styles
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
        # Period tracking
        self.period = 'all_time'
    
    def _get_period_label(self) -> str:
        """Get human-readable label for the current period"""
        period_labels = {
            'all_time': 'All Time',
            'season': f'Season {self.settings.season_year}',
            '12_months': 'Last 12 Months',
            '6_months': 'Last 6 Months',
            '3_months': 'Last 3 Months',
            'last_month': 'Last Month'
        }
        return period_labels.get(self.period, 'All Time')

    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=16,
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
            fontSize=9.5,
            alignment=TA_CENTER,
            textColor=colors.white,
            fontName='Helvetica-Bold'
        ))
        
        # Table cell style
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=9.5,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=11,
            spaceAfter=2,
            wordWrap='LTR'
        ))
        
        # Table cell center style
        self.styles.add(ParagraphStyle(
            name='TableCellCenter',
            parent=self.styles['Normal'],
            fontSize=9.5,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=11,
            spaceAfter=2,
            wordWrap='LTR'
        ))
        
        # Metric value style (large, bold numbers)
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=18,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            textColor=self.primary_color,
            leading=22,
            spaceAfter=4
        ))
        
        # Metric label style
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=8.5,
            alignment=TA_CENTER,
            fontName='Helvetica',
            textColor=self.dark_grey,
            leading=10,
            spaceAfter=0
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

    def generate_pdf(self, matches: List[Match], output_path: str, physical_measurements: List[PhysicalMeasurement] = None, physical_metrics: List[PhysicalMetrics] = None, period: str = 'all_time') -> str:
        """Generate the complete PDF report
        
        Args:
            matches: List of all matches
            output_path: Path to save the PDF
            physical_measurements: List of physical measurements
            physical_metrics: List of physical metrics
            period: Time period filter ('all_time', 'season', '12_months', '6_months', '3_months', 'last_month')
        """
        # Filter matches by period if specified
        if period and period != 'all_time':
            matches = filter_matches_by_period(matches, period, self.settings.season_year)
        
        self.period = period  # Store period for use in sections
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        story = []
        
        # PAGE 1: Cover page
        story.extend(self._create_cover_page(matches))
        story.append(PageBreak())
        
        # PAGE 2: Player profile (simplified) + performance metrics
        page2_elements = []
        page2_elements.extend(self._create_player_profile_simplified(physical_metrics or []))
        page2_elements.append(Spacer(1, 12))
        page2_elements.extend(self._create_advanced_metrics(matches))
        story.append(KeepTogether(page2_elements))
        story.append(PageBreak())
        
        # PAGE 3: Performance highlights
        story.extend(self._create_performance_highlights(matches))
        story.append(PageBreak())
        
        # PAGE 4: Season match data (all matches combined)
        all_matches = [m for m in matches if not m.is_fixture]
        if all_matches:
            story.extend(self._create_season_matches_table(all_matches))
        
        # Add footer
        story.append(self._create_footer(matches))
        
        # Build PDF
        doc.build(story)
        return output_path

    def _create_summary_table(self, matches: List[Match]) -> List:
        """Create the summary statistics table"""
        elements = []
        
        # Calculate stats
        pre_season_matches = [m for m in matches if m.category.value == "Pre-Season Friendly" and not m.is_fixture]
        league_matches = [m for m in matches if m.category.value == "League" and not m.is_fixture]
        all_matches = [m for m in matches if not m.is_fixture]
        
        pre_season_stats = self._calculate_category_stats(pre_season_matches)
        league_stats = self._calculate_category_stats(league_matches)
        total_stats = self._calculate_category_stats(all_matches)
        
        # Table data
        data = [
            ['Category', 'Matches', 'Goals', 'Assists', 'Minutes'],
            ['Pre-Season Friendlies', str(pre_season_stats['matches']), 
             str(pre_season_stats['goals']), str(pre_season_stats['assists']), 
             str(pre_season_stats['minutes'])],
            ['League Matches', str(league_stats['matches']), 
             str(league_stats['goals']), str(league_stats['assists']), 
             str(league_stats['minutes'])],
            ['Total Season', str(total_stats['matches']), 
             str(total_stats['goals']), str(total_stats['assists']), 
             str(total_stats['minutes'])]
        ]
        
        # Create table
        table = Table(data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        
        # Style the table
        table_style = TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9.5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        return elements

    def _create_pre_season_table(self, matches: List[Match]) -> List:
        """Create the pre-season friendlies table"""
        elements = []
        
        # Sort matches by date
        sorted_matches = sort_matches_by_date(matches)
        
        # Table data with performance indicator
        data = [['MD', 'Team', 'Season', 'Opponent', 'Location', 'Date', 'Category', 'Score', 'G', 'A', 'Min', 'Notes']]
        
        for i, match in enumerate(sorted_matches, 1):
            # Create performance indicator
            g_a = match.brodie_goals + match.brodie_assists
            perf_indicator = ""
            if g_a >= 3:
                perf_indicator = "★★★"
            elif g_a >= 2:
                perf_indicator = "★★"
            elif g_a >= 1:
                perf_indicator = "★"
            
            # Format score - ensure it's displayed if it exists
            score_display = match.score if match.score and match.score.strip() else ''
            
            row = [
                str(i),  # MD
                self.settings.club_name,  # Team
                self.settings.season_year,  # Season
                match.opponent,
                match.location,
                match.date,
                match.category.value,  # Category
                score_display,
                str(match.brodie_goals) + (perf_indicator if match.brodie_goals > 0 else ""),
                str(match.brodie_assists) + (perf_indicator if match.brodie_assists > 0 else ""),
                str(match.minutes_played),
                match.notes or ''
            ]
            data.append(row)
        
        # Create table with appropriate column widths (updated for new columns)
        col_widths = [0.4*inch, 1*inch, 0.8*inch, 1.2*inch, 1.2*inch, 0.9*inch, 1*inch, 0.7*inch, 0.5*inch, 0.5*inch, 0.6*inch, 1.2*inch]
        
        # Convert text data to Paragraphs for proper wrapping
        wrapped_data = []
        for row_idx, row in enumerate(data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:  # Header row
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    if col_idx in [3, 4, 11]:  # Opponent, Location, Notes columns - wrap text
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                    else:  # Other columns - center align
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
            wrapped_data.append(wrapped_row)
        
        table = Table(wrapped_data, colWidths=col_widths)
        
        # Style the table
        table_style = TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9.5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9.5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            
            # Text alignment for specific columns
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),  # Opponent
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),  # Location
            ('ALIGN', (11, 1), (11, -1), 'LEFT'),  # Notes
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Padding for better text wrapping
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        return elements

    def _create_season_matches_table(self, matches: List[Match]) -> List:
        """Create the season matches table with header repeating on each page"""
        elements = []
        
        # Section header
        elements.append(Paragraph("Season Match Data", self.styles['SectionHeader']))
        elements.append(Spacer(1, 8))
        
        # Sort matches by date
        sorted_matches = sort_matches_by_date(matches)
        
        # Table data with performance indicator
        data = [['MD', 'Team', 'Season', 'Opponent', 'Location', 'Date', 'Category', 'Score', 'G', 'A', 'Min', 'Notes']]
        
        for i, match in enumerate(sorted_matches, 1):
            # Create performance indicator
            g_a = match.brodie_goals + match.brodie_assists
            perf_indicator = ""
            if g_a >= 3:
                perf_indicator = "★★★"
            elif g_a >= 2:
                perf_indicator = "★★"
            elif g_a >= 1:
                perf_indicator = "★"
            
            # Format score - ensure it's displayed if it exists
            score_display = match.score if match.score and match.score.strip() else ''
            
            row = [
                str(i),
                self.settings.club_name,  # Team
                self.settings.season_year,  # Season
                match.opponent,
                match.location,
                match.date,
                match.category.value,  # Category
                score_display,
                str(match.brodie_goals) + (perf_indicator if match.brodie_goals > 0 else ""),
                str(match.brodie_assists) + (perf_indicator if match.brodie_assists > 0 else ""),
                str(match.minutes_played),
                match.notes or ''
            ]
            data.append(row)
        
        col_widths = [0.4*inch, 1*inch, 0.8*inch, 1.2*inch, 1.2*inch, 0.9*inch, 1*inch, 0.7*inch, 0.5*inch, 0.5*inch, 0.6*inch, 1.2*inch]
        
        wrapped_data = []
        for row_idx, row in enumerate(data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    if col_idx in [3, 4, 11]:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                    else:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
            wrapped_data.append(wrapped_row)
        
        # Use repeatRows=1 to repeat header on each page
        table = Table(wrapped_data, colWidths=col_widths, repeatRows=1)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9.5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9.5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),
            ('ALIGN', (11, 1), (11, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        table.setStyle(table_style)
        elements.append(table)
        return elements
    
    def _create_league_matches_table(self, matches: List[Match]) -> List:
        """Create the league matches table (legacy - kept for compatibility)"""
        return self._create_season_matches_table(matches)

    def _create_league_section(self) -> List:
        """Create the league section with group tables"""
        elements = []
        
        # League heading
        league_heading = Paragraph(f"{self.settings.league_name}", self.styles['SectionHeader'])
        elements.append(league_heading)
        elements.append(Spacer(1, 12))
        
        # Create two-column layout for groups
        group1_data = [['Group 1']] + [[team] for team in self.settings.group1_teams]
        group2_data = [['Group 2']] + [[team] for team in self.settings.group2_teams]
        
        # Group 1 table
        group1_table = Table(group1_data, colWidths=[3*inch])
        group1_style = TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (0, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        group1_table.setStyle(group1_style)
        
        # Group 2 table
        group2_table = Table(group2_data, colWidths=[3*inch])
        group2_style = TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (0, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        group2_table.setStyle(group2_style)
        
        # Create two-column layout
        group_layout = Table([[group1_table, group2_table]], colWidths=[3*inch, 3*inch])
        group_layout_style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ])
        group_layout.setStyle(group_layout_style)
        
        elements.append(group_layout)
        elements.append(Spacer(1, 12))
        
        # Qualification text
        qual_text = "From a single round, the top two teams from each group qualify, followed by semi-finals between the four clubs."
        qual_para = Paragraph(qual_text, self.styles['TableCell'])
        elements.append(qual_para)
        
        return elements
    
    def _create_footer(self, matches: List[Match]) -> Paragraph:
        """Create the footer with latest match date"""
        # Find the latest match date
        latest_date = "N/A"
        completed_matches = [m for m in matches if not m.is_fixture and m.date]
        if completed_matches:
            sorted_matches = sort_matches_by_date(completed_matches)
            if sorted_matches:
                latest_date = sorted_matches[-1].date
        
        footer_text = f"Updated: {latest_date} – Season Summary"
        return Paragraph(footer_text, self.styles['Footer'])

    def _create_player_profile_simplified(self, physical_metrics: List[PhysicalMetrics] = None) -> List:
        """Create simplified player profile section - name, DOB, position, current club, performance metrics"""
        elements = []
        
        elements.append(Paragraph("Player Profile", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        # Build profile data - only essential info
        profile_rows = []
        
        # Name
        profile_rows.append(["Name", self.settings.player_name])
        
        # Date of Birth
        if self.settings.date_of_birth:
            profile_rows.append(["Date of Birth", self.settings.date_of_birth])
        
        # Position
        if self.settings.position:
            profile_rows.append(["Position", self.settings.position])
        
        # Current Club
        profile_rows.append(["Current Club", self.settings.club_name])
        
        if profile_rows:
            data = [['Attribute', 'Details']] + profile_rows
            
            profile_table = Table(data, colWidths=[1.5*inch, 6.5*inch])
            profile_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.header_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9.5),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            profile_table.setStyle(profile_style)
            elements.append(profile_table)
        
        return elements
    
    def _create_player_profile(self, physical_measurements: List[PhysicalMeasurement] = None, physical_metrics: List[PhysicalMetrics] = None) -> List:
        """Create player profile section with physical attributes (legacy - kept for compatibility)"""
        return self._create_player_profile_simplified(physical_metrics or [])
    
    def _create_advanced_metrics(self, matches: List[Match]) -> List:
        """Create advanced performance metrics section"""
        elements = []
        
        elements.append(Paragraph("Performance Metrics", self.styles['SectionHeader']))
        
        # Add period label if not all_time
        if self.period != 'all_time':
            period_label = Paragraph(
                f"<i>Statistics for: {self._get_period_label()}</i>",
                ParagraphStyle(
                    name='PeriodLabel',
                    parent=self.styles['Normal'],
                    fontSize=9,
                    textColor=self.dark_grey,
                    alignment=TA_LEFT,
                    spaceAfter=6
                )
            )
            elements.append(period_label)
        
        completed_matches = [m for m in matches if not m.is_fixture]
        all_matches = completed_matches
        league_matches = [m for m in all_matches if m.category.value == "League"]
        
        # Calculate metrics for all matches
        total_stats = self._calculate_advanced_stats(all_matches)
        
        # Calculate metrics for league matches
        league_stats = self._calculate_advanced_stats(league_matches) if league_matches else None
        
        # Create metric cards
        metric_cards = []
        
        # Goals per 60 (actual match length)
        goals_60 = total_stats['goals_per_60']
        metric_cards.append([Paragraph(f"{goals_60:.2f}", self.styles['MetricValue']),
                            Paragraph("Goals/60", self.styles['MetricLabel'])])
        
        # Assists per 60 (actual match length)
        assists_60 = total_stats['assists_per_60']
        metric_cards.append([Paragraph(f"{assists_60:.2f}", self.styles['MetricValue']),
                            Paragraph("Assists/60", self.styles['MetricLabel'])])
        
        # Goal + Assist contributions
        g_a_total = total_stats['goals'] + total_stats['assists']
        metric_cards.append([Paragraph(str(g_a_total), self.styles['MetricValue']),
                            Paragraph("G+A Total", self.styles['MetricLabel'])])
        
        # Contribution rate (G+A per 60)
        contribution_rate = total_stats['contribution_per_60']
        metric_cards.append([Paragraph(f"{contribution_rate:.2f}", self.styles['MetricValue']),
                            Paragraph("G+A/60", self.styles['MetricLabel'])])
        
        # Goals + Assists per match
        if total_stats['matches'] > 0:
            g_a_per_match = (total_stats['goals'] + total_stats['assists']) / total_stats['matches']
            metric_cards.append([Paragraph(f"{g_a_per_match:.2f}", self.styles['MetricValue']),
                                Paragraph("G+A/Match", self.styles['MetricLabel'])])
        
        # Minutes per goal contribution
        if g_a_total > 0:
            min_per_ga = total_stats['minutes'] / g_a_total
            metric_cards.append([Paragraph(f"{min_per_ga:.0f}", self.styles['MetricValue']),
                                Paragraph("Min/G+A", self.styles['MetricLabel'])])
        
        # Create metrics table
        metrics_table = Table([metric_cards], colWidths=[self.content_width / len(metric_cards)] * len(metric_cards))
        metrics_style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), self.light_grey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ])
        metrics_table.setStyle(metrics_style)
        elements.append(metrics_table)
        
        # Add league comparison if available
        if league_stats and league_matches:
            elements.append(Spacer(1, 8))
            league_metrics = []
            league_metrics.append([Paragraph("League Performance", self.styles['TableCell'])])
            league_metrics.append([Paragraph(f"Goals/60: {league_stats['goals_per_60']:.2f} | "
                                            f"Assists/60: {league_stats['assists_per_60']:.2f} | "
                                            f"G+A/60: {league_stats['contribution_per_60']:.2f}",
                                            self.styles['TableCell'])])
            
            league_comp_table = Table(league_metrics, colWidths=[self.content_width])
            league_comp_style = TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), self.header_color),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (0, 0), 9),
                ('BACKGROUND', (0, 1), (0, 1), colors.white),
                ('FONTNAME', (0, 1), (0, 1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (0, 1), 8.5),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            league_comp_table.setStyle(league_comp_style)
            elements.append(league_comp_table)
        
        return elements
    
    def _create_performance_highlights(self, matches: List[Match]) -> List:
        """Create performance highlights section"""
        elements = []
        
        elements.append(Paragraph("Performance Highlights", self.styles['SectionHeader']))
        
        completed_matches = [m for m in matches if not m.is_fixture]
        if not completed_matches:
            return elements
        
        highlights = []
        
        # Find best matches (highest goal contributions)
        best_matches = sorted(completed_matches, 
                            key=lambda m: (m.brodie_goals + m.brodie_assists, m.brodie_goals),
                            reverse=True)[:3]
        
        if best_matches:
            highlights.append(["Top Performances", ""])
            for i, match in enumerate(best_matches, 1):
                contribution = match.brodie_goals + match.brodie_assists
                perf_text = f"{match.date} vs {match.opponent}: {match.brodie_goals}G"
                if match.brodie_assists > 0:
                    perf_text += f", {match.brodie_assists}A"
                if match.result:
                    perf_text += f" ({match.result.value})"
                highlights.append([f"#{i}", perf_text])
        
        # Calculate streaks and consistency
        sorted_matches = sort_matches_by_date(completed_matches)
        if sorted_matches:
            # Goal scoring consistency
            goal_matches = [m for m in sorted_matches if m.brodie_goals > 0]
            if goal_matches:
                highlights.append(["", ""])  # Spacer
                highlights.append(["Goal Scoring Consistency", f"{len(goal_matches)}/{len(sorted_matches)} matches with goals ({len(goal_matches)/len(sorted_matches)*100:.1f}%)"])
            
            # Recent form (last 5 matches)
            recent = sorted_matches[-5:] if len(sorted_matches) >= 5 else sorted_matches
            recent_goals = sum(m.brodie_goals for m in recent)
            recent_assists = sum(m.brodie_assists for m in recent)
            if recent:
                highlights.append(["Recent Form", f"Last {len(recent)} matches: {recent_goals}G, {recent_assists}A"])
        
        if highlights:
            highlights_table = Table(highlights, colWidths=[2*inch, 6*inch])
            highlights_style = TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (0, 0), 9.5),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            highlights_table.setStyle(highlights_style)
            elements.append(highlights_table)
        
        return elements

    def _calculate_category_stats(self, matches: List[Match]) -> Dict[str, int]:
        """Calculate statistics for a category of matches"""
        stats = {
            'matches': len(matches),
            'goals': 0,
            'assists': 0,
            'minutes': 0
        }
        
        for match in matches:
            stats['goals'] += match.brodie_goals
            stats['assists'] += match.brodie_assists
            stats['minutes'] += match.minutes_played
        
        return stats
    
    def _calculate_advanced_stats(self, matches: List[Match]) -> Dict[str, Any]:
        """Calculate advanced performance statistics"""
        stats = {
            'matches': len(matches),
            'goals': 0,
            'assists': 0,
            'minutes': 0,
            'goals_per_60': 0.0,
            'assists_per_60': 0.0,
            'contribution_per_60': 0.0
        }
        
        for match in matches:
            stats['goals'] += match.brodie_goals
            stats['assists'] += match.brodie_assists
            stats['minutes'] += match.minutes_played
        
        # Calculate per-60 metrics (actual match length is 60 minutes: 3 x 20 min periods)
        if stats['minutes'] > 0:
            stats['goals_per_60'] = round((stats['goals'] / stats['minutes']) * 60, 2)
            stats['assists_per_60'] = round((stats['assists'] / stats['minutes']) * 60, 2)
            stats['contribution_per_60'] = round(((stats['goals'] + stats['assists']) / stats['minutes']) * 60, 2)
        
        return stats
    
    def _create_cover_page(self, matches: List[Match]) -> List:
        """Create professional cover page for season tracker"""
        elements = []
        
        # Calculate some stats for the cover
        completed_matches = [m for m in matches if not m.is_fixture]
        total_stats = self._calculate_category_stats(completed_matches) if completed_matches else {'matches': 0, 'goals': 0, 'assists': 0}
        
        # Main title
        title = Paragraph(
            f"{self.settings.player_name}<br/>Season Tracker",
            ParagraphStyle(
                name='CoverTitle',
                parent=self.styles['Title'],
                fontSize=28,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=self.primary_color,
                fontName='Helvetica-Bold',
                leading=34
            )
        )
        elements.append(title)
        elements.append(Spacer(1, 30))
        
        # Season and club info
        club_info = Paragraph(
            f"<b>{self.settings.club_name}</b><br/>"
            f"Season {self.settings.season_year}",
            ParagraphStyle(
                name='CoverClubInfo',
                parent=self.styles['Normal'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=40,
                leading=24,
                textColor=self.header_color
            )
        )
        elements.append(club_info)
        elements.append(Spacer(1, 50))
        
        # Key statistics on cover
        if completed_matches:
            stats_text = f"<b>{total_stats['matches']}</b> Matches | "
            stats_text += f"<b>{total_stats['goals']}</b> Goals | "
            stats_text += f"<b>{total_stats['assists']}</b> Assists | "
            stats_text += f"<b>{total_stats['goals'] + total_stats['assists']}</b> Goal Contributions"
            
            stats_para = Paragraph(
                stats_text,
                ParagraphStyle(
                    name='CoverStats',
                    parent=self.styles['Normal'],
                    fontSize=14,
                    alignment=TA_CENTER,
                    spaceAfter=60,
                    leading=20,
                    textColor=self.dark_grey
                )
            )
            elements.append(stats_para)
        
        elements.append(Spacer(1, 80))
        
        # Generated date
        gen_date = datetime.now().strftime("%d %B %Y")
        date_text = Paragraph(
            f"Report Generated: {gen_date}",
            ParagraphStyle(
                name='CoverDate',
                parent=self.styles['Normal'],
                fontSize=11,
                alignment=TA_CENTER,
                textColor=self.dark_grey,
                fontName='Helvetica'
            )
        )
        elements.append(date_text)
        
        return elements


def generate_season_pdf(matches: List[Match], settings: AppSettings, output_dir: str = "output", physical_measurements: List[PhysicalMeasurement] = None, physical_metrics: List[PhysicalMetrics] = None, period: str = 'all_time') -> str:
    """Generate a season PDF report
    
    Args:
        matches: List of all matches
        settings: App settings
        output_dir: Output directory
        physical_measurements: List of physical measurements
        physical_metrics: List of physical metrics
        period: Time period filter ('all_time', 'season', '12_months', '6_months', '3_months', 'last_month')
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    from .utils import generate_pdf_filename
    filename = generate_pdf_filename(settings)
    output_path = os.path.join(output_dir, filename)
    
    # Generate PDF
    generator = PDFGenerator(settings)
    return generator.generate_pdf(matches, output_path, physical_measurements or [], physical_metrics or [], period=period)


def generate_scout_pdf(
    matches: List[Match], 
    settings: AppSettings, 
    achievements: List[Achievement],
    club_history: List[ClubHistory],
    physical_measurements: List[PhysicalMeasurement] = None,
    training_camps: List[TrainingCamp] = None,
    physical_metrics: List[PhysicalMetrics] = None,
    references: List[Reference] = None,
    output_dir: str = "output",
    period: str = 'all_time'
) -> str:
    """Generate a professional scout-friendly PDF report
    
    Args:
        matches: List of all matches
        settings: App settings
        achievements: List of achievements
        club_history: List of club history entries
        physical_measurements: List of physical measurements
        training_camps: List of training camps
        physical_metrics: List of physical metrics
        output_dir: Output directory
        period: Time period filter ('all_time', 'season', '12_months', '6_months', '3_months', 'last_month')
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    from .utils import generate_pdf_filename
    base_filename = generate_pdf_filename(settings)
    filename = base_filename.replace('.pdf', '_Scout_Report.pdf')
    output_path = os.path.join(output_dir, filename)
    
    # Generate PDF
    generator = ScoutPDFGenerator(settings)
    return generator.generate_pdf(matches, output_path, achievements, club_history, physical_measurements or [], training_camps or [], physical_metrics or [], references or [], period=period)


class ScoutPDFGenerator(PDFGenerator):
    """Specialized PDF generator for scout/coach reports"""
    
    def generate_pdf(
        self, 
        matches: List[Match], 
        output_path: str, 
        achievements: List[Achievement],
        club_history: List[ClubHistory],
        physical_measurements: List[PhysicalMeasurement] = None,
        training_camps: List[TrainingCamp] = None,
        physical_metrics: List[PhysicalMetrics] = None,
        references: List[Reference] = None,
        period: str = 'all_time'
    ) -> str:
        """Generate the complete scout-friendly PDF report
        
        Args:
            matches: List of all matches
            output_path: Path to save the PDF
            achievements: List of achievements
            club_history: List of club history entries
            physical_measurements: List of physical measurements
            training_camps: List of training camps
            physical_metrics: List of physical metrics
            period: Time period filter ('all_time', 'season', '12_months', '6_months', '3_months', 'last_month')
        """
        # Filter matches by period if specified
        if period and period != 'all_time':
            matches = filter_matches_by_period(matches, period, self.settings.season_year)
        
        self.period = period  # Store period for use in sections
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,  # Portrait for scout reports
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        story = []
        
        # PAGE 1: Cover page
        title_page_elements = self._create_title_page()
        story.extend(title_page_elements)
        
        # PAGE 2: Player profile details, photo, media, and references
        page2_elements = []
        
        # Add comprehensive player profile (always include this - it always returns content)
        profile_elements = self._create_scout_player_profile(physical_measurements or [], physical_metrics)
        page2_elements.extend(profile_elements)
        page2_elements.append(Spacer(1, 12))
        
        # Add player photo, media, and references
        media_elements = self._create_player_media_section(references or [])
        if media_elements:
            page2_elements.extend(media_elements)
        
        # Always add page 2 (player profile is always included)
        story.append(PageBreak())
        story.append(KeepTogether(page2_elements))
        
        # PAGE 3: Club history and training camps
        club_history_elements = []
        training_camps_elements = []
        
        if club_history:
            club_history_elements = self._create_club_history_section(club_history)
        if training_camps:
            training_camps_elements = self._create_training_camps_section(training_camps)
        
        # Combine both sections and keep them together on same page
        if club_history_elements or training_camps_elements:
            story.append(PageBreak())
            combined_elements = []
            if club_history_elements:
                combined_elements.extend(club_history_elements)
                combined_elements.append(Spacer(1, 12))
            if training_camps_elements:
                combined_elements.extend(training_camps_elements)
            # Use KeepTogether to ensure both sections stay on same page
            story.append(KeepTogether(combined_elements))
        
        # PAGE 4: Playing Profile, Key achievements, physical development, physical performance metrics
        page4_elements = []
        
        # Add playing profile section
        if self.settings.playing_profile and len(self.settings.playing_profile) > 0:
            page4_elements.extend(self._create_playing_profile_section())
            page4_elements.append(Spacer(1, 12))
        
        # Add achievements
        if achievements:
            page4_elements.extend(self._create_achievements_section(achievements))
            page4_elements.append(Spacer(1, 12))
        
        # Add physical development
        if physical_measurements:
            page4_elements.extend(self._create_physical_development_section(physical_measurements))
            page4_elements.append(Spacer(1, 12))
        
        # Add physical performance metrics
        if physical_metrics:
            page4_elements.extend(self._create_physical_metrics_section(physical_metrics))
        
        # Keep all page 4 content together
        if page4_elements:
            story.append(PageBreak())
            story.append(KeepTogether(page4_elements))
        
        # PAGE 5: Performance summary and key statistics (always include if there are matches)
        page5_elements = []
        
        # Add performance summary
        performance_summary_elements = self._create_performance_summary(matches)
        if performance_summary_elements:
            page5_elements.extend(performance_summary_elements)
            page5_elements.append(Spacer(1, 12))
        
        # Add key statistics
        key_stats_elements = self._create_key_statistics(matches)
        if key_stats_elements:
            page5_elements.extend(key_stats_elements)
        
        # Keep all page 5 content together
        if page5_elements:
            story.append(PageBreak())
            story.append(KeepTogether(page5_elements))
        
        # Add footer
        story.append(self._create_footer(matches))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    def _create_title_page(self) -> List:
        """Create professional title page"""
        elements = []
        
        # Title
        player_name = self.settings.player_name or "Player"
        title = Paragraph(
            f"{player_name}<br/>Player Profile & Performance Report",
            ParagraphStyle(
                name='TitlePage',
                parent=self.styles['Title'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=self.primary_color,
                fontName='Helvetica-Bold',
                leading=30
            )
        )
        elements.append(title)
        elements.append(Spacer(1, 40))
        
        # Current club and season - handle empty values
        club_name = self.settings.club_name or "N/A"
        season_year = self.settings.season_year or "N/A"
        
        club_info = Paragraph(
            f"<b>Current Club:</b> {club_name}<br/>"
            f"<b>Season:</b> {season_year}",
            ParagraphStyle(
                name='ClubInfo',
                parent=self.styles['Normal'],
                fontSize=14,
                alignment=TA_CENTER,
                spaceAfter=20,
                leading=20
            )
        )
        elements.append(club_info)
        elements.append(Spacer(1, 60))
        
        # Generated date
        gen_date = datetime.now().strftime("%d %B %Y")
        date_text = Paragraph(
            f"Report Generated: {gen_date}",
            ParagraphStyle(
                name='GenDate',
                parent=self.styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=self.dark_grey
            )
        )
        elements.append(date_text)
        
        return elements
    
    def _create_scout_player_profile(self, physical_measurements: List[PhysicalMeasurement], physical_metrics: List[PhysicalMetrics] = None) -> List:
        """Create comprehensive player profile for scouts"""
        elements = []
        
        elements.append(Paragraph("Player Profile", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        # Create profile table
        profile_data = []
        
        # Basic Information - always include name and club
        profile_data.append(["Name", self.settings.player_name or "N/A"])
        if self.settings.date_of_birth:
            profile_data.append(["Date of Birth", self.settings.date_of_birth])
        if self.settings.position:
            profile_data.append(["Position", self.settings.position])
        if self.settings.dominant_foot:
            profile_data.append(["Dominant Foot", self.settings.dominant_foot])
        profile_data.append(["Current Club", self.settings.club_name or "N/A"])
        
        # Physical Attributes
        if self.settings.height_cm:
            profile_data.append(["Height", f"{self.settings.height_cm:.1f} cm"])
        if self.settings.weight_kg:
            profile_data.append(["Weight", f"{self.settings.weight_kg:.1f} kg"])
        if self.settings.height_cm and self.settings.weight_kg:
            bmi = self.settings.weight_kg / ((self.settings.height_cm / 100) ** 2)
            profile_data.append(["BMI", f"{bmi:.1f}"])
        
        # Performance Metrics - use latest physical metric if available, otherwise fall back to settings
        latest_metric = None
        if physical_metrics:
            sorted_metrics = sorted(physical_metrics, key=lambda x: datetime.strptime(x.date, "%d %b %Y"), reverse=True)
            latest_metric = sorted_metrics[0] if sorted_metrics else None
        
        if latest_metric:
            if latest_metric.sprint_speed_ms:
                profile_data.append(["Sprint Speed", f"{latest_metric.sprint_speed_ms:.2f} m/s"])
            elif latest_metric.sprint_speed_kmh:
                profile_data.append(["Sprint Speed", f"{latest_metric.sprint_speed_kmh:.1f} km/h"])
            if latest_metric.vertical_jump_cm:
                profile_data.append(["Vertical Jump", f"{latest_metric.vertical_jump_cm:.1f} cm"])
            if latest_metric.agility_time_sec:
                profile_data.append(["Agility Time", f"{latest_metric.agility_time_sec:.2f} sec"])
        else:
            # Fallback to settings for backward compatibility
            if self.settings.sprint_speed_ms:
                profile_data.append(["Sprint Speed", f"{self.settings.sprint_speed_ms:.2f} m/s"])
            elif self.settings.sprint_speed_kmh:
                profile_data.append(["Sprint Speed", f"{self.settings.sprint_speed_kmh:.1f} km/h"])
            if self.settings.vertical_jump_cm:
                profile_data.append(["Vertical Jump", f"{self.settings.vertical_jump_cm:.1f} cm"])
            if self.settings.agility_time_sec:
                profile_data.append(["Agility Time", f"{self.settings.agility_time_sec:.2f} sec"])
        
        # PHV Information with status explanation
        if self.settings.phv_date and self.settings.phv_age:
            # Determine PHV status
            try:
                phv_date_obj = datetime.strptime(self.settings.phv_date, "%d %b %Y")
                current_date = datetime.now()
                days_diff = (current_date - phv_date_obj).days
                
                if days_diff < 0:
                    status_text = "Currently pre-PHV, indicating early stage of growth spurt."
                elif days_diff < 180:
                    status_text = "Currently at PHV, indicating peak growth velocity period."
                else:
                    status_text = "Currently post-PHV, indicating advanced physical development relative to chronological age."
                
                # Use <br/> for ReportLab paragraph formatting
                phv_value = f"Age {self.settings.phv_age:.1f} years ({self.settings.phv_date})<br/>{status_text}"
            except:
                phv_value = f"Age {self.settings.phv_age:.1f} years ({self.settings.phv_date})"
            
            profile_data.append(["Peak Height Velocity", phv_value])
        
        # Always create table (profile_data should always have at least name and club)
        # But add a safety check
        if not profile_data:
            profile_data.append(["Name", self.settings.player_name or "N/A"])
            profile_data.append(["Current Club", self.settings.club_name or "N/A"])
        
        data = [['Attribute', 'Value']] + profile_data
        
        # Convert to Paragraph objects for proper text wrapping
        wrapped_profile_data = []
        for row_idx, row in enumerate(data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:  # Header row
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    # Both columns can wrap, left column is label, right is value
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
            wrapped_profile_data.append(wrapped_row)
        
        profile_table = Table(wrapped_profile_data, colWidths=[2.5*inch, 4.5*inch])
        profile_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])
        profile_table.setStyle(profile_style)
        elements.append(profile_table)
        
        return elements
    
    def _create_player_media_section(self, references: List[Reference] = None) -> List:
        """Create player photo and links section"""
        elements = []
        
        # Check if there's any media to display
        has_photo = self.settings.player_photo_path and os.path.exists(self.settings.player_photo_path)
        has_highlight_reels = self.settings.highlight_reel_urls and len(self.settings.highlight_reel_urls) > 0
        has_contact_email = self.settings.contact_email and self.settings.contact_email.strip()
        
        # Always show section if there's a photo or contact email (even if no social media)
        if not (has_photo or has_highlight_reels or has_contact_email):
            return elements  # No media to display
        
        elements.append(Paragraph("Player Media & Links", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        # Add player photo if available (centered)
        if has_photo:
            try:
                # Handle both absolute and relative paths
                photo_path = self.settings.player_photo_path
                if not os.path.isabs(photo_path):
                    # Try relative to current working directory first
                    if not os.path.exists(photo_path):
                        # Try relative to app directory
                        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        photo_path = os.path.join(app_dir, photo_path)
                
                # Load and resize image (max 2.5 inches width, maintain aspect ratio)
                img = Image(photo_path, width=2.5*inch, height=3*inch, kind='proportional')
                # Center the image
                img_table = Table([[img]], colWidths=[7.5*inch])
                img_style = TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ])
                img_table.setStyle(img_style)
                elements.append(img_table)
                elements.append(Spacer(1, 12))
            except Exception as e:
                # If image loading fails, add a placeholder text
                elements.append(Paragraph(f"<i>Photo unavailable</i>", self.styles['TableCell']))
                elements.append(Spacer(1, 12))
        
        # Add contact email (below photo)
        if has_contact_email:
            elements.append(Paragraph("<b>Contact Email:</b>", self.styles['TableCell']))
            elements.append(Spacer(1, 4))
            email_para = Paragraph(
                f'<a href="mailto:{self.settings.contact_email}" color="blue"><u>{self.settings.contact_email}</u></a>',
                self.styles['TableCell']
            )
            elements.append(email_para)
            elements.append(Spacer(1, 8))
        
        # Add social media section (below photo) - renamed from Highlight Reels
        if has_highlight_reels:
            elements.append(Paragraph("<b>Social Media:</b>", self.styles['TableCell']))
            elements.append(Spacer(1, 4))
            for url in self.settings.highlight_reel_urls:
                # Create clickable link using ReportLab's <a> tag with full URL displayed
                link_para = Paragraph(
                    f'<a href="{url}" color="blue"><u>{url}</u></a>',
                    self.styles['TableCell']
                )
                elements.append(link_para)
            elements.append(Spacer(1, 8))
        
        # Add references section (below social media links)
        if references and len(references) > 0:
            elements.append(Paragraph("<b>References:</b>", self.styles['TableCell']))
            elements.append(Spacer(1, 4))
            
            for ref in references:
                ref_text = f"<b>{ref.name}</b>"
                if ref.position:
                    ref_text += f" - {ref.position}"
                if ref.organization:
                    ref_text += f" ({ref.organization})"
                elements.append(Paragraph(ref_text, self.styles['TableCell']))
                
                # Add contact info if available
                contact_parts = []
                if ref.email:
                    contact_parts.append(f'<a href="mailto:{ref.email}" color="blue"><u>{ref.email}</u></a>')
                if ref.phone:
                    contact_parts.append(ref.phone)
                if contact_parts:
                    elements.append(Paragraph(" | ".join(contact_parts), self.styles['TableCell']))
                
                if ref.relationship:
                    elements.append(Paragraph(f"<i>{ref.relationship}</i>", self.styles['TableCell']))
                
                elements.append(Spacer(1, 6))
        
        return elements
    
    def _create_club_history_section(self, club_history: List[ClubHistory]) -> List:
        """Create club history section"""
        elements = []
        
        # Sort by season (most recent first)
        sorted_history = sorted(club_history, key=lambda x: x.season, reverse=True)
        
        history_data = [['Club', 'Season', 'Age Group', 'Position', 'Achievements']]
        for entry in sorted_history:
            history_data.append([
                entry.club_name,
                entry.season,
                entry.age_group or '-',
                entry.position or '-',
                entry.achievements or '-'
            ])
        
        # Convert to Paragraph objects for proper text wrapping
        wrapped_history_data = []
        for row_idx, row in enumerate(history_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:  # Header row
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    # All columns can wrap, but center align season and age group
                    if col_idx in [1, 2]:  # Season, Age Group - center align
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
                    else:  # Club, Position, Achievements - left align with wrapping
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
            wrapped_history_data.append(wrapped_row)
        
        # Calculate better column widths for A4 portrait
        history_table = Table(wrapped_history_data, colWidths=[1.8*inch, 1.2*inch, 0.9*inch, 1*inch, 2.1*inch])
        history_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Club
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Season
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Age Group
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),  # Position
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),  # Achievements
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        history_table.setStyle(history_style)
        
        # Use KeepTogether to ensure header, spacer, and table stay together on same page
        header_para = Paragraph("Club History", self.styles['SectionHeader'])
        spacer = Spacer(1, 12)
        elements.append(KeepTogether([header_para, spacer, history_table]))
        
        return elements
    
    def _create_playing_profile_section(self) -> List:
        """Create Playing Profile section with bullet points"""
        elements = []
        
        if not self.settings.playing_profile or len(self.settings.playing_profile) == 0:
            return elements
        
        elements.append(Paragraph("Playing Profile", self.styles['SectionHeader']))
        elements.append(Spacer(1, 8))
        
        # Create bullet list
        for item in self.settings.playing_profile:
            if item and item.strip():
                bullet_para = Paragraph(
                    f"• {item.strip()}",
                    ParagraphStyle(
                        name='PlayingProfileBullet',
                        parent=self.styles['Normal'],
                        fontSize=10,
                        leftIndent=12,
                        spaceAfter=6,
                        fontName='Helvetica',
                        leading=14
                    )
                )
                elements.append(bullet_para)
        
        return elements
    
    def _create_achievements_section(self, achievements: List[Achievement]) -> List:
        """Create achievements section"""
        elements = []
        
        # Sort by date (most recent first)
        sorted_achievements = sorted(
            achievements, 
            key=lambda x: datetime.strptime(x.date, "%d %b %Y"), 
            reverse=True
        )
        
        achievements_data = [['Date', 'Achievement', 'Category', 'Season']]
        for achievement in sorted_achievements:
            achievements_data.append([
                achievement.date,
                achievement.title,
                achievement.category,
                achievement.season or '-'
            ])
        
        # Convert to Paragraph objects for proper text wrapping
        wrapped_achievements_data = []
        for row_idx, row in enumerate(achievements_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:  # Header row
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    # Achievement title column needs wrapping, others can be centered
                    if col_idx == 1:  # Achievement title - left align with wrapping
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                    else:  # Date, Category, Season - center align
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
            wrapped_achievements_data.append(wrapped_row)
        
        achievements_table = Table(wrapped_achievements_data, colWidths=[1.2*inch, 3*inch, 1.2*inch, 1.6*inch])
        achievements_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Date
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Achievement
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Category
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Season
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        achievements_table.setStyle(achievements_style)
        
        # Use KeepTogether to ensure header, spacer, and table stay together on same page
        header_para = Paragraph("Key Achievements", self.styles['SectionHeader'])
        spacer = Spacer(1, 12)
        elements.append(KeepTogether([header_para, spacer, achievements_table]))
        
        return elements
    
    def _create_training_camps_section(self, training_camps: List[TrainingCamp]) -> List:
        """Create training camps section"""
        elements = []
        
        # Sort by start date (most recent first)
        sorted_camps = sorted(
            training_camps, 
            key=lambda x: datetime.strptime(x.start_date, "%d %b %Y"), 
            reverse=True
        )
        
        camps_data = [['Camp Name', 'Organizer', 'Location', 'Date', 'Age Group', 'Focus Area']]
        for camp in sorted_camps:
            date_str = camp.start_date
            if camp.end_date:
                date_str += f" - {camp.end_date}"
            if camp.duration_days:
                date_str += f" ({camp.duration_days} days)"
            
            camps_data.append([
                camp.camp_name,
                camp.organizer,
                camp.location,
                date_str,
                camp.age_group or '-',
                camp.focus_area or '-'
            ])
        
        # Convert to Paragraph objects for proper text wrapping
        wrapped_camps_data = []
        for row_idx, row in enumerate(camps_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:  # Header row
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    # Date column can be long, others can wrap
                    if col_idx in [1, 2, 3]:  # Organizer, Location, Date - left align with wrapping
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                    else:  # Camp Name, Age Group, Focus Area - left align
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
            wrapped_camps_data.append(wrapped_row)
        
        camps_table = Table(wrapped_camps_data, colWidths=[1.5*inch, 1.5*inch, 1.2*inch, 1.5*inch, 0.8*inch, 1.5*inch])
        camps_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        camps_table.setStyle(camps_style)
        
        # Use KeepTogether to ensure header, spacer, and table stay together on same page
        header_para = Paragraph("Training Camps Attended", self.styles['SectionHeader'])
        spacer = Spacer(1, 12)
        elements.append(KeepTogether([header_para, spacer, camps_table]))
        
        return elements
    
    def _create_physical_metrics_section(self, physical_metrics: List[PhysicalMetrics]) -> List:
        """Create physical performance metrics section grouped by category"""
        elements = []
        
        if not physical_metrics:
            return elements
        
        # Filter to only include metrics marked for report
        # All metrics are kept for calculations, but only selected ones appear in PDF
        report_metrics = [
            m for m in physical_metrics 
            if (m.include_in_report if hasattr(m, 'include_in_report') else True)
        ]
        
        if not report_metrics:
            return elements
        
        # Sort by date (most recent first) and use latest metric
        sorted_metrics = sorted(
            report_metrics, 
            key=lambda x: datetime.strptime(x.date, "%d %b %Y"), 
            reverse=True
        )
        
        latest_metric = sorted_metrics[0]
        
        elements.append(Paragraph("Physical Performance Metrics", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        # Speed Category
        speed_items = []
        if latest_metric.sprint_10m_sec:
            speed_items.append(["10m", f"{latest_metric.sprint_10m_sec:.2f} s"])
        if latest_metric.sprint_20m_sec:
            speed_items.append(["20m", f"{latest_metric.sprint_20m_sec:.2f} s"])
        if latest_metric.sprint_30m_sec:
            speed_items.append(["30m", f"{latest_metric.sprint_30m_sec:.2f} s"])
        if latest_metric.sprint_speed_ms:
            speed_items.append(["Max Sprint Speed", f"{latest_metric.sprint_speed_ms:.2f} m/s"])
        elif latest_metric.sprint_speed_kmh:
            speed_items.append(["Max Sprint Speed", f"{latest_metric.sprint_speed_kmh:.1f} km/h"])
        
        if speed_items:
            # Speed header
            speed_header = Paragraph(
                "Speed",
                ParagraphStyle(
                    name='CategoryHeader',
                    parent=self.styles['Normal'],
                    fontSize=11,
                    fontName='Helvetica-Bold',
                    textColor=self.header_color,
                    spaceAfter=6
                )
            )
            elements.append(speed_header)
            
            # Speed items table
            speed_data = [['Metric', 'Value']] + speed_items
            wrapped_speed_data = []
            for row_idx, row in enumerate(speed_data):
                wrapped_row = []
                for col_idx, cell in enumerate(row):
                    if row_idx == 0:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                    else:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                wrapped_speed_data.append(wrapped_row)
            
            speed_table = Table(wrapped_speed_data, colWidths=[3*inch, 4*inch])
            speed_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            speed_table.setStyle(speed_style)
            elements.append(speed_table)
            elements.append(Spacer(1, 12))
        
        # Power Category
        power_items = []
        if latest_metric.vertical_jump_cm:
            power_items.append(["Vertical Jump", f"{latest_metric.vertical_jump_cm:.1f} cm"])
        elif latest_metric.countermovement_jump_cm:
            power_items.append(["Countermovement Jump", f"{latest_metric.countermovement_jump_cm:.1f} cm"])
        if latest_metric.standing_long_jump_cm:
            power_items.append(["Standing Long Jump", f"{latest_metric.standing_long_jump_cm:.1f} cm"])
        
        if power_items:
            # Power header
            power_header = Paragraph(
                "Power",
                ParagraphStyle(
                    name='CategoryHeader',
                    parent=self.styles['Normal'],
                    fontSize=11,
                    fontName='Helvetica-Bold',
                    textColor=self.header_color,
                    spaceAfter=6
                )
            )
            elements.append(power_header)
            
            # Power items table
            power_data = [['Metric', 'Value']] + power_items
            wrapped_power_data = []
            for row_idx, row in enumerate(power_data):
                wrapped_row = []
                for col_idx, cell in enumerate(row):
                    if row_idx == 0:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                    else:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                wrapped_power_data.append(wrapped_row)
            
            power_table = Table(wrapped_power_data, colWidths=[3*inch, 4*inch])
            power_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            power_table.setStyle(power_style)
            elements.append(power_table)
            elements.append(Spacer(1, 12))
        
        # Endurance Category
        endurance_items = []
        if latest_metric.beep_test_level:
            endurance_items.append(["Beep Test", f"Level {latest_metric.beep_test_level:.1f}"])
        
        if endurance_items:
            # Endurance header
            endurance_header = Paragraph(
                "Endurance",
                ParagraphStyle(
                    name='CategoryHeader',
                    parent=self.styles['Normal'],
                    fontSize=11,
                    fontName='Helvetica-Bold',
                    textColor=self.header_color,
                    spaceAfter=6
                )
            )
            elements.append(endurance_header)
            
            # Endurance items table
            endurance_data = [['Metric', 'Value']] + endurance_items
            wrapped_endurance_data = []
            for row_idx, row in enumerate(endurance_data):
                wrapped_row = []
                for col_idx, cell in enumerate(row):
                    if row_idx == 0:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                    else:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                wrapped_endurance_data.append(wrapped_row)
            
            endurance_table = Table(wrapped_endurance_data, colWidths=[3*inch, 4*inch])
            endurance_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            endurance_table.setStyle(endurance_style)
            elements.append(endurance_table)
        
        return elements
    
    def _create_physical_development_section(self, physical_measurements: List[PhysicalMeasurement]) -> List:
        """Create physical development timeline"""
        elements = []
        
        elements.append(Paragraph("Physical Development", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        # Filter to only include measurements marked for report
        # All measurements are kept for PHV calculation, but only selected ones appear in PDF
        report_measurements = [
            m for m in physical_measurements 
            if m.height_cm is not None and (m.include_in_report if hasattr(m, 'include_in_report') else True)
        ]
        
        # Sort by date
        sorted_measurements = sorted(
            report_measurements,
            key=lambda m: datetime.strptime(m.date, "%d %b %Y")
        )
        
        if sorted_measurements:
            dev_data = [['Date', 'Height (cm)', 'Weight (kg)', 'Notes']]
            for m in sorted_measurements:
                dev_data.append([
                    m.date,
                    f"{m.height_cm:.1f}" if m.height_cm else '-',
                    f"{m.weight_kg:.1f}" if m.weight_kg else '-',
                    m.notes or '-'
                ])
            
            # Convert to Paragraph objects for proper text wrapping
            wrapped_dev_data = []
            for row_idx, row in enumerate(dev_data):
                wrapped_row = []
                for col_idx, cell in enumerate(row):
                    if row_idx == 0:  # Header row
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                    else:
                        # Notes column needs wrapping, others can be centered
                        if col_idx == 3:  # Notes - left align with wrapping
                            wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                        else:  # Date, Height, Weight - center align
                            wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
                wrapped_dev_data.append(wrapped_row)
            
            dev_table = Table(wrapped_dev_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 3.1*inch])
            dev_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (2, -1), 'CENTER'),  # Date, Height, Weight - center
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),  # Notes - left
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            dev_table.setStyle(dev_style)
            elements.append(dev_table)
        
        return elements
    
    def _create_performance_summary(self, matches: List[Match]) -> List:
        """Create performance summary section"""
        elements = []
        
        completed_matches = [m for m in matches if not m.is_fixture]
        if not completed_matches:
            elements.append(Paragraph("No match data available.", self.styles['TableCell']))
            return elements
        
        # Add period label if not all_time
        if self.period != 'all_time':
            period_label = Paragraph(
                f"<i>Statistics for: {self._get_period_label()}</i>",
                ParagraphStyle(
                    name='PeriodLabel',
                    parent=self.styles['Normal'],
                    fontSize=9,
                    textColor=self.dark_grey,
                    alignment=TA_LEFT,
                    spaceAfter=6
                )
            )
            elements.append(period_label)
        
        # Calculate overall stats
        total_stats = self._calculate_category_stats(completed_matches)
        
        # Create summary table with proper header
        summary_data = [
            ['Metric', 'Value'],  # Header row
            ['Total Matches', str(total_stats['matches'])],
            ['Total Goals', str(total_stats['goals'])],
            ['Total Assists', str(total_stats['assists'])],
            ['Goal Contributions', str(total_stats['goals'] + total_stats['assists'])],
            ['Total Minutes', str(total_stats['minutes'])],
            ['Goals per Match', f"{(total_stats['goals'] / total_stats['matches']):.2f}" if total_stats['matches'] > 0 else "0.00"],
            ['Assists per Match', f"{(total_stats['assists'] / total_stats['matches']):.2f}" if total_stats['matches'] > 0 else "0.00"],
        ]
        
        # Convert to Paragraph objects for proper text wrapping
        wrapped_summary_data = []
        for row_idx, row in enumerate(summary_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:  # Header row
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    # Left column - left align, right column - right align
                    if col_idx == 0:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                    else:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
            wrapped_summary_data.append(wrapped_row)
        
        summary_table = Table(wrapped_summary_data, colWidths=[3.5*inch, 3.5*inch], repeatRows=1)
        summary_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])
        summary_table.setStyle(summary_style)
        
        # Use KeepTogether to ensure header, spacer, and table stay together on same page
        header_para = Paragraph("Performance Summary", self.styles['SectionHeader'])
        spacer = Spacer(1, 12)
        elements = [KeepTogether([header_para, spacer, summary_table])]
        
        return elements
    
    def _create_key_statistics(self, matches: List[Match]) -> List:
        """Create key performance statistics"""
        elements = []
        
        elements.append(Paragraph("Key Performance Metrics", self.styles['SectionHeader']))
        
        # Add period label if not all_time
        if self.period != 'all_time':
            period_label = Paragraph(
                f"<i>Statistics for: {self._get_period_label()}</i>",
                ParagraphStyle(
                    name='PeriodLabel',
                    parent=self.styles['Normal'],
                    fontSize=9,
                    textColor=self.dark_grey,
                    alignment=TA_LEFT,
                    spaceAfter=6
                )
            )
            elements.append(period_label)
        
        elements.append(Spacer(1, 12))
        
        completed_matches = [m for m in matches if not m.is_fixture]
        if not completed_matches:
            return elements
        
        # Calculate advanced stats
        advanced_stats = self._calculate_advanced_stats(completed_matches)
        
        # Get performance metric comments from settings
        metric_comments = self.settings.performance_metric_comments or {}
        
        # Build metrics data with comments
        goals_60_value = f"{advanced_stats['goals_per_60']:.2f}"
        goals_60_comment = metric_comments.get('goals_per_60', '')
        if goals_60_comment:
            goals_60_value += f" ({goals_60_comment})"
        
        assists_60_value = f"{advanced_stats['assists_per_60']:.2f}"
        assists_60_comment = metric_comments.get('assists_per_60', '')
        if assists_60_comment:
            assists_60_value += f" ({assists_60_comment})"
        
        contribution_60_value = f"{advanced_stats['contribution_per_60']:.2f}"
        contribution_60_comment = metric_comments.get('contribution_per_60', '')
        if contribution_60_comment:
            contribution_60_value += f" ({contribution_60_comment})"
        
        metrics_data = [
            ['Metric', 'Value'],
            ['Goals per 60 minutes', goals_60_value],
            ['Assists per 60 minutes', assists_60_value],
            ['Goal Contributions per 60', contribution_60_value],
        ]
        
        if advanced_stats['matches'] > 0:
            g_a_per_match = (advanced_stats['goals'] + advanced_stats['assists']) / advanced_stats['matches']
            g_a_per_match_value = f"{g_a_per_match:.2f}"
            g_a_comment = metric_comments.get('g_a_per_match', '')
            if g_a_comment:
                g_a_per_match_value += f" ({g_a_comment})"
            metrics_data.append(['Goal Contributions per Match', g_a_per_match_value])
        
        if advanced_stats['goals'] + advanced_stats['assists'] > 0:
            min_per_ga = advanced_stats['minutes'] / (advanced_stats['goals'] + advanced_stats['assists'])
            min_per_ga_value = f"{min_per_ga:.0f}"
            min_per_ga_comment = metric_comments.get('min_per_ga', '')
            if min_per_ga_comment:
                min_per_ga_value += f" ({min_per_ga_comment})"
            metrics_data.append(['Minutes per Goal Contribution', min_per_ga_value])
        
        # Convert to Paragraph objects for proper text wrapping
        wrapped_metrics_data = []
        for row_idx, row in enumerate(metrics_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:  # Header row
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    # Left column - left align, right column - right align
                    if col_idx == 0:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                    else:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
            wrapped_metrics_data.append(wrapped_row)
        
        metrics_table = Table(wrapped_metrics_data, colWidths=[3.5*inch, 3.5*inch])
        metrics_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])
        metrics_table.setStyle(metrics_style)
        elements.append(metrics_table)
        
        return elements


def generate_player_resume_pdf(
    matches: List[Match], 
    settings: AppSettings, 
    achievements: List[Achievement],
    club_history: List[ClubHistory],
    physical_measurements: List[PhysicalMeasurement] = None,
    training_camps: List[TrainingCamp] = None,
    physical_metrics: List[PhysicalMetrics] = None,
    references: List[Reference] = None,
    output_dir: str = "output",
    period: str = 'season'
) -> str:
    """Generate a comprehensive Player Resume PDF report
    
    Args:
        matches: List of all matches
        settings: App settings
        achievements: List of achievements
        club_history: List of club history entries
        physical_measurements: List of physical measurements
        training_camps: List of training camps
        physical_metrics: List of physical metrics
        references: List of references
        output_dir: Output directory
        period: Time period filter ('all_time', 'season', '12_months', '6_months', '3_months', 'last_month')
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    from .utils import generate_pdf_filename
    base_filename = generate_pdf_filename(settings)
    filename = base_filename.replace('.pdf', '_Player_Resume.pdf')
    output_path = os.path.join(output_dir, filename)
    
    # Generate PDF
    generator = PlayerResumePDFGenerator(settings)
    return generator.generate_pdf(matches, output_path, achievements, club_history, physical_measurements or [], training_camps or [], physical_metrics or [], references or [], period=period)


class PlayerResumePDFGenerator(PDFGenerator):
    """Specialized PDF generator for comprehensive Player Resume reports"""
    
    def generate_pdf(
        self, 
        matches: List[Match], 
        output_path: str, 
        achievements: List[Achievement],
        club_history: List[ClubHistory],
        physical_measurements: List[PhysicalMeasurement] = None,
        training_camps: List[TrainingCamp] = None,
        physical_metrics: List[PhysicalMetrics] = None,
        references: List[Reference] = None,
        period: str = 'season'
    ) -> str:
        """Generate the complete Player Resume PDF report
        
        Args:
            matches: List of all matches
            output_path: Path to save the PDF
            achievements: List of achievements
            club_history: List of club history entries
            physical_measurements: List of physical measurements
            training_camps: List of training camps
            physical_metrics: List of physical metrics
            references: List of references
            period: Time period filter ('all_time', 'season', '12_months', '6_months', '3_months', 'last_month')
        """
        # Filter matches by period if specified
        if period and period != 'all_time':
            matches = filter_matches_by_period(matches, period, self.settings.season_year)
        
        self.period = period  # Store period for use in sections
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,  # Portrait for player resume
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        story = []
        
        # PAGE 1: Cover and Identity
        cover_elements = self._create_resume_cover_page(physical_measurements or [], physical_metrics)
        story.extend(cover_elements)
        story.append(PageBreak())
        
        # PAGE 2: Season Performance Summary (aggregated only)
        performance_elements = self._create_season_performance_summary(matches)
        if performance_elements:
            story.extend(performance_elements)
            story.append(PageBreak())
        
        # PAGE 3: Match Contribution Overview (no match list)
        contribution_elements = self._create_match_contribution_overview(matches)
        if contribution_elements:
            story.extend(contribution_elements)
            story.append(PageBreak())
        
        # PAGE 4: Achievements
        achievements_elements = self._create_resume_achievements_section(achievements)
        if achievements_elements:
            story.extend(achievements_elements)
            story.append(PageBreak())
        
        # PAGE 5: Physical Development and Growth Analysis
        physical_elements = self._create_resume_physical_development_section(physical_measurements or [], physical_metrics)
        if physical_elements:
            story.extend(physical_elements)
            story.append(PageBreak())
        
        # PAGE 6: Club History (always include, even if empty)
        club_history_elements = self._create_resume_club_history_section(club_history or [])
        story.extend(club_history_elements)
        story.append(PageBreak())
        
        # PAGE 7: Training and Development Exposure (always include, even if empty)
        training_elements = self._create_resume_training_camps_section(training_camps or [])
        story.extend(training_elements)
        story.append(PageBreak())
        
        # PAGE 8: References
        references_elements = self._create_resume_references_section(references or [])
        if references_elements:
            story.extend(references_elements)
        
        # Add footer
        story.append(self._create_footer(matches))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    def _create_resume_cover_page(self, physical_measurements: List[PhysicalMeasurement], physical_metrics: List[PhysicalMetrics] = None) -> List:
        """Create comprehensive cover page with player identity and profile"""
        elements = []
        
        # Title
        player_name = self.settings.player_name or "Player"
        title = Paragraph(
            f"{player_name}<br/>Player Resume",
            ParagraphStyle(
                name='ResumeTitle',
                parent=self.styles['Title'],
                fontSize=28,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=self.primary_color,
                fontName='Helvetica-Bold',
                leading=34
            )
        )
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Player Photo (if available)
        if self.settings.player_photo_path and os.path.exists(self.settings.player_photo_path):
            try:
                photo_path = self.settings.player_photo_path
                if not os.path.isabs(photo_path):
                    if not os.path.exists(photo_path):
                        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        photo_path = os.path.join(app_dir, photo_path)
                
                img = Image(photo_path, width=2.5*inch, height=3*inch, kind='proportional')
                img_table = Table([[img]], colWidths=[7.5*inch])
                img_style = TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ])
                img_table.setStyle(img_style)
                elements.append(img_table)
                elements.append(Spacer(1, 20))
            except Exception as e:
                print(f"Error loading player photo: {e}")
        
        # Identity Information
        identity_data = []
        
        # Full name
        identity_data.append(["Full Name", self.settings.player_name or "Not recorded"])
        
        # Current club and age group
        club_name = self.settings.club_name or "Not recorded"
        # Calculate age group from date of birth
        age_group = "Not recorded"
        if self.settings.date_of_birth:
            try:
                from .phv_calculator import calculate_age_at_date
                current_age = calculate_age_at_date(self.settings.date_of_birth, datetime.now().strftime("%d %b %Y"))
                if current_age <= 12:
                    age_group = "U12"
                elif current_age <= 13:
                    age_group = "U13"
                elif current_age <= 14:
                    age_group = "U14"
                elif current_age <= 15:
                    age_group = "U15"
                elif current_age <= 16:
                    age_group = "U16"
                elif current_age <= 17:
                    age_group = "U17"
                else:
                    age_group = "U18+"
            except:
                pass
        
        identity_data.append(["Current Club", f"{club_name} ({age_group})"])
        
        # Selected season
        identity_data.append(["Season", self.settings.season_year or "Not recorded"])
        
        # Position and dominant foot
        position = self.settings.position or "Not recorded"
        dominant_foot = self.settings.dominant_foot or "Not recorded"
        identity_data.append(["Position", position])
        identity_data.append(["Dominant Foot", dominant_foot])
        
        # Date of birth
        identity_data.append(["Date of Birth", self.settings.date_of_birth or "Not recorded"])
        
        # Current height and weight from latest physical measurement
        latest_height = "Not recorded"
        latest_weight = "Not recorded"
        if physical_measurements:
            valid_measurements = [m for m in physical_measurements if m.height_cm is not None or m.weight_kg is not None]
            if valid_measurements:
                sorted_measurements = sorted(valid_measurements, key=lambda x: datetime.strptime(x.date, "%d %b %Y"), reverse=True)
                latest_measurement = sorted_measurements[0]
                if latest_measurement.height_cm:
                    latest_height = f"{latest_measurement.height_cm:.1f} cm"
                if latest_measurement.weight_kg:
                    latest_weight = f"{latest_measurement.weight_kg:.1f} kg"
        
        # Fallback to settings if no measurements
        if latest_height == "Not recorded" and self.settings.height_cm:
            latest_height = f"{self.settings.height_cm:.1f} cm"
        if latest_weight == "Not recorded" and self.settings.weight_kg:
            latest_weight = f"{self.settings.weight_kg:.1f} kg"
        
        identity_data.append(["Current Height", latest_height])
        identity_data.append(["Current Weight", latest_weight])
        
        # PHV Summary
        if self.settings.phv_date and self.settings.phv_age:
            # Determine PHV status
            try:
                phv_date_obj = datetime.strptime(self.settings.phv_date, "%d %b %Y")
                current_date = datetime.now()
                days_diff = (current_date - phv_date_obj).days
                
                if days_diff < 0:
                    phv_status = "Pre-PHV"
                elif days_diff < 180:
                    phv_status = "At PHV"
                else:
                    phv_status = "Post-PHV"
                
                phv_summary = f"{phv_status} (Age {self.settings.phv_age:.1f} years on {self.settings.phv_date})"
            except:
                phv_summary = f"Age {self.settings.phv_age:.1f} years ({self.settings.phv_date})"
            
            identity_data.append(["PHV Status", phv_summary])
        else:
            identity_data.append(["PHV Status", "Not recorded"])
        
        # Predicted adult height with confidence rating
        if physical_measurements and self.settings.date_of_birth:
            try:
                from .phv_calculator import calculate_phv, calculate_predicted_adult_height, calculate_age_at_date
                from .elite_benchmarks import get_elite_benchmarks_for_age
                
                # Get latest measurement for current age
                valid_measurements = [m for m in physical_measurements if m.height_cm is not None]
                if valid_measurements:
                    latest_measurement = max(valid_measurements, key=lambda m: datetime.strptime(m.date, "%d %b %Y"))
                    current_age = calculate_age_at_date(self.settings.date_of_birth, latest_measurement.date)
                    
                    phv_result = calculate_phv(physical_measurements, self.settings.date_of_birth)
                    predicted_height = calculate_predicted_adult_height(
                        physical_measurements,
                        self.settings.date_of_birth,
                        current_age,
                        phv_result
                    )
                    
                    if predicted_height:
                        confidence = predicted_height.get('confidence', 'medium')
                        height_cm = predicted_height.get('predicted_adult_height_cm', 0)
                        height_ft_in = predicted_height.get('predicted_adult_height_ft_in', '')
                        identity_data.append(["Predicted Adult Height", f"{height_cm:.1f} cm ({height_ft_in}) - Confidence: {confidence.title()}"])
                    else:
                        identity_data.append(["Predicted Adult Height", "Not recorded"])
                else:
                    identity_data.append(["Predicted Adult Height", "Not recorded"])
            except Exception as e:
                print(f"Error calculating predicted height: {e}")
                identity_data.append(["Predicted Adult Height", "Not recorded"])
        else:
            identity_data.append(["Predicted Adult Height", "Not recorded"])
        
        # Playing profile bullet points
        if self.settings.playing_profile and len(self.settings.playing_profile) > 0:
            profile_text = "<br/>".join([f"• {item.strip()}" for item in self.settings.playing_profile if item and item.strip()])
            identity_data.append(["Playing Profile", profile_text])
        else:
            identity_data.append(["Playing Profile", "Not recorded"])
        
        # Performance metric context comments
        if self.settings.performance_metric_comments and len(self.settings.performance_metric_comments) > 0:
            comments_text = "<br/>".join([f"<b>{key}:</b> {value}" for key, value in self.settings.performance_metric_comments.items() if value])
            identity_data.append(["Performance Metric Context", comments_text])
        else:
            identity_data.append(["Performance Metric Context", "Not recorded"])
        
        # Create identity table
        wrapped_identity_data = []
        for row_idx, row in enumerate(identity_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:  # Header row (we'll add one)
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
            wrapped_identity_data.append(wrapped_row)
        
        # Add header row
        header_row = [Paragraph("Attribute", self.styles['TableHeader']), Paragraph("Details", self.styles['TableHeader'])]
        identity_table_data = [header_row] + [[Paragraph(str(row[0]), self.styles['TableCell']), Paragraph(str(row[1]), self.styles['TableCell'])] for row in identity_data]
        
        identity_table = Table(identity_table_data, colWidths=[2.5*inch, 4.5*inch])
        identity_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])
        identity_table.setStyle(identity_style)
        elements.append(identity_table)
        
        return elements
    
    def _create_season_performance_summary(self, matches: List[Match]) -> List:
        """Create season performance summary with aggregated statistics only"""
        elements = []
        
        elements.append(Paragraph("Season Performance Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        completed_matches = [m for m in matches if not m.is_fixture]
        if not completed_matches:
            elements.append(Paragraph("No match data available for the selected period.", self.styles['TableCell']))
            return elements
        
        # Calculate aggregated stats
        total_stats = self._calculate_category_stats(completed_matches)
        advanced_stats = self._calculate_advanced_stats(completed_matches)
        
        # Calculate wins, draws, losses
        wins = sum(1 for m in completed_matches if m.result and m.result.value == "Win")
        draws = sum(1 for m in completed_matches if m.result and m.result.value == "Draw")
        losses = sum(1 for m in completed_matches if m.result and m.result.value == "Loss")
        
        # Calculate average minutes per match
        avg_minutes_per_match = total_stats['minutes'] / total_stats['matches'] if total_stats['matches'] > 0 else 0
        
        # Create summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Matches Played', str(total_stats['matches'])],
            ['Wins', str(wins)],
            ['Draws', str(draws)],
            ['Losses', str(losses)],
            ['Total Goals', str(total_stats['goals'])],
            ['Total Assists', str(total_stats['assists'])],
            ['Total Minutes Played', str(total_stats['minutes'])],
            ['Average Minutes per Match', f"{avg_minutes_per_match:.1f}"],
            ['Goals per 60 Minutes', f"{advanced_stats['goals_per_60']:.2f}"],
            ['Assists per 60 Minutes', f"{advanced_stats['assists_per_60']:.2f}"],
            ['Goal Contributions per 60 Minutes', f"{advanced_stats['contribution_per_60']:.2f}"],
        ]
        
        # Add minutes per goal and minutes per contribution
        if total_stats['goals'] > 0:
            min_per_goal = total_stats['minutes'] / total_stats['goals']
            summary_data.append(['Minutes per Goal', f"{min_per_goal:.0f}"])
        
        if (total_stats['goals'] + total_stats['assists']) > 0:
            min_per_contribution = total_stats['minutes'] / (total_stats['goals'] + total_stats['assists'])
            summary_data.append(['Minutes per Goal Contribution', f"{min_per_contribution:.0f}"])
        
        # Convert to Paragraph objects
        wrapped_summary_data = []
        for row_idx, row in enumerate(summary_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    if col_idx == 0:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                    else:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
            wrapped_summary_data.append(wrapped_row)
        
        summary_table = Table(wrapped_summary_data, colWidths=[3.5*inch, 3.5*inch])
        summary_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])
        summary_table.setStyle(summary_style)
        elements.append(summary_table)
        
        return elements
    
    def _create_match_contribution_overview(self, matches: List[Match]) -> List:
        """Create match contribution overview with summary metrics and textual summary"""
        elements = []
        
        elements.append(Paragraph("Match Contribution Overview", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        completed_matches = [m for m in matches if not m.is_fixture]
        if not completed_matches:
            elements.append(Paragraph("No match data available for the selected period.", self.styles['TableCell']))
            return elements
        
        # Calculate stats
        total_stats = self._calculate_category_stats(completed_matches)
        advanced_stats = self._calculate_advanced_stats(completed_matches)
        
        # Goal involvement summary
        goal_involvements = sum(1 for m in completed_matches if m.brodie_goals > 0 or m.brodie_assists > 0)
        goal_involvement_rate = (goal_involvements / total_stats['matches']) * 100 if total_stats['matches'] > 0 else 0
        
        # Contribution rate metrics
        contribution_rate = advanced_stats['contribution_per_60']
        
        # Consistency indicators
        matches_with_goals = sum(1 for m in completed_matches if m.brodie_goals > 0)
        matches_with_assists = sum(1 for m in completed_matches if m.brodie_assists > 0)
        matches_with_contributions = sum(1 for m in completed_matches if (m.brodie_goals + m.brodie_assists) > 0)
        
        # Create overview table
        overview_data = [
            ['Metric', 'Value'],
            ['Goal Involvement Rate', f"{goal_involvement_rate:.1f}% ({goal_involvements}/{total_stats['matches']} matches)"],
            ['Contribution Rate (G+A per 60 min)', f"{contribution_rate:.2f}"],
            ['Matches with Goals', f"{matches_with_goals} ({matches_with_goals/total_stats['matches']*100:.1f}%)" if total_stats['matches'] > 0 else "0"],
            ['Matches with Assists', f"{matches_with_assists} ({matches_with_assists/total_stats['matches']*100:.1f}%)" if total_stats['matches'] > 0 else "0"],
            ['Matches with Contributions', f"{matches_with_contributions} ({matches_with_contributions/total_stats['matches']*100:.1f}%)" if total_stats['matches'] > 0 else "0"],
        ]
        
        # Convert to Paragraph objects
        wrapped_overview_data = []
        for row_idx, row in enumerate(overview_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    if col_idx == 0:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                    else:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
            wrapped_overview_data.append(wrapped_row)
        
        overview_table = Table(wrapped_overview_data, colWidths=[3.5*inch, 3.5*inch])
        overview_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])
        overview_table.setStyle(overview_style)
        elements.append(overview_table)
        
        # Generate textual summary
        elements.append(Spacer(1, 12))
        summary_text = self._generate_contribution_summary_text(total_stats, advanced_stats, goal_involvement_rate, matches_with_contributions, total_stats['matches'])
        summary_para = Paragraph(summary_text, ParagraphStyle(
            name='ContributionSummary',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=0,
            leading=14
        ))
        elements.append(summary_para)
        
        return elements
    
    def _generate_contribution_summary_text(self, total_stats: Dict, advanced_stats: Dict, goal_involvement_rate: float, matches_with_contributions: int, total_matches: int) -> str:
        """Generate textual summary of match contributions"""
        if total_matches == 0:
            return "No match data available."
        
        contribution_rate = advanced_stats.get('contribution_per_60', 0)
        goals_per_60 = advanced_stats.get('goals_per_60', 0)
        assists_per_60 = advanced_stats.get('assists_per_60', 0)
        
        # Build summary text
        summary_parts = []
        
        # Consistency
        if matches_with_contributions >= total_matches * 0.7:
            summary_parts.append("Consistent attacking contributor across the season")
        elif matches_with_contributions >= total_matches * 0.5:
            summary_parts.append("Regular contributor to team attacking play")
        else:
            summary_parts.append("Contributing player with selective impact")
        
        # Rate-based description
        if contribution_rate >= 1.5:
            summary_parts.append("with high goal contribution rate")
        elif contribution_rate >= 1.0:
            summary_parts.append("with solid goal contribution rate")
        else:
            summary_parts.append("with developing contribution rate")
        
        # Goals vs assists balance
        if goals_per_60 > assists_per_60 * 1.5:
            summary_parts.append("primarily through goal scoring")
        elif assists_per_60 > goals_per_60 * 1.5:
            summary_parts.append("primarily through assists")
        else:
            summary_parts.append("through balanced goals and assists")
        
        return ". ".join(summary_parts) + "."
    
    def _create_resume_achievements_section(self, achievements: List[Achievement]) -> List:
        """Create achievements section grouped by season and achievement type"""
        elements = []
        
        elements.append(Paragraph("Achievements", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        if not achievements:
            elements.append(Paragraph("No achievements recorded.", self.styles['TableCell']))
            return elements
        
        # Group by season
        achievements_by_season = {}
        for achievement in achievements:
            season = achievement.season or "Unknown Season"
            if season not in achievements_by_season:
                achievements_by_season[season] = []
            achievements_by_season[season].append(achievement)
        
        # Sort seasons (most recent first)
        sorted_seasons = sorted(achievements_by_season.keys(), reverse=True)
        
        # Group by achievement type (category)
        for season in sorted_seasons:
            season_achievements = achievements_by_season[season]
            
            # Group by category
            by_category = {}
            for achievement in season_achievements:
                category = achievement.category or "Other"
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(achievement)
            
            # Create table for this season
            season_data = [['Date', 'Achievement', 'Category', 'Description']]
            for category in sorted(by_category.keys()):
                for achievement in sorted(by_category[category], key=lambda x: datetime.strptime(x.date, "%d %b %Y"), reverse=True):
                    season_data.append([
                        achievement.date,
                        achievement.title,
                        achievement.category,
                        achievement.description or '-'
                    ])
            
            # Add season header
            season_header = Paragraph(f"<b>Season: {season}</b>", ParagraphStyle(
                name='SeasonHeader',
                parent=self.styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                textColor=self.header_color,
                spaceAfter=6
            ))
            elements.append(season_header)
            
            # Convert to Paragraph objects
            wrapped_season_data = []
            for row_idx, row in enumerate(season_data):
                wrapped_row = []
                for col_idx, cell in enumerate(row):
                    if row_idx == 0:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                    else:
                        if col_idx == 1 or col_idx == 3:  # Achievement title and description - left align
                            wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                        else:  # Date and Category - center align
                            wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
                wrapped_season_data.append(wrapped_row)
            
            season_table = Table(wrapped_season_data, colWidths=[1.2*inch, 2.5*inch, 1*inch, 2.3*inch])
            season_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Date
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Achievement
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Category
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),  # Description
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            season_table.setStyle(season_style)
            elements.append(season_table)
            elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_resume_physical_development_section(self, physical_measurements: List[PhysicalMeasurement], physical_metrics: List[PhysicalMetrics] = None) -> List:
        """Create comprehensive physical development and growth analysis section"""
        elements = []
        
        elements.append(Paragraph("Physical Development and Growth Analysis", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        # PHV Details
        if self.settings.phv_date and self.settings.phv_age:
            phv_data = [
                ['PHV Metric', 'Value'],
                ['PHV Date', self.settings.phv_date],
                ['PHV Age', f"{self.settings.phv_age:.1f} years"],
            ]
            
            # Get PHV velocity if available from calculations
            if physical_measurements and self.settings.date_of_birth:
                try:
                    from .phv_calculator import calculate_phv
                    phv_result = calculate_phv(physical_measurements, self.settings.date_of_birth)
                    if phv_result and phv_result.get('phv_velocity_cm_per_year'):
                        phv_data.append(['Peak Growth Velocity', f"{phv_result['phv_velocity_cm_per_year']:.2f} cm/year"])
                except:
                    pass
            
            # Determine PHV status
            try:
                phv_date_obj = datetime.strptime(self.settings.phv_date, "%d %b %Y")
                current_date = datetime.now()
                days_diff = (current_date - phv_date_obj).days
                
                if days_diff < 0:
                    phv_status = "Pre-PHV"
                elif days_diff < 180:
                    phv_status = "At PHV"
                else:
                    phv_status = "Post-PHV"
                
                phv_data.append(['Current PHV Status', phv_status])
            except:
                pass
            
            # Create PHV table
            wrapped_phv_data = []
            for row_idx, row in enumerate(phv_data):
                wrapped_row = []
                for col_idx, cell in enumerate(row):
                    if row_idx == 0:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                    else:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                wrapped_phv_data.append(wrapped_row)
            
            phv_table = Table(wrapped_phv_data, colWidths=[3.5*inch, 3.5*inch])
            phv_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ])
            phv_table.setStyle(phv_style)
            elements.append(phv_table)
            elements.append(Spacer(1, 12))
        
        # Elite benchmark comparisons
        if physical_measurements and self.settings.date_of_birth:
            try:
                from .phv_calculator import calculate_age_at_date
                from .elite_benchmarks import get_elite_benchmarks_for_age, compare_to_elite
                
                # Get latest measurement for current age
                valid_measurements = [m for m in physical_measurements if m.height_cm is not None]
                if valid_measurements:
                    latest_measurement = max(valid_measurements, key=lambda m: datetime.strptime(m.date, "%d %b %Y"))
                    current_age = calculate_age_at_date(self.settings.date_of_birth, latest_measurement.date)
                    current_height = latest_measurement.height_cm
                    current_weight = latest_measurement.weight_kg
                    
                    benchmarks = get_elite_benchmarks_for_age(current_age)
                    
                    # Height percentile
                    height_comparison = compare_to_elite(current_height, benchmarks['metrics']['height'], 'higher_is_better')
                    
                    # BMI calculation and comparison
                    bmi = None
                    if current_height and current_weight:
                        bmi = current_weight / ((current_height / 100) ** 2)
                        bmi_benchmark = benchmarks['metrics']['body_composition']
                    
                    # Create elite benchmarks table
                    benchmark_data = [
                        ['Metric', 'Player Value', 'Elite Percentile', 'Rating'],
                        ['Height', f"{current_height:.1f} cm", f"{height_comparison['percentile']}th", height_comparison['rating']],
                    ]
                    
                    if bmi:
                        if bmi_benchmark['optimal_bmi_min'] <= bmi <= bmi_benchmark['optimal_bmi_max']:
                            bmi_rating = "Optimal"
                        elif bmi_benchmark['elite_bmi_min'] <= bmi <= bmi_benchmark['elite_bmi_max']:
                            bmi_rating = "Elite Range"
                        else:
                            bmi_rating = "Outside Range"
                        
                        benchmark_data.append(['BMI', f"{bmi:.1f}", f"Range: {bmi_benchmark['optimal_bmi_min']:.1f}-{bmi_benchmark['optimal_bmi_max']:.1f}", bmi_rating])
                    
                    # Convert to Paragraph objects
                    wrapped_benchmark_data = []
                    for row_idx, row in enumerate(benchmark_data):
                        wrapped_row = []
                        for col_idx, cell in enumerate(row):
                            if row_idx == 0:
                                wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                            else:
                                wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                        wrapped_benchmark_data.append(wrapped_row)
                    
                    benchmark_table = Table(wrapped_benchmark_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 2.5*inch])
                    benchmark_style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ])
                    benchmark_table.setStyle(benchmark_style)
                    elements.append(benchmark_table)
                    elements.append(Spacer(1, 12))
            except Exception as e:
                print(f"Error calculating elite benchmarks: {e}")
        
        # Historical height and weight measurements (respecting include_in_report flags)
        report_measurements = [
            m for m in physical_measurements 
            if m.height_cm is not None and (m.include_in_report if hasattr(m, 'include_in_report') else True)
        ]
        
        if report_measurements:
            sorted_measurements = sorted(report_measurements, key=lambda m: datetime.strptime(m.date, "%d %b %Y"))
            
            measurements_data = [['Date', 'Height (cm)', 'Weight (kg)', 'Notes']]
            for m in sorted_measurements:
                measurements_data.append([
                    m.date,
                    f"{m.height_cm:.1f}" if m.height_cm else '-',
                    f"{m.weight_kg:.1f}" if m.weight_kg else '-',
                    m.notes or '-'
                ])
            
            # Convert to Paragraph objects
            wrapped_measurements_data = []
            for row_idx, row in enumerate(measurements_data):
                wrapped_row = []
                for col_idx, cell in enumerate(row):
                    if row_idx == 0:
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                    else:
                        if col_idx == 3:  # Notes - left align
                            wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                        else:  # Date, Height, Weight - center align
                            wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
                wrapped_measurements_data.append(wrapped_row)
            
            measurements_table = Table(wrapped_measurements_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 3.1*inch])
            measurements_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (2, -1), 'CENTER'),  # Date, Height, Weight
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),  # Notes
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            measurements_table.setStyle(measurements_style)
            elements.append(measurements_table)
        
        return elements
    
    def _create_resume_club_history_section(self, club_history: List[ClubHistory]) -> List:
        """Create club history section"""
        elements = []
        
        elements.append(Paragraph("Club History", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        if not club_history:
            elements.append(Paragraph("No club history recorded.", self.styles['TableCell']))
            return elements
        
        # Sort by season (most recent first)
        sorted_history = sorted(club_history, key=lambda x: x.season, reverse=True)
        
        history_data = [['Club Name', 'Season', 'Age Group', 'Position', 'Achievements/Notes']]
        for entry in sorted_history:
            history_data.append([
                entry.club_name,
                entry.season,
                entry.age_group or '-',
                entry.position or '-',
                entry.achievements or entry.notes or '-'
            ])
        
        # Convert to Paragraph objects
        wrapped_history_data = []
        for row_idx, row in enumerate(history_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    if col_idx in [1, 2]:  # Season, Age Group - center align
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCellCenter']))
                    else:  # Club, Position, Achievements - left align
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
            wrapped_history_data.append(wrapped_row)
        
        history_table = Table(wrapped_history_data, colWidths=[1.8*inch, 1.2*inch, 0.9*inch, 1*inch, 2.1*inch])
        history_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Club
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Season
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Age Group
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),  # Position
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),  # Achievements
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        history_table.setStyle(history_style)
        elements.append(history_table)
        
        return elements
    
    def _create_resume_training_camps_section(self, training_camps: List[TrainingCamp]) -> List:
        """Create training camps section"""
        elements = []
        
        elements.append(Paragraph("Training and Development Exposure", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        if not training_camps:
            elements.append(Paragraph("No training camps recorded.", self.styles['TableCell']))
            return elements
        
        # Sort by start date (most recent first)
        sorted_camps = sorted(
            training_camps, 
            key=lambda x: datetime.strptime(x.start_date, "%d %b %Y"), 
            reverse=True
        )
        
        camps_data = [['Camp Name', 'Organizer', 'Location', 'Date Range', 'Age Group', 'Focus Area']]
        for camp in sorted_camps:
            date_str = camp.start_date
            if camp.end_date:
                date_str += f" - {camp.end_date}"
            
            camps_data.append([
                camp.camp_name,
                camp.organizer,
                camp.location,
                date_str,
                camp.age_group or '-',
                camp.focus_area or '-'
            ])
        
        # Convert to Paragraph objects
        wrapped_camps_data = []
        for row_idx, row in enumerate(camps_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    if col_idx in [1, 2, 3]:  # Organizer, Location, Date - left align with wrapping
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
                    else:  # Camp Name, Age Group, Focus Area - left align
                        wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
            wrapped_camps_data.append(wrapped_row)
        
        camps_table = Table(wrapped_camps_data, colWidths=[1.5*inch, 1.5*inch, 1.2*inch, 1.5*inch, 0.8*inch, 1.5*inch])
        camps_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        camps_table.setStyle(camps_style)
        elements.append(camps_table)
        
        return elements
    
    def _create_resume_references_section(self, references: List[Reference]) -> List:
        """Create references section"""
        elements = []
        
        elements.append(Paragraph("References", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        if not references or len(references) == 0:
            elements.append(Paragraph("No references recorded.", self.styles['TableCell']))
            return elements
        
        # Create references list
        for ref in references:
            ref_elements = []
            
            # Name and position
            name_text = f"<b>{ref.name}</b>"
            if ref.position:
                name_text += f" - {ref.position}"
            if ref.organization:
                name_text += f" ({ref.organization})"
            
            ref_elements.append(Paragraph(name_text, self.styles['TableCell']))
            
            # Contact info
            contact_parts = []
            if ref.email:
                contact_parts.append(f"Email: {ref.email}")
            if ref.phone:
                contact_parts.append(f"Phone: {ref.phone}")
            if contact_parts:
                ref_elements.append(Paragraph(" | ".join(contact_parts), self.styles['TableCell']))
            
            # Relationship
            if ref.relationship:
                ref_elements.append(Paragraph(f"<i>{ref.relationship}</i>", self.styles['TableCell']))
            
            # Notes
            if ref.notes:
                ref_elements.append(Paragraph(ref.notes, self.styles['TableCell']))
            
            # Add spacing between references
            ref_elements.append(Spacer(1, 8))
            
            elements.extend(ref_elements)
        
        return elements
