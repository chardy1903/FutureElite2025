from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, validator
from enum import Enum


class MatchCategory(str, Enum):
    PRE_SEASON_FRIENDLY = "Pre-Season Friendly"
    LEAGUE = "League"
    FRIENDLY = "Friendly"


class MatchResult(str, Enum):
    WIN = "Win"
    DRAW = "Draw"
    LOSS = "Loss"


class Match(BaseModel):
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    category: MatchCategory
    date: str  # Format: "dd MMM yyyy"
    opponent: str
    location: str
    result: Optional[MatchResult] = None
    score: Optional[str] = None  # Format: "7 - 5"
    brodie_goals: int = 0
    brodie_assists: int = 0
    clean_sheets: Optional[int] = None  # Clean sheets (for defenders/goalkeepers)
    minutes_played: int = 0
    notes: str = ""
    is_fixture: bool = False  # True for upcoming matches without results
    include_in_report: bool = True  # Whether to include this match in PDF reports

    @validator('date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%d %b %Y")
            return v
        except ValueError:
            raise ValueError('Date must be in format "dd MMM yyyy" (e.g., "23 Oct 2025")')

    @validator('score')
    def validate_score(cls, v):
        if v is None:
            return v
        if ' - ' not in v:
            raise ValueError('Score must be in format "7 - 5"')
        try:
            parts = v.split(' - ')
            if len(parts) != 2:
                raise ValueError
            int(parts[0])
            int(parts[1])
            return v
        except (ValueError, IndexError):
            raise ValueError('Score must be in format "7 - 5"')

    @validator('brodie_goals', 'brodie_assists', 'minutes_played')
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError('Value must be non-negative')
        return v


class SeasonStats(BaseModel):
    matches: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals: int = 0
    assists: int = 0
    minutes: int = 0


class AppSettings(BaseModel):
    season_year: str = "2025/26"
    club_name: str = "Al Qadsiah U12"
    player_name: str = "Brodie Hardy"
    primary_color: str = "#B22222"  # Qadsiah red
    header_color: str = "#1F2937"   # Header grey
    footer_text: str = "FutureElite - Privacy First"
    show_logo: bool = False
    league_name: str = "Eastern Province U12 League 2025/26"
    
    # League groups
    group1_teams: List[str] = Field(default_factory=lambda: [
        "Winners Club", "Dhahran Sports", "Al-Qadsiah", "Al-Dhanna Academy", 
        "Kat Academy", "The Talented Player", "Generations of Excellence", 
        "Al-Ibtisam", "Al-Khaleej", "Al-Ettifaq", "Al-Salam"
    ])
    
    group2_teams: List[str] = Field(default_factory=lambda: [
        "Al-Huda", "Al-Moheet", "Al-Noor", "Mudhar Club", "Ashbal Al-Baraem", 
        "Al-Nojoom Al-Mudhee'na (The Shining Stars)", "H.S. Sport", "Meridiana", 
        "Khaled Mubarak Sports", "Generations Sports", "Aspire"
    ])
    
    # Physical data fields
    date_of_birth: Optional[str] = None  # Format: "dd MMM yyyy"
    height_cm: Optional[float] = None  # Height in centimeters
    weight_kg: Optional[float] = None  # Weight in kilograms
    phv_date: Optional[str] = None  # Peak Height Velocity date - Format: "dd MMM yyyy"
    phv_age: Optional[float] = None  # Peak Height Velocity age in years
    sprint_speed_ms: Optional[float] = None  # Sprint speed in m/s
    sprint_speed_kmh: Optional[float] = None  # Sprint speed in km/h (alternative to m/s)
    position: Optional[str] = None  # Playing position (e.g., "Forward", "Midfielder", "Defender", "Goalkeeper")
    dominant_foot: Optional[str] = None  # "Left", "Right", or "Both"
    vertical_jump_cm: Optional[float] = None  # Vertical jump height in cm
    agility_time_sec: Optional[float] = None  # Agility test time in seconds
    
    # Media and links
    player_photo_path: Optional[str] = None  # Path to player photo file
    highlight_reel_urls: Optional[List[str]] = Field(default_factory=list)  # List of highlight reel URLs
    social_media_links: Optional[Dict[str, str]] = Field(default_factory=dict)  # Dictionary of social media platform -> URL
    contact_email: Optional[str] = None  # Player/Parent contact email
    
    # Playing profile
    playing_profile: Optional[List[str]] = Field(default_factory=list)  # List of playing profile comments/bullet points
    
    # Performance metric comments/context
    performance_metric_comments: Optional[Dict[str, str]] = Field(default_factory=dict)  # Dictionary mapping metric names to contextual comments
    
    @validator('date_of_birth', 'phv_date')
    def validate_date_fields(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%d %b %Y")
            return v
        except ValueError:
            raise ValueError('Date must be in format "dd MMM yyyy" (e.g., "23 Oct 2005")')
    
    @validator('height_cm', 'weight_kg', 'phv_age', 'sprint_speed_ms', 'sprint_speed_kmh', 'vertical_jump_cm', 'agility_time_sec')
    def validate_positive_numeric(cls, v):
        if v is None:
            return v
        if v < 0:
            raise ValueError('Value must be non-negative')
        return v


class PhysicalMeasurement(BaseModel):
    """Historical physical measurement (height/weight) at a specific date"""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    date: str  # Format: "dd MMM yyyy"
    height_cm: Optional[float] = None  # Height in centimeters
    weight_kg: Optional[float] = None  # Weight in kilograms
    notes: Optional[str] = None  # Optional notes about the measurement
    include_in_report: bool = True  # Whether to include this measurement in PDF reports (all data kept for PHV calculation)
    
    @validator('date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%d %b %Y")
            return v
        except ValueError:
            raise ValueError('Date must be in format "dd MMM yyyy" (e.g., "23 Oct 2025")')
    
    @validator('height_cm', 'weight_kg')
    def validate_positive_numeric(cls, v):
        if v is None:
            return v
        if v < 0:
            raise ValueError('Value must be non-negative')
        return v


class Achievement(BaseModel):
    """Represents a key achievement or award"""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    title: str  # e.g., "Player of the Year", "Top Scorer", "Player of the Tournament"
    category: str  # e.g., "Season", "Tournament", "Match", "League"
    date: str  # Format: "dd MMM yyyy" - when the achievement was awarded
    season: Optional[str] = None  # e.g., "2025/26"
    description: Optional[str] = None  # Additional details about the achievement
    notes: Optional[str] = None  # Optional notes
    # Position-specific stats
    goals: Optional[int] = None  # Number of goals (for forwards/strikers)
    clean_sheets: Optional[int] = None  # Number of clean sheets (for defenders/goalkeepers)
    
    @validator('date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%d %b %Y")
            return v
        except ValueError:
            raise ValueError('Date must be in format "dd MMM yyyy" (e.g., "23 Oct 2025")')
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class ClubHistory(BaseModel):
    """Represents a club/team the player has been part of"""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    club_name: str  # Name of the club/team
    season: str  # Season(s) e.g., "2023/24", "2024/25 - 2025/26"
    age_group: Optional[str] = None  # e.g., "U10", "U12", "U14"
    position: Optional[str] = None  # Position played at this club
    achievements: Optional[str] = None  # Key achievements at this club
    notes: Optional[str] = None  # Additional notes
    
    @validator('club_name')
    def validate_club_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Club name cannot be empty')
        return v.strip()
    
    @validator('season')
    def validate_season(cls, v):
        if not v or not v.strip():
            raise ValueError('Season cannot be empty')
        return v.strip()


class PhysicalMetrics(BaseModel):
    """Historical physical performance metrics at a specific date"""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    date: str  # Format: "dd MMM yyyy"
    
    # Sprint metrics
    sprint_speed_ms: Optional[float] = None  # Sprint speed in m/s
    sprint_speed_kmh: Optional[float] = None  # Sprint speed in km/h
    sprint_10m_sec: Optional[float] = None  # 10m sprint time in seconds
    sprint_20m_sec: Optional[float] = None  # 20m sprint time in seconds
    sprint_30m_sec: Optional[float] = None  # 30m sprint time in seconds
    
    # Jump metrics
    vertical_jump_cm: Optional[float] = None  # Vertical jump height in cm
    standing_long_jump_cm: Optional[float] = None  # Standing long jump in cm
    countermovement_jump_cm: Optional[float] = None  # Countermovement jump in cm
    
    # Agility and speed
    agility_time_sec: Optional[float] = None  # Agility test time in seconds (e.g., 5-10-5 shuttle)
    yo_yo_test_level: Optional[float] = None  # Yo-Yo test level achieved
    beep_test_level: Optional[float] = None  # Beep test level achieved
    
    # Report inclusion flag
    include_in_report: bool = True  # Whether to include this metric in PDF reports (all data kept for calculations)
    
    # Strength metrics
    bench_press_kg: Optional[float] = None  # Bench press max in kg
    squat_kg: Optional[float] = None  # Squat max in kg
    deadlift_kg: Optional[float] = None  # Deadlift max in kg
    
    # Endurance
    vo2_max: Optional[float] = None  # VO2 max in ml/kg/min
    max_heart_rate: Optional[int] = None  # Maximum heart rate in bpm
    resting_heart_rate: Optional[int] = None  # Resting heart rate in bpm
    
    # Flexibility
    sit_and_reach_cm: Optional[float] = None  # Sit and reach test in cm
    
    # Other metrics
    notes: Optional[str] = None  # Optional notes about the test/measurement
    
    @validator('date')
    def validate_date(cls, v):
        """Parse and convert date from various formats to standard format"""
        if not v or not v.strip():
            raise ValueError('Date is required')
        
        v = v.strip()
        
        # Try standard format first
        try:
            datetime.strptime(v, "%d %b %Y")
            return v
        except ValueError:
            pass
        
        # Try multiple date formats and convert to standard format
        date_formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d",
            "%d %b %Y", "%d %B %Y",
            "%b %d, %Y", "%B %d, %Y",
            "%d/%m/%y", "%d-%m-%y"
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(v, fmt)
                return date_obj.strftime("%d %b %Y")
            except ValueError:
                continue
        
        raise ValueError('Date must be in format "dd MMM yyyy" (e.g., "23 Oct 2025") or "dd-mm-yyyy" (e.g., "23-10-2025")')
    
    @validator('sprint_speed_ms', 'sprint_speed_kmh', 'sprint_10m_sec', 'sprint_20m_sec', 'sprint_30m_sec',
               'vertical_jump_cm', 'standing_long_jump_cm', 'countermovement_jump_cm',
               'agility_time_sec', 'yo_yo_test_level', 'beep_test_level',
               'bench_press_kg', 'squat_kg', 'deadlift_kg', 'vo2_max', 'sit_and_reach_cm')
    def validate_positive_numeric(cls, v):
        if v is None:
            return v
        if v < 0:
            raise ValueError('Value must be non-negative')
        return v
    
    @validator('max_heart_rate', 'resting_heart_rate')
    def validate_heart_rate(cls, v):
        if v is None:
            return v
        if v < 0 or v > 250:
            raise ValueError('Heart rate must be between 0 and 250 bpm')
        return v


class TrainingCamp(BaseModel):
    """Represents a football training camp attended"""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    camp_name: str  # Name of the training camp
    organizer: str  # Organizing club/company (e.g., "Manchester United", "Barcelona Academy")
    location: str  # Location of the camp (city, country)
    start_date: str  # Format: "dd MMM yyyy" - when the camp started
    end_date: Optional[str] = None  # Format: "dd MMM yyyy" - when the camp ended
    duration_days: Optional[int] = None  # Number of days
    age_group: Optional[str] = None  # e.g., "U10", "U12", "U14"
    focus_area: Optional[str] = None  # e.g., "Technical Skills", "Tactical Awareness", "Goalkeeping"
    achievements: Optional[str] = None  # Key achievements or recognition at the camp
    notes: Optional[str] = None  # Additional notes about the experience
    
    @validator('camp_name')
    def validate_camp_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Camp name cannot be empty')
        return v.strip()
    
    @validator('organizer')
    def validate_organizer(cls, v):
        if not v or not v.strip():
            raise ValueError('Organizer cannot be empty')
        return v.strip()
    
    @validator('location')
    def validate_location(cls, v):
        if not v or not v.strip():
            raise ValueError('Location cannot be empty')
        return v.strip()
    
    @validator('start_date')
    def validate_start_date(cls, v):
        """Parse and convert date from various formats to standard format"""
        if not v or not v.strip():
            raise ValueError('Start date is required')
        
        v = v.strip()
        
        # Try standard format first
        try:
            datetime.strptime(v, "%d %b %Y")
            return v
        except ValueError:
            pass
        
        # Try multiple date formats and convert to standard format
        date_formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d",
            "%d %b %Y", "%d %B %Y",
            "%b %d, %Y", "%B %d, %Y",
            "%d/%m/%y", "%d-%m-%y"
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(v, fmt)
                return date_obj.strftime("%d %b %Y")
            except ValueError:
                continue
        
        raise ValueError('Start date must be in format "dd MMM yyyy" (e.g., "15 Jul 2025") or "dd-mm-yyyy" (e.g., "15-07-2025")')
    
    @validator('end_date')
    def validate_end_date(cls, v):
        """Parse and convert date from various formats to standard format"""
        if v is None or not v.strip():
            return None
        
        v = v.strip()
        
        # Try standard format first
        try:
            datetime.strptime(v, "%d %b %Y")
            return v
        except ValueError:
            pass
        
        # Try multiple date formats and convert to standard format
        date_formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d",
            "%d %b %Y", "%d %B %Y",
            "%b %d, %Y", "%B %d, %Y",
            "%d/%m/%y", "%d-%m-%y"
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(v, fmt)
                return date_obj.strftime("%d %b %Y")
            except ValueError:
                continue
        
        raise ValueError('End date must be in format "dd MMM yyyy" (e.g., "20 Jul 2025") or "dd-mm-yyyy" (e.g., "20-07-2025")')


class MatchData(BaseModel):
    matches: List[Match] = Field(default_factory=list)
    settings: AppSettings = Field(default_factory=AppSettings)


class User(BaseModel):
    """User account model"""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    username: str
    password_hash: str  # Hashed password (using werkzeug's generate_password_hash)
    email: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%d %b %Y"))
    is_active: bool = True
    
    @validator('username')
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if ' ' in v:
            raise ValueError('Username cannot contain spaces')
        return v


class SubscriptionStatus(str, Enum):
    """Subscription status enum"""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    NONE = "none"


class Subscription(BaseModel):
    """Subscription model"""
    user_id: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    status: SubscriptionStatus = SubscriptionStatus.NONE
    plan_id: Optional[str] = None  # Stripe price ID
    plan_name: Optional[str] = None  # e.g., "Monthly", "Annual"
    current_period_start: Optional[str] = None  # ISO format date
    current_period_end: Optional[str] = None  # ISO format date
    cancel_at_period_end: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%d %b %Y"))
    updated_at: str = Field(default_factory=lambda: datetime.now().strftime("%d %b %Y"))
    
    @validator('status', pre=True)
    def validate_status(cls, v):
        """Convert string status to enum if needed"""
        if isinstance(v, str):
            try:
                return SubscriptionStatus(v.lower())
            except ValueError:
                return SubscriptionStatus.NONE
        elif isinstance(v, SubscriptionStatus):
            return v
        else:
            return SubscriptionStatus.NONE


class Reference(BaseModel):
    """Reference model for contacts/references"""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    user_id: str
    name: str
    position: str  # e.g., "Head Coach", "Academy Director", "Scout"
    organization: Optional[str] = None  # e.g., "Manchester United FC", "FA"
    email: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None  # e.g., "Former Coach", "Current Manager"
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%d %b %Y"))
    updated_at: str = Field(default_factory=lambda: datetime.now().strftime("%d %b %Y"))

