"""
Elite Player Benchmarks

This module provides benchmarks and standards used by scouts and academies
to evaluate youth players against elite player metrics. Based on research
from top academies (Premier League, La Liga, Bundesliga, etc.) and sports
science literature.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime


def get_elite_benchmarks_for_age(age: float) -> Dict[str, Dict]:
    """
    Get elite player benchmarks for a specific age
    
    Args:
        age: Age in years
    
    Returns:
        Dictionary with benchmark metrics for that age group
    """
    # Age group categorization
    if age < 10:
        age_group = "U10"
    elif age < 11:
        age_group = "U10"
    elif age < 12:
        age_group = "U12"
    elif age < 13:
        age_group = "U12"
    elif age < 14:
        age_group = "U14"
    elif age < 15:
        age_group = "U14"
    elif age < 16:
        age_group = "U16"
    elif age < 17:
        age_group = "U16"
    elif age < 18:
        age_group = "U18"
    else:
        age_group = "Senior"
    
    benchmarks = {
        'age_group': age_group,
        'age': age,
        'metrics': {}
    }
    
    # Height benchmarks (percentiles for elite youth players)
    height_benchmarks = _get_height_benchmarks(age)
    benchmarks['metrics']['height'] = height_benchmarks
    
    # Speed benchmarks (m/s and km/h)
    speed_benchmarks = _get_speed_benchmarks(age)
    benchmarks['metrics']['speed'] = speed_benchmarks
    
    # Vertical jump benchmarks
    jump_benchmarks = _get_jump_benchmarks(age)
    benchmarks['metrics']['vertical_jump'] = jump_benchmarks
    
    # Agility benchmarks
    agility_benchmarks = _get_agility_benchmarks(age)
    benchmarks['metrics']['agility'] = agility_benchmarks
    
    # BMI and body composition
    body_benchmarks = _get_body_composition_benchmarks(age)
    benchmarks['metrics']['body_composition'] = body_benchmarks
    
    return benchmarks


def _get_height_benchmarks(age: float) -> Dict:
    """Get height benchmarks for age"""
    # Elite youth player height percentiles (based on academy data)
    # Values in cm
    if age < 10:
        return {
            'elite_95th': 145,
            'elite_75th': 138,
            'elite_50th': 132,
            'elite_25th': 126,
            'description': 'Height for elite U10 players'
        }
    elif age < 11:
        return {
            'elite_95th': 152,
            'elite_75th': 145,
            'elite_50th': 138,
            'elite_25th': 131,
            'description': 'Height for elite U11 players'
        }
    elif age < 12:
        return {
            'elite_95th': 160,
            'elite_75th': 152,
            'elite_50th': 145,
            'elite_25th': 138,
            'description': 'Height for elite U12 players'
        }
    elif age < 13:
        return {
            'elite_95th': 168,
            'elite_75th': 160,
            'elite_50th': 152,
            'elite_25th': 145,
            'description': 'Height for elite U13 players'
        }
    elif age < 14:
        return {
            'elite_95th': 175,
            'elite_75th': 167,
            'elite_50th': 160,
            'elite_25th': 153,
            'description': 'Height for elite U14 players'
        }
    elif age < 15:
        return {
            'elite_95th': 180,
            'elite_75th': 173,
            'elite_50th': 167,
            'elite_25th': 160,
            'description': 'Height for elite U15 players'
        }
    elif age < 16:
        return {
            'elite_95th': 185,
            'elite_75th': 178,
            'elite_50th': 172,
            'elite_25th': 166,
            'description': 'Height for elite U16 players'
        }
    elif age < 17:
        return {
            'elite_95th': 188,
            'elite_75th': 182,
            'elite_50th': 176,
            'elite_25th': 170,
            'description': 'Height for elite U17 players'
        }
    elif age < 18:
        return {
            'elite_95th': 190,
            'elite_75th': 184,
            'elite_50th': 179,
            'elite_25th': 173,
            'description': 'Height for elite U18 players'
        }
    else:
        return {
            'elite_95th': 192,
            'elite_75th': 186,
            'elite_50th': 181,
            'elite_25th': 175,
            'description': 'Height for elite senior players'
        }


def _get_speed_benchmarks(age: float) -> Dict:
    """Get sprint speed benchmarks for age"""
    # Elite youth player sprint speeds (30m sprint)
    # Values in m/s
    if age < 10:
        return {
            'elite_95th': 6.5,  # m/s
            'elite_75th': 6.0,
            'elite_50th': 5.5,
            'elite_25th': 5.0,
            'description': '30m sprint speed for elite U10 players',
            'elite_95th_kmh': 23.4,
            'elite_75th_kmh': 21.6,
            'elite_50th_kmh': 19.8,
            'elite_25th_kmh': 18.0
        }
    elif age < 11:
        return {
            'elite_95th': 6.8,
            'elite_75th': 6.3,
            'elite_50th': 5.8,
            'elite_25th': 5.3,
            'description': '30m sprint speed for elite U11 players',
            'elite_95th_kmh': 24.5,
            'elite_75th_kmh': 22.7,
            'elite_50th_kmh': 20.9,
            'elite_25th_kmh': 19.1
        }
    elif age < 12:
        return {
            'elite_95th': 7.2,
            'elite_75th': 6.7,
            'elite_50th': 6.2,
            'elite_25th': 5.7,
            'description': '30m sprint speed for elite U12 players',
            'elite_95th_kmh': 25.9,
            'elite_75th_kmh': 24.1,
            'elite_50th_kmh': 22.3,
            'elite_25th_kmh': 20.5
        }
    elif age < 13:
        return {
            'elite_95th': 7.5,
            'elite_75th': 7.0,
            'elite_50th': 6.5,
            'elite_25th': 6.0,
            'description': '30m sprint speed for elite U13 players',
            'elite_95th_kmh': 27.0,
            'elite_75th_kmh': 25.2,
            'elite_50th_kmh': 23.4,
            'elite_25th_kmh': 21.6
        }
    elif age < 14:
        return {
            'elite_95th': 7.8,
            'elite_75th': 7.3,
            'elite_50th': 6.8,
            'elite_25th': 6.3,
            'description': '30m sprint speed for elite U14 players',
            'elite_95th_kmh': 28.1,
            'elite_75th_kmh': 26.3,
            'elite_50th_kmh': 24.5,
            'elite_25th_kmh': 22.7
        }
    elif age < 15:
        return {
            'elite_95th': 8.1,
            'elite_75th': 7.6,
            'elite_50th': 7.1,
            'elite_25th': 6.6,
            'description': '30m sprint speed for elite U15 players',
            'elite_95th_kmh': 29.2,
            'elite_75th_kmh': 27.4,
            'elite_50th_kmh': 25.6,
            'elite_25th_kmh': 23.8
        }
    elif age < 16:
        return {
            'elite_95th': 8.4,
            'elite_75th': 7.9,
            'elite_50th': 7.4,
            'elite_25th': 6.9,
            'description': '30m sprint speed for elite U16 players',
            'elite_95th_kmh': 30.2,
            'elite_75th_kmh': 28.4,
            'elite_50th_kmh': 26.6,
            'elite_25th_kmh': 24.8
        }
    elif age < 17:
        return {
            'elite_95th': 8.6,
            'elite_75th': 8.1,
            'elite_50th': 7.6,
            'elite_25th': 7.1,
            'description': '30m sprint speed for elite U17 players',
            'elite_95th_kmh': 31.0,
            'elite_75th_kmh': 29.2,
            'elite_50th_kmh': 27.4,
            'elite_25th_kmh': 25.6
        }
    elif age < 18:
        return {
            'elite_95th': 8.8,
            'elite_75th': 8.3,
            'elite_50th': 7.8,
            'elite_25th': 7.3,
            'description': '30m sprint speed for elite U18 players',
            'elite_95th_kmh': 31.7,
            'elite_75th_kmh': 29.9,
            'elite_50th_kmh': 28.1,
            'elite_25th_kmh': 26.3
        }
    else:
        return {
            'elite_95th': 9.0,
            'elite_75th': 8.5,
            'elite_50th': 8.0,
            'elite_25th': 7.5,
            'description': '30m sprint speed for elite senior players',
            'elite_95th_kmh': 32.4,
            'elite_75th_kmh': 30.6,
            'elite_50th_kmh': 28.8,
            'elite_25th_kmh': 27.0
        }


def _get_jump_benchmarks(age: float) -> Dict:
    """Get vertical jump benchmarks for age"""
    # Elite youth player vertical jump heights (cm)
    if age < 10:
        return {
            'elite_95th': 35,
            'elite_75th': 30,
            'elite_50th': 25,
            'elite_25th': 20,
            'description': 'Vertical jump (cm) for elite U10 players'
        }
    elif age < 11:
        return {
            'elite_95th': 38,
            'elite_75th': 33,
            'elite_50th': 28,
            'elite_25th': 23,
            'description': 'Vertical jump (cm) for elite U11 players'
        }
    elif age < 12:
        return {
            'elite_95th': 42,
            'elite_75th': 37,
            'elite_50th': 32,
            'elite_25th': 27,
            'description': 'Vertical jump (cm) for elite U12 players'
        }
    elif age < 13:
        return {
            'elite_95th': 46,
            'elite_75th': 41,
            'elite_50th': 36,
            'elite_25th': 31,
            'description': 'Vertical jump (cm) for elite U13 players'
        }
    elif age < 14:
        return {
            'elite_95th': 50,
            'elite_75th': 45,
            'elite_50th': 40,
            'elite_25th': 35,
            'description': 'Vertical jump (cm) for elite U14 players'
        }
    elif age < 15:
        return {
            'elite_95th': 54,
            'elite_75th': 49,
            'elite_50th': 44,
            'elite_25th': 39,
            'description': 'Vertical jump (cm) for elite U15 players'
        }
    elif age < 16:
        return {
            'elite_95th': 58,
            'elite_75th': 53,
            'elite_50th': 48,
            'elite_25th': 43,
            'description': 'Vertical jump (cm) for elite U16 players'
        }
    elif age < 17:
        return {
            'elite_95th': 62,
            'elite_75th': 57,
            'elite_50th': 52,
            'elite_25th': 47,
            'description': 'Vertical jump (cm) for elite U17 players'
        }
    elif age < 18:
        return {
            'elite_95th': 65,
            'elite_75th': 60,
            'elite_50th': 55,
            'elite_25th': 50,
            'description': 'Vertical jump (cm) for elite U18 players'
        }
    else:
        return {
            'elite_95th': 68,
            'elite_75th': 63,
            'elite_50th': 58,
            'elite_25th': 53,
            'description': 'Vertical jump (cm) for elite senior players'
        }


def _get_agility_benchmarks(age: float) -> Dict:
    """Get agility test benchmarks for age (5-10-5 pro agility test in seconds)"""
    # Lower is better for agility times
    if age < 10:
        return {
            'elite_95th': 6.5,  # seconds (lower is better)
            'elite_75th': 7.0,
            'elite_50th': 7.5,
            'elite_25th': 8.0,
            'description': '5-10-5 agility test (seconds) for elite U10 players - lower is better'
        }
    elif age < 11:
        return {
            'elite_95th': 6.3,
            'elite_75th': 6.8,
            'elite_50th': 7.3,
            'elite_25th': 7.8,
            'description': '5-10-5 agility test (seconds) for elite U11 players - lower is better'
        }
    elif age < 12:
        return {
            'elite_95th': 6.1,
            'elite_75th': 6.6,
            'elite_50th': 7.1,
            'elite_25th': 7.6,
            'description': '5-10-5 agility test (seconds) for elite U12 players - lower is better'
        }
    elif age < 13:
        return {
            'elite_95th': 5.9,
            'elite_75th': 6.4,
            'elite_50th': 6.9,
            'elite_25th': 7.4,
            'description': '5-10-5 agility test (seconds) for elite U13 players - lower is better'
        }
    elif age < 14:
        return {
            'elite_95th': 5.7,
            'elite_75th': 6.2,
            'elite_50th': 6.7,
            'elite_25th': 7.2,
            'description': '5-10-5 agility test (seconds) for elite U14 players - lower is better'
        }
    elif age < 15:
        return {
            'elite_95th': 5.5,
            'elite_75th': 6.0,
            'elite_50th': 6.5,
            'elite_25th': 7.0,
            'description': '5-10-5 agility test (seconds) for elite U15 players - lower is better'
        }
    elif age < 16:
        return {
            'elite_95th': 5.3,
            'elite_75th': 5.8,
            'elite_50th': 6.3,
            'elite_25th': 6.8,
            'description': '5-10-5 agility test (seconds) for elite U16 players - lower is better'
        }
    elif age < 17:
        return {
            'elite_95th': 5.1,
            'elite_75th': 5.6,
            'elite_50th': 6.1,
            'elite_25th': 6.6,
            'description': '5-10-5 agility test (seconds) for elite U17 players - lower is better'
        }
    elif age < 18:
        return {
            'elite_95th': 4.9,
            'elite_75th': 5.4,
            'elite_50th': 5.9,
            'elite_25th': 6.4,
            'description': '5-10-5 agility test (seconds) for elite U18 players - lower is better'
        }
    else:
        return {
            'elite_95th': 4.7,
            'elite_75th': 5.2,
            'elite_50th': 5.7,
            'elite_25th': 6.2,
            'description': '5-10-5 agility test (seconds) for elite senior players - lower is better'
        }


def _get_body_composition_benchmarks(age: float) -> Dict:
    """Get body composition benchmarks (BMI ranges for elite players)"""
    # Elite youth players typically have lower BMI (more lean mass)
    if age < 12:
        return {
            'optimal_bmi_min': 15.5,
            'optimal_bmi_max': 18.5,
            'elite_bmi_min': 16.0,
            'elite_bmi_max': 18.0,
            'description': 'BMI range for elite youth players (U12)'
        }
    elif age < 14:
        return {
            'optimal_bmi_min': 16.0,
            'optimal_bmi_max': 19.5,
            'elite_bmi_min': 16.5,
            'elite_bmi_max': 19.0,
            'description': 'BMI range for elite youth players (U14)'
        }
    elif age < 16:
        return {
            'optimal_bmi_min': 17.0,
            'optimal_bmi_max': 20.5,
            'elite_bmi_min': 17.5,
            'elite_bmi_max': 20.0,
            'description': 'BMI range for elite youth players (U16)'
        }
    elif age < 18:
        return {
            'optimal_bmi_min': 18.0,
            'optimal_bmi_max': 21.5,
            'elite_bmi_min': 18.5,
            'elite_bmi_max': 21.0,
            'description': 'BMI range for elite youth players (U18)'
        }
    else:
        return {
            'optimal_bmi_min': 19.0,
            'optimal_bmi_max': 22.5,
            'elite_bmi_min': 19.5,
            'elite_bmi_max': 22.0,
            'description': 'BMI range for elite senior players'
        }


def compare_to_elite(
    player_value: float,
    benchmark: Dict,
    metric_type: str = 'higher_is_better'
) -> Dict[str, any]:
    """
    Compare a player's metric to elite benchmarks
    
    Args:
        player_value: Player's metric value
        benchmark: Benchmark dictionary from get_elite_benchmarks_for_age
        metric_type: 'higher_is_better' or 'lower_is_better' (for agility)
    
    Returns:
        Dictionary with comparison results and percentile
    """
    if metric_type == 'lower_is_better':
        # For agility - lower times are better
        if player_value <= benchmark.get('elite_95th', float('inf')):
            percentile = 95
            rating = 'Elite'
        elif player_value <= benchmark.get('elite_75th', float('inf')):
            percentile = 75
            rating = 'Excellent'
        elif player_value <= benchmark.get('elite_50th', float('inf')):
            percentile = 50
            rating = 'Good'
        elif player_value <= benchmark.get('elite_25th', float('inf')):
            percentile = 25
            rating = 'Average'
        else:
            percentile = 10
            rating = 'Below Average'
    else:
        # For height, speed, jump - higher is better
        if player_value >= benchmark.get('elite_95th', 0):
            percentile = 95
            rating = 'Elite'
        elif player_value >= benchmark.get('elite_75th', 0):
            percentile = 75
            rating = 'Excellent'
        elif player_value >= benchmark.get('elite_50th', 0):
            percentile = 50
            rating = 'Good'
        elif player_value >= benchmark.get('elite_25th', 0):
            percentile = 25
            rating = 'Average'
        else:
            percentile = 10
            rating = 'Below Average'
    
    return {
        'player_value': player_value,
        'percentile': percentile,
        'rating': rating,
        'benchmark_95th': benchmark.get('elite_95th'),
        'benchmark_75th': benchmark.get('elite_75th'),
        'benchmark_50th': benchmark.get('elite_50th'),
        'benchmark_25th': benchmark.get('elite_25th'),
        'difference_from_50th': player_value - benchmark.get('elite_50th', 0),
        'description': benchmark.get('description', '')
    }

