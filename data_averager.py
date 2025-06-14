"""
Data Averaging and Wind Shift Calculation Library
Handles time-windowed averaging of navigation data and wind shift calculations
"""

from datetime import datetime, timedelta
from collections import deque

class DataAverager:
    def __init__(self, window_minutes=5):
        self.window = timedelta(minutes=window_minutes)
        self.data = {
            'vmg': deque(),
            'cog': deque(),
            'sog': deque(),
            'true_wind_speed': deque(),
            'true_wind_angle': deque(),
            'apparent_wind_speed': deque(),
            'apparent_wind_angle': deque(),
            'absolute_wind_direction': deque(),
            'timestamps': deque()
        }
    
    def add_data(self, data_type, value, timestamp=None):
        """Add a data point to the averaging window"""
        if timestamp is None:
            timestamp = datetime.now()
        
        if data_type in self.data:
            self.data[data_type].append(value)
            self.data['timestamps'].append(timestamp)
            self._cleanup_old_data()
    
    def _cleanup_old_data(self):
        """Remove data points outside the time window"""
        cutoff = datetime.now() - self.window
        while self.data['timestamps'] and self.data['timestamps'][0] < cutoff:
            self.data['timestamps'].popleft()
            for key in self.data:
                if key != 'timestamps' and self.data[key]:
                    self.data[key].popleft()
    
    def get_average(self, data_type):
        """Get the average value for a specific data type"""
        if data_type in self.data and self.data[data_type]:
            return sum(self.data[data_type]) / len(self.data[data_type])
        return 0
    
    def get_all_averages(self):
        """Get averages for all data types"""
        return {key: self.get_average(key) for key in self.data if key != 'timestamps'}
    
    def get_wind_shift(self, minutes):
        """Calculate wind shift over specified time period"""
        if 'absolute_wind_direction' not in self.data or not self.data['absolute_wind_direction']:
            return 0
            
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        # Find values within the time window
        wind_values = []
        for i, timestamp in enumerate(self.data['timestamps']):
            if timestamp >= cutoff and i < len(self.data['absolute_wind_direction']):
                wind_values.append(self.data['absolute_wind_direction'][i])
        
        if len(wind_values) < 2:
            return 0
        
        # Calculate the difference between current and oldest value in the window
        # Handle circular nature of wind direction (0-360 degrees)
        current_wind = wind_values[-1]
        old_wind = wind_values[0]
        
        diff = current_wind - old_wind
        
        # Normalize to -180 to +180 range
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
            
        return diff
    
    def get_data_count(self):
        """Get the number of data points in the current window"""
        return len(self.data['timestamps'])
    
    def clear_all_data(self):
        """Clear all stored data"""
        for key in self.data:
            self.data[key].clear()