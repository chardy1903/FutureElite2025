"""
Peak Height Velocity (PHV) Calculator

PHV is the period of maximum growth velocity during puberty, typically occurring 
between ages 11-14 in boys. This calculator uses longitudinal height data to 
determine PHV date and age.

The calculation method:
1. Calculate growth velocity between consecutive measurements
2. Identify the maximum velocity (PHV)
3. Determine the date and age at which PHV occurred
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from .models import PhysicalMeasurement


def calculate_age_at_date(date_of_birth: str, measurement_date: str) -> float:
    """
    Calculate age in years at a given date
    
    Args:
        date_of_birth: Date of birth in "dd MMM yyyy" format
        measurement_date: Measurement date in "dd MMM yyyy" format
    
    Returns:
        Age in years as a float
    """
    try:
        dob = datetime.strptime(date_of_birth, "%d %b %Y")
        meas_date = datetime.strptime(measurement_date, "%d %b %Y")
        delta = meas_date - dob
        return delta.days / 365.25
    except (ValueError, TypeError):
        return 0.0


def days_between_dates(date1: str, date2: str) -> float:
    """
    Calculate days between two dates
    
    Args:
        date1: First date in "dd MMM yyyy" format
        date2: Second date in "dd MMM yyyy" format
    
    Returns:
        Number of days as a float
    """
    try:
        d1 = datetime.strptime(date1, "%d %b %Y")
        d2 = datetime.strptime(date2, "%d %b %Y")
        delta = abs((d2 - d1).days)
        return float(delta) if delta > 0 else 1.0  # Minimum 1 day to avoid division by zero
    except (ValueError, TypeError):
        return 1.0


def calculate_growth_velocity(
    measurement1: PhysicalMeasurement,
    measurement2: PhysicalMeasurement
) -> Optional[Dict[str, float]]:
    """
    Calculate growth velocity between two measurements
    
    Args:
        measurement1: First measurement (earlier)
        measurement2: Second measurement (later)
    
    Returns:
        Dictionary with velocity data or None if insufficient data
    """
    if not measurement1.height_cm or not measurement2.height_cm:
        return None
    
    days = days_between_dates(measurement1.date, measurement2.date)
    if days < 1:
        return None
    
    height_change = measurement2.height_cm - measurement1.height_cm
    velocity_cm_per_day = height_change / days
    velocity_cm_per_year = velocity_cm_per_day * 365.25
    
    # Calculate midpoint date for velocity assignment
    try:
        d1 = datetime.strptime(measurement1.date, "%d %b %Y")
        d2 = datetime.strptime(measurement2.date, "%d %b %Y")
        midpoint = d1 + (d2 - d1) / 2
        midpoint_date = midpoint.strftime("%d %b %Y")
    except (ValueError, TypeError):
        midpoint_date = measurement1.date
    
    return {
        'velocity_cm_per_year': velocity_cm_per_year,
        'velocity_cm_per_day': velocity_cm_per_day,
        'height_change': height_change,
        'days': days,
        'midpoint_date': midpoint_date,
        'start_date': measurement1.date,
        'end_date': measurement2.date,
        'start_height': measurement1.height_cm,
        'end_height': measurement2.height_cm
    }


def calculate_phv(
    measurements: List[PhysicalMeasurement],
    date_of_birth: Optional[str] = None
) -> Optional[Dict[str, any]]:
    """
    Calculate Peak Height Velocity (PHV) from historical measurements
    
    Args:
        measurements: List of physical measurements sorted by date
        date_of_birth: Date of birth in "dd MMM yyyy" format (optional, for age calculation)
    
    Returns:
        Dictionary with PHV results or None if insufficient data
    """
    if not measurements or len(measurements) < 2:
        return None
    
    # Filter measurements with height data and sort by date
    valid_measurements = [
        m for m in measurements 
        if m.height_cm is not None
    ]
    
    if len(valid_measurements) < 2:
        return None
    
    # Sort by date
    try:
        valid_measurements.sort(
            key=lambda m: datetime.strptime(m.date, "%d %b %Y")
        )
    except (ValueError, TypeError):
        return None
    
    # Calculate velocities between consecutive measurements
    velocities = []
    for i in range(len(valid_measurements) - 1):
        velocity = calculate_growth_velocity(
            valid_measurements[i],
            valid_measurements[i + 1]
        )
        if velocity:
            # Filter out unrealistic velocities from very short intervals
            # Minimum 30 days between measurements for reliable velocity calculation
            if velocity['days'] >= 30:
                # Cap velocity at reasonable maximum (15 cm/year for boys)
                # Very high velocities are usually measurement errors or very short intervals
                if velocity['velocity_cm_per_year'] <= 15.0:
                    velocities.append(velocity)
                else:
                    # If velocity is too high, it's likely a measurement error
                    # Skip this interval
                    continue
    
    if not velocities:
        return None
    
    # Find maximum velocity (PHV)
    # Cap at reasonable maximum (12 cm/year is typical peak for boys)
    max_velocity = max(velocities, key=lambda v: v['velocity_cm_per_year'])
    
    # Validate and cap PHV velocity at realistic maximum
    if max_velocity['velocity_cm_per_year'] > 12.0:
        # If calculated PHV is unrealistically high, cap it at 12 cm/year
        # This prevents prediction errors from measurement outliers
        max_velocity['velocity_cm_per_year'] = min(max_velocity['velocity_cm_per_year'], 12.0)
        max_velocity['velocity_cm_per_day'] = max_velocity['velocity_cm_per_year'] / 365.25
    
    # Calculate PHV date (midpoint of the interval with max velocity)
    phv_date = max_velocity['midpoint_date']
    
    # Calculate PHV age if date of birth provided
    phv_age = None
    if date_of_birth:
        phv_age = calculate_age_at_date(date_of_birth, phv_date)
    
    return {
        'phv_date': phv_date,
        'phv_age': phv_age,
        'phv_velocity_cm_per_year': max_velocity['velocity_cm_per_year'],
        'phv_velocity_cm_per_day': max_velocity['velocity_cm_per_day'],
        'calculation_based_on_measurements': len(valid_measurements),
        'growth_intervals': len(velocities),
        'velocity_details': velocities
    }


def estimate_phv_from_minimal_data(
    current_height: float,
    current_age: float,
    date_of_birth: Optional[str] = None
) -> Optional[Dict[str, any]]:
    """
    Estimate PHV using minimal data and statistical models
    
    Note: This is a less accurate method. For accurate PHV calculation,
    longitudinal height data is strongly recommended.
    
    Based on typical growth patterns:
    - Boys typically reach PHV around age 13.5 (range 11-15)
    - Growth velocity peaks at ~9-10 cm/year during PHV
    
    Args:
        current_height: Current height in cm
        current_age: Current age in years
        date_of_birth: Date of birth (for date calculation)
    
    Returns:
        Dictionary with estimated PHV results
    """
    # Statistical estimate - boys typically reach PHV at 13.5 years
    estimated_phv_age = 13.5
    
    # If current age is significantly past typical PHV, adjust estimate
    if current_age > 15:
        # Likely past PHV
        estimated_phv_age = current_age - 1.5  # Estimate 1.5 years ago
    elif current_age < 11:
        # Likely before PHV
        estimated_phv_age = current_age + 2.0  # Estimate in future
    
    if date_of_birth:
        try:
            dob = datetime.strptime(date_of_birth, "%d %b %Y")
            phv_datetime = dob + timedelta(days=int(estimated_phv_age * 365.25))
            phv_date = phv_datetime.strftime("%d %b %Y")
        except (ValueError, TypeError):
            phv_date = None
    else:
        phv_date = None
    
    return {
        'phv_date': phv_date,
        'phv_age': estimated_phv_age,
        'phv_velocity_cm_per_year': 9.5,  # Typical peak velocity
        'calculation_method': 'statistical_estimate',
        'accuracy_note': 'This is an estimate. For accurate PHV, add historical height measurements.'
    }


def validate_measurements_for_phv(measurements: List[PhysicalMeasurement]) -> Dict[str, any]:
    """
    Validate and provide feedback on measurements for PHV calculation
    
    Returns:
        Dictionary with validation results and recommendations
    """
    valid = [m for m in measurements if m.height_cm is not None]
    
    if len(valid) < 2:
        return {
            'valid': False,
            'message': 'At least 2 height measurements are required for PHV calculation',
            'recommendation': 'Add more historical height measurements'
        }
    
    # Check time span
    try:
        dates = [datetime.strptime(m.date, "%d %b %Y") for m in valid]
        dates.sort()
        span_days = (dates[-1] - dates[0]).days
        span_years = span_days / 365.25
        
        if span_years < 1.0:
            return {
                'valid': True,
                'warning': True,
                'message': f'Only {span_years:.1f} years of data. More measurements over a longer period would improve accuracy.',
                'recommendation': 'Add measurements spanning at least 2-3 years for better accuracy'
            }
        
        # Check measurement frequency
        avg_interval = span_days / (len(valid) - 1)
        if avg_interval > 180:  # More than 6 months between measurements
            return {
                'valid': True,
                'warning': True,
                'message': 'Measurements are spaced far apart. More frequent measurements would improve accuracy.',
                'recommendation': 'Aim for measurements every 3-6 months during growth years'
            }
        
        return {
            'valid': True,
            'message': f'{len(valid)} measurements spanning {span_years:.1f} years. Good for PHV calculation.'
        }
    
    except (ValueError, TypeError):
        return {
            'valid': False,
            'message': 'Invalid date formats in measurements',
            'recommendation': 'Check date formats'
        }


def calculate_predicted_adult_height(
    measurements: List[PhysicalMeasurement],
    date_of_birth: Optional[str] = None,
    current_age: Optional[float] = None,
    phv_result: Optional[Dict] = None
) -> Optional[Dict[str, any]]:
    """
    Calculate predicted adult height using multiple methods for accuracy
    
    Methods used:
    1. Growth velocity method (if PHV data available)
    2. Khamis-Roche method (if age and current height available)
    3. Mid-parental height method (if parent heights available - not implemented here)
    4. Growth curve projection (if multiple measurements available)
    
    Args:
        measurements: List of physical measurements
        date_of_birth: Date of birth in "dd MMM yyyy" format
        current_age: Current age in years (optional, calculated if date_of_birth provided)
        phv_result: PHV calculation result (optional, calculated if not provided)
    
    Returns:
        Dictionary with predicted height results from multiple methods
    """
    if not measurements:
        return None
    
    # Get valid height measurements
    valid_measurements = [m for m in measurements if m.height_cm is not None]
    if not valid_measurements:
        return None
    
    # Sort by date
    try:
        valid_measurements.sort(key=lambda m: datetime.strptime(m.date, "%d %b %Y"))
    except (ValueError, TypeError):
        return None
    
    # Get most recent measurement
    latest_measurement = valid_measurements[-1]
    current_height = latest_measurement.height_cm
    latest_date = latest_measurement.date
    
    # Calculate current age if not provided
    if current_age is None and date_of_birth:
        current_age = calculate_age_at_date(date_of_birth, latest_date)
    
    if current_age is None:
        return None
    
    predictions = {}
    methods_used = []
    
    # Method 1: Growth Velocity Method (if PHV available)
    if phv_result and phv_result.get('phv_age') is not None:
        phv_age = phv_result['phv_age']
        phv_velocity = phv_result.get('phv_velocity_cm_per_year', 0)
        
        # Boys typically reach 98% of adult height by age 18
        # Growth after PHV follows a deceleration curve
        # Using Tanner's growth model: remaining growth = (18 - current_age) * deceleration_factor
        if current_age < 18:
            years_remaining = 18 - current_age
            
            # Deceleration factor based on how far past PHV
            if current_age > phv_age:
                # Past PHV - growth decelerating
                years_since_phv = current_age - phv_age
                # Growth velocity decreases exponentially after PHV
                # Typical: 8-10 cm/year at PHV, ~1-2 cm/year by age 18
                if years_since_phv < 1:
                    remaining_velocity = phv_velocity * 0.6  # 60% of peak
                elif years_since_phv < 2:
                    remaining_velocity = phv_velocity * 0.3  # 30% of peak
                else:
                    remaining_velocity = max(1.0, phv_velocity * 0.15)  # 15% of peak, min 1 cm/year
            else:
                # Before PHV - still accelerating
                years_to_phv = phv_age - current_age
                if years_to_phv < 0.5:
                    remaining_velocity = phv_velocity * 0.8  # Approaching PHV
                else:
                    remaining_velocity = phv_velocity * 0.5  # Pre-PHV growth
            
            # Cap remaining velocity at reasonable maximum (5 cm/year max after PHV)
            remaining_velocity = min(remaining_velocity, 5.0)
            
            predicted_growth = remaining_velocity * years_remaining
            predicted_height_velocity = current_height + predicted_growth
            
            # Cap predicted height at realistic maximum (220 cm / 7'2.5")
            # This prevents unrealistic predictions from data errors
            predicted_height_velocity = min(predicted_height_velocity, 220.0)
            
            predictions['growth_velocity_method'] = {
                'predicted_height_cm': round(predicted_height_velocity, 1),
                'confidence': 'high' if len(valid_measurements) >= 4 else 'medium',
                'method': 'Growth Velocity (PHV-based)'
            }
            methods_used.append('growth_velocity')
    
    # Method 2: Khamis-Roche Method (simplified)
    # This method uses current height, age, and weight
    # Full Khamis-Roche requires parent heights, but we can use a simplified version
    if current_age >= 4 and current_age <= 18:
        # Simplified Khamis-Roche: uses age and current height
        # Boys: predicted height = current_height / (0.92 - 0.002 * age) for ages 4-18
        # More accurate formula for boys 4-18 years
        if current_age < 9:
            # Pre-pubertal: use different coefficient
            khamis_factor = 0.90 - 0.001 * current_age
        elif current_age < 13:
            # Early puberty
            khamis_factor = 0.88 - 0.001 * current_age
        else:
            # Mid-late puberty
            khamis_factor = 0.85 - 0.0005 * current_age
        
        if khamis_factor > 0:
            predicted_height_khamis = current_height / khamis_factor
            # Cap at realistic maximum
            predicted_height_khamis = min(predicted_height_khamis, 220.0)
            predictions['khamis_roche_method'] = {
                'predicted_height_cm': round(predicted_height_khamis, 1),
                'confidence': 'medium',
                'method': 'Khamis-Roche (Simplified)'
            }
            methods_used.append('khamis_roche')
    
    # Method 3: Growth Curve Projection (if multiple measurements)
    if len(valid_measurements) >= 3:
        # Calculate average growth velocity over recent period
        recent_measurements = valid_measurements[-3:]  # Last 3 measurements
        velocities = []
        
        for i in range(len(recent_measurements) - 1):
            vel = calculate_growth_velocity(recent_measurements[i], recent_measurements[i + 1])
            if vel:
                velocities.append(vel['velocity_cm_per_year'])
        
        if velocities:
            avg_velocity = sum(velocities) / len(velocities)
            
            # Project forward with deceleration
            years_to_18 = 18 - current_age
            if years_to_18 > 0:
                # Apply deceleration: growth slows as approaching adult height
                # Use exponential decay model
                deceleration_factor = 0.7 ** min(years_to_18, 3)  # Decelerate over next 3 years
                # Cap average velocity at reasonable maximum
                avg_velocity = min(avg_velocity, 8.0)
                
                projected_velocity = avg_velocity * deceleration_factor
                predicted_growth = projected_velocity * years_to_18
                predicted_height_curve = current_height + predicted_growth
                
                # Cap at realistic maximum
                predicted_height_curve = min(predicted_height_curve, 220.0)
                
                predictions['growth_curve_method'] = {
                    'predicted_height_cm': round(predicted_height_curve, 1),
                    'confidence': 'high' if len(valid_measurements) >= 5 else 'medium',
                    'method': 'Growth Curve Projection'
                }
                methods_used.append('growth_curve')
    
    if not predictions:
        return None
    
    # Calculate weighted average of all methods
    weights = {
        'growth_velocity': 0.4,  # Highest weight if PHV available
        'khamis_roche': 0.3,
        'growth_curve': 0.3
    }
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for method, weight in weights.items():
        if method in predictions:
            weighted_sum += predictions[method]['predicted_height_cm'] * weight
            total_weight += weight
    
    if total_weight > 0:
        final_prediction = weighted_sum / total_weight
    else:
        # Fallback: simple average
        heights = [p['predicted_height_cm'] for p in predictions.values()]
        final_prediction = sum(heights) / len(heights)
    
    # Cap final prediction at realistic maximum (220 cm / 7'2.5")
    # This prevents unrealistic predictions from any calculation method
    final_prediction = min(final_prediction, 220.0)
    
    # Also ensure minimum reasonable height (150 cm / 4'11")
    final_prediction = max(final_prediction, 150.0)
    
    return {
        'predicted_adult_height_cm': round(final_prediction, 1),
        'predicted_adult_height_ft_in': _cm_to_ft_in(final_prediction),
        'methods': predictions,
        'methods_used': methods_used,
        'current_height_cm': current_height,
        'current_age': current_age,
        'confidence': 'high' if len(methods_used) >= 2 else 'medium'
    }


def _cm_to_ft_in(cm: float) -> str:
    """Convert centimeters to feet and inches"""
    total_inches = cm / 2.54
    feet = int(total_inches // 12)
    inches = round(total_inches % 12)
    return f"{feet}'{inches}\""





