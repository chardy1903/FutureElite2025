"""
Type definitions for the report generation system.

These types define the data contract for generating PDF reports.
"""

from typing import Optional, List, Dict, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class Match(BaseModel):
    """Match data model for reports"""
    matchDay: Optional[int] = None
    date: str  # ISO format date string
    opponent: str
    location: Optional[str] = None
    category: Optional[str] = None  # Friendly/League/Tournament/etc
    scoreFor: Optional[int] = None
    scoreAgainst: Optional[int] = None
    minutesPlayed: int
    goals: int
    assists: int
    notes: Optional[str] = None


class PHVData(BaseModel):
    """Peak Height Velocity data"""
    phvDate: Optional[str] = None  # ISO format
    phvAgeYears: Optional[float] = None
    status: Optional[Literal["Pre-PHV", "Circa-PHV", "Post-PHV"]] = None
    peakGrowthVelocityCmPerYear: Optional[float] = None
    predictedAdultHeightCm: Optional[float] = None
    predictedAdultHeightConfidence: Optional[Literal["Low", "Medium", "High"]] = None


class GrowthHistoryEntry(BaseModel):
    """Historical growth measurement"""
    date: str  # ISO format
    heightCm: Optional[float] = None
    weightKg: Optional[float] = None
    notes: Optional[str] = None


class ClubHistoryEntry(BaseModel):
    """Club history entry"""
    clubName: str
    season: str
    ageGroup: Optional[str] = None
    position: Optional[str] = None
    achievements: Optional[str] = None


class Award(BaseModel):
    """Award or achievement"""
    date: str  # ISO format
    title: str
    category: str
    description: Optional[str] = None


class TrainingCamp(BaseModel):
    """Training camp entry"""
    name: str
    organizer: Optional[str] = None
    location: Optional[str] = None
    startDate: str  # ISO format
    endDate: str  # ISO format
    ageGroup: Optional[str] = None
    focusArea: Optional[str] = None


class SocialLink(BaseModel):
    """Social media link"""
    platform: str
    url: str


class Reference(BaseModel):
    """Reference contact"""
    name: str
    role: Optional[str] = None
    club: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class Player(BaseModel):
    """Complete player data model for report generation"""
    fullName: str
    dob: str  # ISO format date string
    nationality: Optional[str] = None
    positionPrimary: str
    positionSecondary: Optional[List[str]] = None
    dominantFoot: Optional[Literal["Right", "Left", "Both"]] = None
    currentClub: str
    team: str
    seasonLabel: str  # e.g., "2025/26"
    contactEmail: Optional[str] = None
    socialLinks: Optional[List[SocialLink]] = None
    heightCm: Optional[float] = None
    weightKg: Optional[float] = None
    bmi: Optional[float] = None
    phv: Optional[PHVData] = None
    growthHistory: Optional[List[GrowthHistoryEntry]] = None
    clubHistory: Optional[List[ClubHistoryEntry]] = None
    awards: Optional[List[Award]] = None
    camps: Optional[List[TrainingCamp]] = None
    highlightReelUrl: Optional[str] = None
    references: Optional[List[Reference]] = None
    matches: List[Match] = Field(default_factory=list)

