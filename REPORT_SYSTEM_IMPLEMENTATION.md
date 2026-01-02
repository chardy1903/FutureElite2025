# FutureElite Report System Implementation

## Overview

This document describes the new three-report PDF generation system for FutureElite. The system produces three distinct PDF reports with unique purposes, layouts, and content.

## Report Types

### 1. Season Tracker
- **Purpose**: Detailed match-by-match log for the current season
- **Layout**: Landscape A4, 2-5 pages
- **Content**: 
  - Cover header with summary stats
  - Season summary metrics table
  - Performance highlights (top 3 matches, consistency, recent form)
  - Full season match data table

### 2. Scout Report
- **Purpose**: Fast scout decision document
- **Layout**: Portrait A4, 1-2 pages maximum
- **Content**:
  - Player snapshot (identity, physical attributes, PHV status)
  - Key performance indicators (compact grid)
  - Standout performances (top 3)
  - Media and contact information

### 3. Player Resume
- **Purpose**: Comprehensive career document for clubs, trials, and longer review
- **Layout**: Portrait A4, multi-page allowed
- **Content**:
  - Identity & snapshot
  - Season performance summary
  - Match contribution overview
  - Achievements & awards
  - Physical development and growth
  - Club history
  - Training & development exposure
  - References

## File Structure

```
app/reports/
├── __init__.py              # Main entry point
├── types.py                 # Player and Match data models
├── adapters.py              # Convert from app models to Player type
├── metrics.py               # Standardized metric calculations
├── formatters.py            # Date, rounding, and unit conversions
├── base_generator.py         # Base PDF generator class
├── season_tracker.py         # Season Tracker report generator
├── scout_report.py           # Scout Report generator
├── player_resume.py          # Player Resume generator
└── generators.py             # Main entry functions
```

## Usage

### Basic Usage

```python
from app.reports import (
    generate_season_tracker_from_data,
    generate_scout_report_from_data,
    generate_player_resume_from_data
)

# Generate Season Tracker
season_tracker_path = generate_season_tracker_from_data(
    settings=settings,
    matches=matches,
    physical_measurements=physical_measurements,
    output_dir="output"
)

# Generate Scout Report
scout_report_path = generate_scout_report_from_data(
    settings=settings,
    matches=matches,
    achievements=achievements,
    club_history=club_history,
    training_camps=training_camps,
    references=references,
    output_dir="output"
)

# Generate Player Resume
player_resume_path = generate_player_resume_from_data(
    settings=settings,
    matches=matches,
    achievements=achievements,
    club_history=club_history,
    training_camps=training_camps,
    physical_measurements=physical_measurements,
    references=references,
    output_dir="output"
)

# Or generate all three at once
from app.reports import generate_all_reports

reports = generate_all_reports(
    settings=settings,
    matches=matches,
    physical_measurements=physical_measurements,
    achievements=achievements,
    club_history=club_history,
    training_camps=training_camps,
    references=references,
    output_dir="output"
)
```

## Key Features

### Standardized Metrics
All metrics are calculated consistently across reports using shared functions in `metrics.py`:
- Total matches, minutes, goals, assists, contributions
- Per-60 metrics (goals, assists, contributions)
- Per-match metrics
- Minutes per goal/contribution
- Goal involvement rate

### Consistent Formatting
All formatting is handled by `formatters.py`:
- Dates: DD MMM YYYY format
- Per-60 metrics: 2 decimals
- Per-match metrics: 2 decimals
- Minutes per: nearest whole minute
- Percentages: 1 decimal
- Height/weight: 1 decimal

### Data Safety
- Only renders fields that exist in input data
- Shows "Not recorded" for missing required fields
- Omits sections if no data available (where appropriate)
- No invented data or subjective claims

## Integration with Existing Code

The new system is designed to work alongside the existing PDF generation code. It uses adapters to convert from existing app models (`AppSettings`, `Match`, etc.) to the new `Player` type, ensuring zero breaking changes.

To integrate with existing routes, you can replace calls to the old PDF generators with calls to the new generators from `app.reports.generators`.

## Quality Checks

- Scout Report never exceeds 2 pages (enforced by layout rules)
- No report includes disallowed sections
- All per-60 metrics match across reports for the same data
- Safe handling of zero minutes (shows "N/A" for per-60 and minutes-per metrics)

## Dependencies

- ReportLab (already in requirements.txt)
- Pydantic (already in requirements.txt)
- Standard library modules

## Notes

- The system uses ReportLab for PDF generation
- All reports include consistent headers and footers
- Typography, spacing, and section headers are consistent across reports
- The Player data model defines the complete data contract for report generation

