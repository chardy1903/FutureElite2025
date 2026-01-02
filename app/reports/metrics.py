"""
Standardized metric calculations for all reports.

All metrics must be calculated consistently across reports using these functions.
"""

from typing import List, Optional
from .types import Match, Player


class PlayerMetrics:
    """Calculated metrics for a player based on their matches"""
    
    def __init__(self, matches: List[Match]):
        self.matches = matches
        self._calculate_all()
    
    def _calculate_all(self):
        """Calculate all metrics"""
        # Basic totals
        self.totalMatches = len(self.matches)
        self.totalMinutes = sum(m.minutesPlayed for m in self.matches)
        self.totalGoals = sum(m.goals for m in self.matches)
        self.totalAssists = sum(m.assists for m in self.matches)
        self.totalContributions = self.totalGoals + self.totalAssists
        
        # Per-match metrics
        if self.totalMatches > 0:
            self.goalsPerMatch = round(self.totalGoals / self.totalMatches, 2)
            self.assistsPerMatch = round(self.totalAssists / self.totalMatches, 2)
            self.contributionsPerMatch = round(self.totalContributions / self.totalMatches, 2)
        else:
            self.goalsPerMatch = 0.0
            self.assistsPerMatch = 0.0
            self.contributionsPerMatch = 0.0
        
        # Per-60 metrics
        if self.totalMinutes > 0:
            self.goalsPer60 = round((self.totalGoals / self.totalMinutes) * 60, 2)
            self.assistsPer60 = round((self.totalAssists / self.totalMinutes) * 60, 2)
            self.contributionsPer60 = round((self.totalContributions / self.totalMinutes) * 60, 2)
        else:
            self.goalsPer60 = 0.0
            self.assistsPer60 = 0.0
            self.contributionsPer60 = 0.0
        
        # Minutes per goal/contribution
        if self.totalGoals > 0:
            self.minutesPerGoal = round(self.totalMinutes / self.totalGoals)
        else:
            self.minutesPerGoal = None  # "N/A"
        
        if self.totalContributions > 0:
            self.minutesPerContribution = round(self.totalMinutes / self.totalContributions)
        else:
            self.minutesPerContribution = None  # "N/A"
        
        # Match involvement
        self.matchesWithGoal = sum(1 for m in self.matches if m.goals > 0)
        self.matchesWithAssist = sum(1 for m in self.matches if m.assists > 0)
        self.matchesWithContribution = sum(1 for m in self.matches if (m.goals + m.assists) > 0)
        
        # Goal involvement rate
        if self.totalMatches > 0:
            self.goalInvolvementRate = round((self.matchesWithContribution / self.totalMatches) * 100, 1)
        else:
            self.goalInvolvementRate = 0.0


def calculate_metrics(matches: List[Match]) -> PlayerMetrics:
    """
    Calculate all standardized metrics for a list of matches.
    
    Args:
        matches: List of Match objects
        
    Returns:
        PlayerMetrics object with all calculated metrics
    """
    return PlayerMetrics(matches)


def get_top_performances(matches: List[Match], top_n: int = 3) -> List[Match]:
    """
    Get top N performances by contributions (goals + assists).
    
    Tie-breaker order:
    1. Most contributions (goals + assists)
    2. Lower minutes played (better efficiency)
    3. Most recent date
    
    Args:
        matches: List of Match objects
        top_n: Number of top performances to return
        
    Returns:
        List of top N Match objects, sorted by performance
    """
    if not matches:
        return []
    
    # Filter matches with contributions
    matches_with_contributions = [m for m in matches if (m.goals + m.assists) > 0]
    
    if not matches_with_contributions:
        return []
    
    # Sort by: contributions (desc), minutes (asc), date (desc)
    def sort_key(m: Match):
        contributions = m.goals + m.assists
        # Parse date for sorting (ISO format: YYYY-MM-DD)
        try:
            from datetime import datetime
            date_val = datetime.fromisoformat(m.date.replace('Z', '+00:00').split('T')[0])
            date_timestamp = date_val.timestamp()
        except:
            date_timestamp = 0
        
        # Return tuple for sorting: (-contributions, minutes, -date_timestamp)
        # Negative for descending order
        return (-contributions, m.minutesPlayed, -date_timestamp)
    
    sorted_matches = sorted(matches_with_contributions, key=sort_key)
    return sorted_matches[:top_n]


def get_recent_form(matches: List[Match], last_n: int = 5) -> dict:
    """
    Get recent form statistics from last N matches.
    
    Args:
        matches: List of Match objects
        last_n: Number of recent matches to analyze
        
    Returns:
        Dictionary with 'goals', 'assists', 'matches' keys
    """
    if not matches:
        return {'goals': 0, 'assists': 0, 'matches': 0}
    
    # Sort by date descending (most recent first)
    def date_key(m: Match):
        try:
            from datetime import datetime
            date_val = datetime.fromisoformat(m.date.replace('Z', '+00:00').split('T')[0])
            return date_val
        except:
            from datetime import datetime
            return datetime.min
    
    sorted_matches = sorted(matches, key=date_key, reverse=True)
    recent_matches = sorted_matches[:last_n]
    
    total_goals = sum(m.goals for m in recent_matches)
    total_assists = sum(m.assists for m in recent_matches)
    
    return {
        'goals': total_goals,
        'assists': total_assists,
        'matches': len(recent_matches)
    }


def calculate_match_results(matches: List[Match]) -> dict:
    """
    Calculate wins, draws, losses from matches.
    Only includes matches where scoreFor and scoreAgainst are available.
    
    Args:
        matches: List of Match objects
        
    Returns:
        Dictionary with 'wins', 'draws', 'losses', 'total' keys
    """
    wins = 0
    draws = 0
    losses = 0
    
    for match in matches:
        if match.scoreFor is not None and match.scoreAgainst is not None:
            if match.scoreFor > match.scoreAgainst:
                wins += 1
            elif match.scoreFor == match.scoreAgainst:
                draws += 1
            else:
                losses += 1
    
    return {
        'wins': wins,
        'draws': draws,
        'losses': losses,
        'total': wins + draws + losses
    }

