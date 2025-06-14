"""
NMEA2000 Message Parser Library
Handles parsing of various NMEA2000 PGN messages
"""

import struct
import math

class NMEA2000Parser:
    def __init__(self):
        self.pgn_parsers = {
            129025: self.parse_position_rapid_update,
            129026: self.parse_cog_sog_rapid_update,
            130306: self.parse_wind_data,
            129284: self.parse_navigation_data,
            129285: self.parse_route_waypoint_info,
            129283: self.parse_cross_track_error,
            129281: self.parse_navigation_route_info,
            129540: self.parse_waypoint_list,
            130074: self.parse_route_waypoint_database
        }
    
    def parse_message(self, raw_data):
        """Parse raw NMEA2000 message"""
        try:
            if len(raw_data) < 8:
                return None
            
            # Extract CAN ID and PGN
            can_id = struct.unpack('>I', raw_data[:4])[0]
            pgn = (can_id >> 8) & 0x1FFFF
            
            data = raw_data[8:]  # Skip header
            
            if pgn in self.pgn_parsers:
                return self.pgn_parsers[pgn](data)
            
            return {'pgn': pgn, 'raw': raw_data.hex()}
        except Exception as e:
            return {'error': str(e)}
    
    def parse_position_rapid_update(self, data):
        """Parse PGN 129025 - Position Rapid Update"""
        if len(data) < 8:
            return None
        lat = struct.unpack('<i', data[0:4])[0] * 1e-7
        lon = struct.unpack('<i', data[4:8])[0] * 1e-7
        return {'type': 'position', 'latitude': lat, 'longitude': lon}
    
    def parse_cog_sog_rapid_update(self, data):
        """Parse PGN 129026 - COG & SOG Rapid Update"""
        if len(data) < 8:
            return None
        cog = struct.unpack('<H', data[2:4])[0] * 0.0001 * 180 / math.pi
        sog = struct.unpack('<H', data[4:6])[0] * 0.01
        return {'type': 'navigation', 'cog': cog, 'sog': sog}
    
    def parse_wind_data(self, data):
        """Parse PGN 130306 - Wind Data"""
        if len(data) < 6:
            return None
        wind_speed = struct.unpack('<H', data[0:2])[0] * 0.01
        wind_angle = struct.unpack('<H', data[2:4])[0] * 0.0001 * 180 / math.pi
        reference = data[4] & 0x07
        
        wind_type = 'apparent' if reference == 2 else 'true'
        return {
            'type': 'wind',
            'speed': wind_speed,
            'angle': wind_angle,
            'reference': wind_type
        }
    
    def parse_navigation_data(self, data):
        """Parse PGN 129284 - Navigation Data"""
        if len(data) < 8:
            return None
        bearing_to_waypoint = struct.unpack('<H', data[4:6])[0] * 0.0001 * 180 / math.pi
        distance_to_waypoint = struct.unpack('<I', data[0:4])[0] * 0.01
        return {
            'type': 'waypoint_nav',
            'bearing_to_waypoint': bearing_to_waypoint,
            'distance_to_waypoint': distance_to_waypoint
        }
    
    def parse_route_waypoint_info(self, data):
        """Parse PGN 129285 - Route/Waypoint Information"""
        if len(data) < 8:
            return None
        
        # Extract basic waypoint info
        waypoint_id = struct.unpack('<H', data[0:2])[0]
        waypoint_name = ""
        
        # Try to extract waypoint name if available
        if len(data) > 8:
            # Name typically starts at byte 8, null-terminated
            name_data = data[8:]
            null_pos = name_data.find(b'\x00')
            if null_pos > 0:
                try:
                    waypoint_name = name_data[:null_pos].decode('ascii', errors='ignore')
                except:
                    waypoint_name = f"WP{waypoint_id}"
            else:
                waypoint_name = f"WP{waypoint_id}"
        else:
            waypoint_name = f"WP{waypoint_id}"
        
        return {
            'type': 'waypoint_info',
            'waypoint_id': waypoint_id,
            'name': waypoint_name
        }
    
    def parse_cross_track_error(self, data):
        """Parse PGN 129283 - Cross Track Error"""
        if len(data) < 6:
            return None
        
        # XTE mode and navigation terminated flags
        xte_mode = data[0] & 0x0F
        nav_terminated = (data[0] & 0x40) != 0
        
        # Cross track error in meters
        xte = struct.unpack('<i', data[1:5])[0] * 0.01
        
        return {
            'type': 'cross_track_error',
            'xte': xte,
            'xte_mode': xte_mode,
            'nav_terminated': nav_terminated
        }
    
    def parse_navigation_route_info(self, data):
        """Parse PGN 129281 - Navigation Route/WP Information"""
        if len(data) < 16:
            return None
        
        # Route/WP ID
        route_id = struct.unpack('<H', data[0:2])[0]
        waypoint_id = struct.unpack('<H', data[2:4])[0]
        
        # Distance and bearing to waypoint
        distance_to_waypoint = struct.unpack('<I', data[4:8])[0] * 0.01  # meters to nm
        bearing_to_waypoint = struct.unpack('<H', data[8:10])[0] * 0.0001 * 180 / math.pi
        
        # Destination waypoint position
        dest_latitude = struct.unpack('<i', data[10:14])[0] * 1e-7
        dest_longitude = struct.unpack('<i', data[14:18])[0] * 1e-7 if len(data) >= 18 else None
        
        result = {
            'type': 'navigation_route_info',
            'route_id': route_id,
            'waypoint_id': waypoint_id,
            'distance_to_waypoint': distance_to_waypoint,
            'bearing_to_waypoint': bearing_to_waypoint,
            'destination_latitude': dest_latitude
        }
        
        if dest_longitude is not None:
            result['destination_longitude'] = dest_longitude
        
        return result
    
    def parse_waypoint_list(self, data):
        """Parse PGN 129540 - GNSS Sats in View"""
        # This PGN is sometimes used for waypoint lists in some systems
        # Implementation depends on specific manufacturer
        if len(data) < 8:
            return None
        
        return {
            'type': 'waypoint_list',
            'raw_data': data.hex(),
            'length': len(data)
        }
    
    def parse_route_waypoint_database(self, data):
        """Parse PGN 130074 - Route and WP Service - Database List"""
        if len(data) < 8:
            return None
        
        # Route/Database ID
        database_id = struct.unpack('<H', data[0:2])[0]
        route_id = struct.unpack('<H', data[2:4])[0]
        
        # Navigation direction and supplementary route info
        nav_direction = data[4] & 0x07
        supplementary_route = (data[4] & 0x08) != 0
        
        # Waypoint coordinates if available
        waypoints = []
        offset = 8
        
        while offset + 16 <= len(data):
            try:
                waypoint_id = struct.unpack('<H', data[offset:offset+2])[0]
                waypoint_lat = struct.unpack('<i', data[offset+2:offset+6])[0] * 1e-7
                waypoint_lon = struct.unpack('<i', data[offset+6:offset+10])[0] * 1e-7
                
                waypoints.append({
                    'waypoint_id': waypoint_id,
                    'latitude': waypoint_lat,
                    'longitude': waypoint_lon,
                    'name': f"WP{waypoint_id}"
                })
                
                offset += 16  # Move to next waypoint
            except:
                break
        
        return {
            'type': 'route_waypoint_database',
            'database_id': database_id,
            'route_id': route_id,
            'nav_direction': nav_direction,
            'supplementary_route': supplementary_route,
            'waypoints': waypoints
        }
    
    def get_waypoint_coordinates(self, waypoint_id):
        """Helper method to get stored waypoint coordinates"""
        # This would typically interface with a waypoint database
        # For now, returns None - would need to be implemented based on 
        # how waypoints are stored in your specific system
        return None