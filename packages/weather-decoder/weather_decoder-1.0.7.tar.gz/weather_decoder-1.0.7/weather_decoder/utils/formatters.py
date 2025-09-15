"""Formatting utilities for weather data"""

from typing import Dict


def format_wind(wind: Dict) -> str:
    """Format wind information into a readable string"""
    if wind.get('direction') == 'VRB':
        dir_text = "Variable"
    else:
        dir_text = f"{wind['direction']}°"
        
    speed_text = f"{wind['speed']} {wind['unit']}"
    
    if wind.get('gust'):
        speed_text += f", gusting to {wind['gust']} {wind['unit']}"
        
    if wind.get('variable_direction'):
        var_dir = wind['variable_direction']
        speed_text += f" (varying between {var_dir[0]}° and {var_dir[1]}°)"
        
    return f"{dir_text} at {speed_text}"


def format_visibility(visibility: Dict) -> str:
    """Format visibility information into a readable string"""
    if visibility.get('is_cavok'):
        return "CAVOK (Ceiling and Visibility OK)"
    
    vis_value = visibility['value']
    vis_unit = visibility['unit']
    
    if vis_value == 9999:
        result = "10 km or more"
    elif vis_unit == 'M' and vis_value >= 1000 and vis_value <= 9000:
        # Format meter values to km if 1000 or greater
        km_value = vis_value / 1000
        result = f"{km_value:.1f} km" if km_value % 1 != 0 else f"{int(km_value)} km"
    elif vis_value == 0 and visibility.get('is_less_than'):
        result = f"Less than {vis_value} {vis_unit}"
    elif visibility.get('is_greater_than'):
        if vis_unit == 'SM':
            result = f"Greater than {vis_value} {vis_unit}"
        else:
            # If meters and greater than 1000, convert to km
            if vis_value >= 1000:
                km_value = vis_value / 1000
                result = f"Greater than {km_value:.1f} km" if km_value % 1 != 0 else f"Greater than {int(km_value)} km"
            else:
                result = f"Greater than {vis_value} {vis_unit}"
    else:
        # Handle fractional statute miles
        if vis_unit == 'SM' and isinstance(vis_value, float):
            if vis_value.is_integer():
                result = f"{int(vis_value)} {vis_unit}"
            else:
                result = f"{vis_value} {vis_unit}"
        # Handle meters - convert to km if 1000 or greater
        elif vis_unit == 'M' and vis_value >= 1000:
            km_value = vis_value / 1000
            result = f"{km_value:.1f} km" if km_value % 1 != 0 else f"{int(km_value)} km"
        else:
            result = f"{vis_value} {vis_unit}"
    
    # Add NDV indicator if present (METAR specific)
    if visibility.get('ndv'):
        result += " (No Directional Variation)"
    
    return result


def format_temperature(temp_value: float) -> str:
    """Format temperature value"""
    return f"{temp_value}°C"


def format_pressure(pressure: Dict) -> str:
    """Format pressure information"""
    return f"{pressure['value']} {pressure['unit']}"


def format_sky_condition(sky: Dict) -> str:
    """Format a single sky condition"""
    if sky['type'] in ['CLR', 'SKC']:
        return "Clear skies"
    elif sky['type'] == 'NSC':
        return "No significant cloud"
    elif sky['type'] == 'NCD':
        return "No cloud detected"
    elif sky['type'] == 'VV':
        return f"Vertical visibility {sky['height']} feet"
    elif sky['type'] == '///':
        return f"Unknown cloud type at {sky['height']} feet"
    else:
        result = f"{sky['type']} clouds at {sky['height']} feet"
        if sky.get('cb'):
            result += " (CB)"
        elif sky.get('tcu'):
            result += " (TCU)"
        elif sky.get('unknown_type'):
            result += " (unknown type)"
        return result


def format_weather_group(weather: Dict) -> str:
    """Format a weather phenomena group"""
    parts = []
    
    if weather.get('intensity'):
        parts.append(weather['intensity'])
    
    if weather.get('descriptor'):
        parts.append(weather['descriptor'])
    
    if weather.get('phenomena'):
        parts.append(', '.join(weather['phenomena']))
    
    return ' '.join(parts) if parts else ""
