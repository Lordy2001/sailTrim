"""
Plotting Manager for Navigation Data Visualization
Handles matplotlib plotting of time-series navigation data
"""

import matplotlib.pyplot as plt
from collections import deque
from datetime import datetime

class PlottingManager:
    def __init__(self, max_points=60):
        self.max_points = max_points
        
        # Initialize plot data storage
        self.plot_data = {
            'time': deque(maxlen=max_points),
            'sog': deque(maxlen=max_points),
            'cog': deque(maxlen=max_points),
            'true_wind_speed': deque(maxlen=max_points),
            'absolute_wind_direction': deque(maxlen=max_points)
        }
        
        # Create matplotlib figure
        self.fig, self.axes = plt.subplots(2, 2, figsize=(8, 6))
        self.fig.suptitle('5-minute Averages')
        
        # Configure plot styling
        plt.style.use('default')
        self.fig.patch.set_facecolor('white')
    
    def add_data_point(self, averages):
        """Add a new data point to the plots"""
        now = datetime.now()
        
        self.plot_data['time'].append(now)
        self.plot_data['sog'].append(averages.get('sog', 0))
        self.plot_data['cog'].append(averages.get('cog', 0))
        self.plot_data['true_wind_speed'].append(averages.get('true_wind_speed', 0))
        self.plot_data['absolute_wind_direction'].append(averages.get('absolute_wind_direction', 0))
    
    def update_plots(self):
        """Update all plots with current data"""
        # Clear all axes
        for ax in self.axes.flat:
            ax.clear()
        
        if len(self.plot_data['time']) > 1:
            times = list(self.plot_data['time'])
            
            # SOG plot
            self.axes[0,0].plot(times, list(self.plot_data['sog']), 'b-', linewidth=2)
            self.axes[0,0].set_title('Speed Over Ground (kts)', fontsize=10)
            self.axes[0,0].grid(True, alpha=0.3)
            self.axes[0,0].tick_params(axis='x', rotation=45, labelsize=8)
            self.axes[0,0].tick_params(axis='y', labelsize=8)
            
            # COG plot
            self.axes[0,1].plot(times, list(self.plot_data['cog']), 'g-', linewidth=2)
            self.axes[0,1].set_title('Course Over Ground (°)', fontsize=10)
            self.axes[0,1].grid(True, alpha=0.3)
            self.axes[0,1].tick_params(axis='x', rotation=45, labelsize=8)
            self.axes[0,1].tick_params(axis='y', labelsize=8)
            
            # True Wind Speed
            self.axes[1,0].plot(times, list(self.plot_data['true_wind_speed']), 'r-', linewidth=2)
            self.axes[1,0].set_title('True Wind Speed (kts)', fontsize=10)
            self.axes[1,0].grid(True, alpha=0.3)
            self.axes[1,0].tick_params(axis='x', rotation=45, labelsize=8)
            self.axes[1,0].tick_params(axis='y', labelsize=8)
            
            # Absolute Wind Direction
            self.axes[1,1].plot(times, list(self.plot_data['absolute_wind_direction']), 'm-', linewidth=2)
            self.axes[1,1].set_title('Absolute Wind Direction (°)', fontsize=10)
            self.axes[1,1].set_ylim(0, 360)
            self.axes[1,1].grid(True, alpha=0.3)
            self.axes[1,1].tick_params(axis='x', rotation=45, labelsize=8)
            self.axes[1,1].tick_params(axis='y', labelsize=8)
        
        # Adjust layout to prevent overlapping
        self.fig.tight_layout()
    
    def get_figure(self):
        """Get the matplotlib figure for embedding in UI"""
        return self.fig
    
    def clear_data(self):
        """Clear all plot data"""
        for key in self.plot_data:
            self.plot_data[key].clear()
    
    def set_max_points(self, max_points):
        """Change the maximum number of points to display"""
        self.max_points = max_points
        for key in self.plot_data:
            # Create new deque with new maxlen
            old_data = list(self.plot_data[key])
            self.plot_data[key] = deque(old_data[-max_points:], maxlen=max_points)
    
    def export_plot(self, filename):
        """Export current plot to file"""
        try:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"Error exporting plot: {e}")
            return False