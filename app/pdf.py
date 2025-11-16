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

from .models import Match, AppSettings, PhysicalMeasurement, Achievement, ClubHistory, TrainingCamp, PhysicalMetrics
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
    return generator.generate_pdf(matches, output_path, achievements, club_history, physical_measurements or [], training_camps or [], physical_metrics or [], period=period)


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
        story.extend(self._create_title_page())
        story.append(PageBreak())
        
        # PAGE 2: Player photo & social media links
        story.extend(self._create_player_media_section())
        story.append(PageBreak())
        
        # PAGE 3: Club history and training camps
        club_history_elements = []
        training_camps_elements = []
        
        if club_history:
            club_history_elements = self._create_club_history_section(club_history)
        if training_camps:
            training_camps_elements = self._create_training_camps_section(training_camps)
        
        # Combine both sections and keep them together on same page
        if club_history_elements or training_camps_elements:
            combined_elements = []
            if club_history_elements:
                combined_elements.extend(club_history_elements)
                combined_elements.append(Spacer(1, 12))
            if training_camps_elements:
                combined_elements.extend(training_camps_elements)
            # Use KeepTogether to ensure both sections stay on same page
            story.append(KeepTogether(combined_elements))
        story.append(PageBreak())
        
        # PAGE 4: Key achievements, physical development, physical performance metrics
        page4_elements = []
        
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
            story.append(KeepTogether(page4_elements))
        story.append(PageBreak())
        
        # PAGE 5: Performance summary and key statistics
        page5_elements = []
        
        # Add performance summary
        performance_summary_elements = self._create_performance_summary(matches)
        if performance_summary_elements:
            page5_elements.extend(performance_summary_elements)
            page5_elements.append(Spacer(1, 12))
        
        # Add key statistics
        page5_elements.extend(self._create_key_statistics(matches))
        
        # Keep all page 5 content together
        if page5_elements:
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
        title = Paragraph(
            f"{self.settings.player_name}<br/>Player Profile & Performance Report",
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
        
        # Current club and season
        club_info = Paragraph(
            f"<b>Current Club:</b> {self.settings.club_name}<br/>"
            f"<b>Season:</b> {self.settings.season_year}",
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
        
        # Basic Information
        if self.settings.player_name:
            profile_data.append(["Name", self.settings.player_name])
        if self.settings.date_of_birth:
            profile_data.append(["Date of Birth", self.settings.date_of_birth])
        if self.settings.position:
            profile_data.append(["Position", self.settings.position])
        if self.settings.dominant_foot:
            profile_data.append(["Dominant Foot", self.settings.dominant_foot])
        if self.settings.club_name:
            profile_data.append(["Current Club", self.settings.club_name])
        
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
        
        # PHV Information
        if self.settings.phv_date and self.settings.phv_age:
            profile_data.append(["Peak Height Velocity", f"Age {self.settings.phv_age:.1f} years ({self.settings.phv_date})"])
        
        if profile_data:
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
    
    def _create_player_media_section(self) -> List:
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
        """Create physical performance metrics section"""
        elements = []
        
        # Sort by date (most recent first)
        sorted_metrics = sorted(
            physical_metrics, 
            key=lambda x: datetime.strptime(x.date, "%d %b %Y"), 
            reverse=True
        )
        
        # Create a comprehensive table with key metrics
        metrics_data = [['Date', 'Sprint Speed', '10m (s)', '20m (s)', '30m (s)', 'Vertical Jump', 'Standing Long Jump', 'Beep Test']]
        for metric in sorted_metrics:
            # Sprint speed info
            sprint_str = '-'
            if metric.sprint_speed_ms:
                sprint_str = f"{metric.sprint_speed_ms:.2f} m/s"
            elif metric.sprint_speed_kmh:
                sprint_str = f"{metric.sprint_speed_kmh:.1f} km/h"
            else:
                sprint_str = '-'
            
            # Sprint times
            sprint_10m_str = f"{metric.sprint_10m_sec:.2f}" if metric.sprint_10m_sec else '-'
            sprint_20m_str = f"{metric.sprint_20m_sec:.2f}" if metric.sprint_20m_sec else '-'
            sprint_30m_str = f"{metric.sprint_30m_sec:.2f}" if metric.sprint_30m_sec else '-'
            
            # Vertical Jump info
            vertical_jump_str = '-'
            if metric.vertical_jump_cm:
                vertical_jump_str = f"{metric.vertical_jump_cm:.1f} cm"
            elif metric.countermovement_jump_cm:
                vertical_jump_str = f"CMJ: {metric.countermovement_jump_cm:.1f} cm"
            
            # Standing Long Jump info
            standing_long_jump_str = f"{metric.standing_long_jump_cm:.1f} cm" if metric.standing_long_jump_cm else '-'
            
            # Beep Test
            beep_test_str = f"{metric.beep_test_level:.1f}" if metric.beep_test_level else '-'
            
            metrics_data.append([
                metric.date,
                sprint_str,
                sprint_10m_str,
                sprint_20m_str,
                sprint_30m_str,
                vertical_jump_str,
                standing_long_jump_str,
                beep_test_str
            ])
        
        # Convert to Paragraph objects for proper text wrapping
        wrapped_metrics_data = []
        for row_idx, row in enumerate(metrics_data):
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                if row_idx == 0:  # Header row
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableHeader']))
                else:
                    wrapped_row.append(Paragraph(str(cell), self.styles['TableCell']))
            wrapped_metrics_data.append(wrapped_row)
        
        # Calculate better column widths for A4 portrait (8.27 inches total width, minus margins)
        # Using approximately 7.5 inches for table width
        metrics_table = Table(wrapped_metrics_data, colWidths=[
            0.85*inch,  # Date
            1.0*inch,   # Sprint Speed
            0.7*inch,   # 10m
            0.7*inch,   # 20m
            0.7*inch,   # 30m
            1.0*inch,   # Vertical Jump
            1.1*inch,   # Standing Long Jump
            0.75*inch   # Beep Test
        ])
        metrics_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Date
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Sprint Speed
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # 10m
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # 20m
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # 30m
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Vertical Jump
            ('ALIGN', (6, 1), (6, -1), 'CENTER'),  # Standing Long Jump
            ('ALIGN', (7, 1), (7, -1), 'CENTER'),  # Beep Test
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_grey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])
        metrics_table.setStyle(metrics_style)
        
        # Use KeepTogether to ensure header and table stay on same page
        header_para = Paragraph("Physical Performance Metrics", self.styles['SectionHeader'])
        spacer = Spacer(1, 12)
        elements.append(KeepTogether([header_para, spacer, metrics_table]))
        
        return elements
    
    def _create_physical_development_section(self, physical_measurements: List[PhysicalMeasurement]) -> List:
        """Create physical development timeline"""
        elements = []
        
        elements.append(Paragraph("Physical Development", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))
        
        # Sort by date
        sorted_measurements = sorted(
            [m for m in physical_measurements if m.height_cm is not None],
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
        
        metrics_data = [
            ['Metric', 'Value'],
            ['Goals per 60 minutes', f"{advanced_stats['goals_per_60']:.2f}"],
            ['Assists per 60 minutes', f"{advanced_stats['assists_per_60']:.2f}"],
            ['Goal Contributions per 60', f"{advanced_stats['contribution_per_60']:.2f}"],
        ]
        
        if advanced_stats['matches'] > 0:
            g_a_per_match = (advanced_stats['goals'] + advanced_stats['assists']) / advanced_stats['matches']
            metrics_data.append(['Goal Contributions per Match', f"{g_a_per_match:.2f}"])
        
        if advanced_stats['goals'] + advanced_stats['assists'] > 0:
            min_per_ga = advanced_stats['minutes'] / (advanced_stats['goals'] + advanced_stats['assists'])
            metrics_data.append(['Minutes per Goal Contribution', f"{min_per_ga:.0f}"])
        
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
