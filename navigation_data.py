"""
Navigation Data Storage and Management
Handles current navigation state, waypoint information, and route data
"""

class NavigationData:
    def __init__(self):
        # Navigation state
        self.current_cog = 0
        self.current_sog = 0
        self.current_vmg = 0
        
        # Wind data
        self.true_wind_speed = 0
        self.true_wind_angle = 0
        self.apparent_wind_speed = 0
        self.apparent_wind_angle = 0
        self.absolute_wind_direction = 0
        
        # Position data
        self.latitude = 0
        self.longitude = 0
        
        # Waypoint information
        self.current_waypoint = "N/A"
        self.current_waypoint_id = 0
        self.bearing_to_waypoint = 0
        self.distance_to_waypoint = 0
        self.next_waypoint = "N/A"
        self.next_waypoint_id = 0
        self.course_to_next = 0
        
        # Enhanced waypoint data with coordinates
        self.destination_latitude = 0
        self.destination_longitude = 0
        self.cross_track_error = 0
        
        # Route information
        self.current_route_id = 0
        self.route_waypoints = {}  # Dictionary of waypoint_id: {lat, lon, name}
        self.waypoint_sequence = []  # Ordered list of waypoint IDs in route
        
        # Wind shift data
        self.wind_shift_1min = 0
        self.wind_shift_5min = 0
        self.wind_shift_10min = 0
    
    def update_navigation(self, cog=None, sog=None, vmg=None):
        """Update navigation data"""
        if cog is not None:
            self.current_cog = cog
        if sog is not None:
            self.current_sog = sog
        if vmg is not None:
            self.current_vmg = vmg
    
    def update_wind(self, true_speed=None, true_angle=None, 
                   apparent_speed=None, apparent_angle=None):
        """Update wind data"""
        if true_speed is not None:
            self.true_wind_speed = true_speed
        if true_angle is not None:
            self.true_wind_angle = true_angle
        if apparent_speed is not None:
            self.apparent_wind_speed = apparent_speed
        if apparent_angle is not None:
            self.apparent_wind_angle = apparent_angle
        
        # Calculate absolute wind direction
        if self.true_wind_angle is not None and self.current_cog is not None:
            self.absolute_wind_direction = (self.true_wind_angle + self.current_cog) % 360
    
    def update_position(self, latitude=None, longitude=None):
        """Update position data"""
        if latitude is not None:
            self.latitude = latitude
        if longitude is not None:
            self.longitude = longitude
    
    def update_waypoint(self, current_wp=None, bearing=None, distance=None, 
                       next_wp=None, course_to_next=None, waypoint_id=None,
                       dest_lat=None, dest_lon=None, xte=None):
        """Update waypoint information"""
        if current_wp is not None:
            self.current_waypoint = current_wp
        if bearing is not None:
            self.bearing_to_waypoint = bearing
        if distance is not None:
            self.distance_to_waypoint = distance
        if next_wp is not None:
            self.next_waypoint = next_wp
        if course_to_next is not None:
            self.course_to_next = course_to_next
        if waypoint_id is not None:
            self.current_waypoint_id = waypoint_id
        if dest_lat is not None:
            self.destination_latitude = dest_lat
        if dest_lon is not None:
            self.destination_longitude = dest_lon
        if xte is not None:
            self.cross_track_error = xte
    
    def add_route_waypoint(self, waypoint_id, latitude, longitude, name=None):
        """Add a waypoint to the route database"""
        if name is None:
            name = f"WP{waypoint_id}"
        
        self.route_waypoints[waypoint_id] = {
            'latitude': latitude,
            'longitude': longitude,
            'name': name
        }
        
        # Update sequence if not already present
        if waypoint_id not in self.waypoint_sequence:
            self.waypoint_sequence.append(waypoint_id)
    
    def update_route(self, route_id=None, waypoints_list=None):
        """Update route information"""
        if route_id is not None:
            self.current_route_id = route_id
        
        if waypoints_list is not None:
            # Clear existing route waypoints
            self.route_waypoints.clear()
            self.waypoint_sequence.clear()
            
            # Add new waypoints
            for wp in waypoints_list:
                self.add_route_waypoint(
                    wp['waypoint_id'],
                    wp['latitude'], 
                    wp['longitude'],
                    wp.get('name')
                )
    
    def get_waypoint_coordinates(self, waypoint_id):
        """Get coordinates for a specific waypoint"""
        if waypoint_id in self.route_waypoints:
            wp = self.route_waypoints[waypoint_id]
            return wp['latitude'], wp['longitude']
        return None, None
    
    def get_next_waypoint_in_route(self):
        """Get the next waypoint in the current route"""
        try:
            current_index = self.waypoint_sequence.index(self.current_waypoint_id)
            if current_index + 1 < len(self.waypoint_sequence):
                next_wp_id = self.waypoint_sequence[current_index + 1]
                if next_wp_id in self.route_waypoints:
                    return self.route_waypoints[next_wp_id]
        except (ValueError, IndexError):
            pass
        return None
    
    def calculate_course_to_next_waypoint(self):
        """Calculate bearing from current waypoint to next waypoint"""
        if (self.current_waypoint_id in self.route_waypoints and 
            self.destination_latitude != 0 and self.destination_longitude != 0):
            
            next_wp = self.get_next_waypoint_in_route()
            if next_wp:
                # Calculate bearing between current destination and next waypoint
                bearing = self._calculate_bearing(
                    self.destination_latitude, self.destination_longitude,
                    next_wp['latitude'], next_wp['longitude']
                )
                self.course_to_next = bearing
                self.next_waypoint = next_wp['name']
                self.next_waypoint_id = next_wp.get('waypoint_id', 0)
    
    def _calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculate bearing between two points"""
        import math
        
        # Convert to radians
        lat1_r = math.radians(lat1)
        lat2_r = math.radians(lat2)
        delta_lon_r = math.radians(lon2 - lon1)
        
        # Calculate bearing
        y = math.sin(delta_lon_r) * math.cos(lat2_r)
        x = (math.cos(lat1_r) * math.sin(lat2_r) - 
             math.sin(lat1_r) * math.cos(lat2_r) * math.cos(delta_lon_r))
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360  # Normalize to 0-360
        
        return bearing
    
    def update_wind_shifts(self, shift_1min=None, shift_5min=None, shift_10min=None):
        """Update wind shift data"""
        if shift_1min is not None:
            self.wind_shift_1min = shift_1min
        if shift_5min is not None:
            self.wind_shift_5min = shift_5min
        if shift_10min is not None:
            self.wind_shift_10min = shift_10min
    
    def get_navigation_summary(self):
        """Get a summary of current navigation data"""
        return {
            'COG': self.current_cog,
            'SOG': self.current_sog,
            'VMG': self.current_vmg,
            'True Wind Speed': self.true_wind_speed,
            'True Wind Angle': self.true_wind_angle,
            'App Wind Speed': self.apparent_wind_speed,
            'App Wind Angle': self.apparent_wind_angle,
            'Abs Wind Direction': self.absolute_wind_direction
        }
    
    def get_waypoint_summary(self):
        """Get a summary of waypoint information"""
        return {
            'Current WP': self.current_waypoint,
            'Bearing to WP': self.bearing_to_waypoint,
            'Distance to WP': self.distance_to_waypoint,
            'Next WP': self.next_waypoint,
            'Course to Next': self.course_to_next,
            'Dest Latitude': self.destination_latitude,
            'Dest Longitude': self.destination_longitude,
            'Cross Track Error': self.cross_track_error
        }
    
    def get_route_summary(self):
        """Get a summary of route information"""
        return {
            'Route ID': self.current_route_id,
            'Total Waypoints': len(self.route_waypoints),
            'Waypoint Sequence': self.waypoint_sequence.copy(),
            'Route Waypoints': self.route_waypoints.copy()
        }
    
    def get_wind_shift_summary(self):
        """Get a summary of wind shift information"""
        return {
            '1 min': self.wind_shift_1min,
            '5 min': self.wind_shift_5min,
            '10 min': self.wind_shift_10min
        }