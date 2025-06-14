"""
Main NMEA2000 Navigation Application
Uses modular libraries for parsing, data management, and visualization
"""

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

# Import our custom libraries
from nmea2000_parser import NMEA2000Parser
from data_averager import DataAverager
from tcp_client import NMEA2000TCPClient
from navigation_data import NavigationData
from plotting_manager import PlottingManager

class NMEA2000App(App):
    def build(self):
        self.title = "NMEA2000 Navigation Monitor"
        
        # Initialize components
        self.parser = NMEA2000Parser()
        self.averager = DataAverager()
        self.nav_data = NavigationData()
        self.plotting_manager = PlottingManager()
        
        # Initialize TCP client with callbacks
        self.tcp_client = NMEA2000TCPClient(
            message_callback=self.on_message_received,
            status_callback=self.on_status_change
        )
        
        # Create main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Connection section
        conn_layout = GridLayout(cols=4, size_hint_y=None, height=40)
        conn_layout.add_widget(Label(text='Server:', size_hint_x=0.15))
        self.server_input = TextInput(text='localhost', size_hint_x=0.25)
        conn_layout.add_widget(self.server_input)
        conn_layout.add_widget(Label(text='Port:', size_hint_x=0.1))
        self.port_input = TextInput(text='2000', size_hint_x=0.15)
        conn_layout.add_widget(self.port_input)
        self.connect_btn = Button(text='Connect', size_hint_x=0.15)
        self.connect_btn.bind(on_press=self.toggle_connection)
        conn_layout.add_widget(self.connect_btn)
        main_layout.add_widget(conn_layout)
        
        # Status section
        status_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.status_label = Label(text='Status: Disconnected', size_hint_x=0.7)
        status_layout.add_widget(self.status_label)
        self.log_label = Label(text='Messages: 0', size_hint_x=0.3)
        status_layout.add_widget(self.log_label)
        main_layout.add_widget(status_layout)
        
        # Data display section
        data_layout = BoxLayout(orientation='horizontal')
        
        # Left panel - Current data
        left_panel = self._create_navigation_panel()
        data_layout.add_widget(left_panel)
        
        # Center panel - Waypoint info and Wind Shifts
        center_panel = self._create_waypoint_panel()
        data_layout.add_widget(center_panel)
        
        # Right panel - Plot
        right_panel = self._create_plot_panel()
        data_layout.add_widget(right_panel)
        
        main_layout.add_widget(data_layout)
        
        # Schedule updates
        Clock.schedule_interval(self.update_display, 1.0)
        Clock.schedule_interval(self.update_plots, 10.0)
        
        return main_layout
    
    def _create_navigation_panel(self):
        """Create the navigation data display panel"""
        left_panel = BoxLayout(orientation='vertical', size_hint_x=0.4)
        left_panel.add_widget(Label(text='Current Navigation Data', 
                                  size_hint_y=None, height=30, bold=True))
        
        self.nav_labels = {}
        nav_data_items = ['COG', 'SOG', 'VMG', 'True Wind Speed', 'True Wind Angle', 
                         'App Wind Speed', 'App Wind Angle', 'Abs Wind Direction']
        
        for item in nav_data_items:
            self.nav_labels[item] = Label(text=f'{item}: --', size_hint_y=None, height=30)
            left_panel.add_widget(self.nav_labels[item])
        
        return left_panel
    
    def _create_waypoint_panel(self):
        """Create the waypoint and wind shift display panel"""
        center_panel = BoxLayout(orientation='vertical', size_hint_x=0.3)
        
        # Waypoint section
        center_panel.add_widget(Label(text='Waypoint Information', 
                                    size_hint_y=None, height=30, bold=True))
        
        self.waypoint_labels = {}
        waypoint_items = ['Current WP', 'Bearing to WP', 'Distance to WP', 
                         'Dest Latitude', 'Dest Longitude', 'Cross Track Error',
                         'Next WP', 'Course to Next']
        
        for item in waypoint_items:
            self.waypoint_labels[item] = Label(text=f'{item}: --', size_hint_y=None, height=25)
            center_panel.add_widget(self.waypoint_labels[item])
        
        # Wind shift section
        center_panel.add_widget(Label(text='Wind Shifts', 
                                    size_hint_y=None, height=30, bold=True))
        
        self.wind_shift_labels = {}
        wind_shift_periods = ['1 min', '5 min', '10 min']
        
        for period in wind_shift_periods:
            self.wind_shift_labels[period] = Label(text=f'{period}: --°', size_hint_y=None, height=30)
            center_panel.add_widget(self.wind_shift_labels[period])
        
        return center_panel
    
    def _create_plot_panel(self):
        """Create the plotting panel"""
        right_panel = BoxLayout(orientation='vertical', size_hint_x=0.3)
        
        # Add plot controls
        plot_controls = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        clear_btn = Button(text='Clear Plots', size_hint_x=0.5)
        clear_btn.bind(on_press=self.clear_plots)
        export_btn = Button(text='Export', size_hint_x=0.5)
        export_btn.bind(on_press=self.export_plots)
        plot_controls.add_widget(clear_btn)
        plot_controls.add_widget(export_btn)
        right_panel.add_widget(plot_controls)
        
        # Add matplotlib canvas
        self.canvas = FigureCanvasKivyAgg(self.plotting_manager.get_figure())
        right_panel.add_widget(self.canvas)
        
        return right_panel
    
    def toggle_connection(self, instance):
        """Toggle TCP connection"""
        if self.tcp_client.is_connected():
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        """Connect to TCP server"""
        server = self.server_input.text.strip()
        try:
            port = int(self.port_input.text.strip())
        except ValueError:
            self.on_status_change('Invalid port number')
            return
        
        if self.tcp_client.connect(server, port):
            self.connect_btn.text = 'Disconnect'
        
    def disconnect(self):
        """Disconnect from TCP server"""
        self.tcp_client.disconnect()
        self.connect_btn.text = 'Connect'
    
    def on_message_received(self, raw_data):
        """Callback for when a message is received"""
        # Parse the message
        parsed = self.parser.parse_message(raw_data)
        if not parsed:
            return
        
        # Process different message types
        self._process_parsed_message(parsed)
    
    def _process_parsed_message(self, parsed):
        """Process a parsed NMEA2000 message"""
        if parsed.get('type') == 'navigation':
            if 'cog' in parsed:
                self.nav_data.update_navigation(cog=parsed['cog'])
                self.averager.add_data('cog', parsed['cog'])
            if 'sog' in parsed:
                self.nav_data.update_navigation(sog=parsed['sog'])
                self.averager.add_data('sog', parsed['sog'])
                # Calculate VMG (simplified as SOG for this example)
                self.nav_data.update_navigation(vmg=parsed['sog'])
                self.averager.add_data('vmg', parsed['sog'])
        
        elif parsed.get('type') == 'wind':
            if parsed.get('reference') == 'true':
                self.nav_data.update_wind(true_speed=parsed['speed'], 
                                        true_angle=parsed['angle'])
                self.averager.add_data('true_wind_speed', parsed['speed'])
                self.averager.add_data('true_wind_angle', parsed['angle'])
                
                # Calculate absolute wind direction
                absolute_wind_dir = (parsed['angle'] + self.nav_data.current_cog) % 360
                self.averager.add_data('absolute_wind_direction', absolute_wind_dir)
                
            else:
                self.nav_data.update_wind(apparent_speed=parsed['speed'], 
                                        apparent_angle=parsed['angle'])
                self.averager.add_data('apparent_wind_speed', parsed['speed'])
                self.averager.add_data('apparent_wind_angle', parsed['angle'])
        
        elif parsed.get('type') == 'waypoint_nav':
            self.nav_data.update_waypoint(
                bearing=parsed.get('bearing_to_waypoint', 0),
                distance=parsed.get('distance_to_waypoint', 0)
            )
        
        elif parsed.get('type') == 'waypoint_info':
            self.nav_data.update_waypoint(
                current_wp=parsed.get('name', 'N/A'),
                waypoint_id=parsed.get('waypoint_id', 0)
            )
        
        elif parsed.get('type') == 'navigation_route_info':
            # Update destination waypoint coordinates and navigation info
            self.nav_data.update_waypoint(
                waypoint_id=parsed.get('waypoint_id', 0),
                bearing=parsed.get('bearing_to_waypoint', 0),
                distance=parsed.get('distance_to_waypoint', 0),
                dest_lat=parsed.get('destination_latitude', 0),
                dest_lon=parsed.get('destination_longitude', 0)
            )
            
            # Calculate course to next waypoint
            self.nav_data.calculate_course_to_next_waypoint()
        
        elif parsed.get('type') == 'cross_track_error':
            self.nav_data.update_waypoint(xte=parsed.get('xte', 0))
        
        elif parsed.get('type') == 'route_waypoint_database':
            # Update route information with waypoint coordinates
            self.nav_data.update_route(
                route_id=parsed.get('route_id', 0),
                waypoints_list=parsed.get('waypoints', [])
            )
        
        elif parsed.get('type') == 'position':
            self.nav_data.update_position(
                latitude=parsed.get('latitude', 0),
                longitude=parsed.get('longitude', 0)
            )
    
    def on_status_change(self, status):
        """Callback for status changes"""
        self.status_label.text = f'Status: {status}'
    
    def update_display(self, dt):
        """Update the display with current data"""
        # Update message counter
        self.log_label.text = f'Messages: {self.tcp_client.get_message_count()}'
        
        # Get averaged data
        averages = self.averager.get_all_averages()
        
        # Update navigation data display
        nav_summary = {
            'COG': averages.get('cog', 0),
            'SOG': averages.get('sog', 0),
            'VMG': averages.get('vmg', 0),
            'True Wind Speed': averages.get('true_wind_speed', 0),
            'True Wind Angle': averages.get('true_wind_angle', 0),
            'App Wind Speed': averages.get('apparent_wind_speed', 0),
            'App Wind Angle': averages.get('apparent_wind_angle', 0),
            'Abs Wind Direction': averages.get('absolute_wind_direction', 0)
        }
        
        for key, value in nav_summary.items():
            if key in ['COG', 'True Wind Angle', 'App Wind Angle', 'Abs Wind Direction']:
                self.nav_labels[key].text = f"{key}: {value:.1f}°"
            else:
                self.nav_labels[key].text = f"{key}: {value:.1f} kts"
        
        # Update waypoint information
        waypoint_summary = self.nav_data.get_waypoint_summary()
        
        self.waypoint_labels['Current WP'].text = f"Current WP: {waypoint_summary['Current WP']}"
        self.waypoint_labels['Bearing to WP'].text = f"Bearing to WP: {waypoint_summary['Bearing to WP']:.1f}°"
        self.waypoint_labels['Distance to WP'].text = f"Distance to WP: {waypoint_summary['Distance to WP']:.2f} nm"
        self.waypoint_labels['Dest Latitude'].text = f"Dest Latitude: {waypoint_summary['Dest Latitude']:.6f}°"
        self.waypoint_labels['Dest Longitude'].text = f"Dest Longitude: {waypoint_summary['Dest Longitude']:.6f}°"
        self.waypoint_labels['Cross Track Error'].text = f"Cross Track Error: {waypoint_summary['Cross Track Error']:.1f} m"
        self.waypoint_labels['Next WP'].text = f"Next WP: {waypoint_summary['Next WP']}"
        self.waypoint_labels['Course to Next'].text = f"Course to Next: {waypoint_summary['Course to Next']:.1f}°"
        
        # Update wind shift information
        wind_shift_1min = self.averager.get_wind_shift(1)
        wind_shift_5min = self.averager.get_wind_shift(5)
        wind_shift_10min = self.averager.get_wind_shift(10)
        
        self.wind_shift_labels['1 min'].text = f"1 min: {wind_shift_1min:+.1f}°"
        self.wind_shift_labels['5 min'].text = f"5 min: {wind_shift_5min:+.1f}°"
        self.wind_shift_labels['10 min'].text = f"10 min: {wind_shift_10min:+.1f}°"
    
    def update_plots(self, dt):
        """Update the plots with current averaged data"""
        averages = self.averager.get_all_averages()
        self.plotting_manager.add_data_point(averages)
        self.plotting_manager.update_plots()
        self.canvas.draw()
    
    def clear_plots(self, instance):
        """Clear all plot data"""
        self.plotting_manager.clear_data()
        self.plotting_manager.update_plots()
        self.canvas.draw()
    
    def export_plots(self, instance):
        """Export current plots to file"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"navigation_plots_{timestamp}.png"
        
        if self.plotting_manager.export_plot(filename):
            self.on_status_change(f'Plots exported to {filename}')
        else:
            self.on_status_change('Failed to export plots')
    
    def on_stop(self):
        """Called when the app is closing"""
        self.tcp_client.disconnect()

if __name__ == '__main__':
    NMEA2000App().run()