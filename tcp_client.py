"""
TCP Client Library for NMEA2000 Data Reception
Handles TCP connection and message reception in a separate thread
"""

import socket
import threading
from datetime import datetime

class NMEA2000TCPClient:
    def __init__(self, message_callback=None, status_callback=None):
        self.socket = None
        self.connected = False
        self.receive_thread = None
        self.message_callback = message_callback
        self.status_callback = status_callback
        self.log_file = None
        self.message_count = 0
        
    def connect(self, server, port):
        """Connect to TCP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10 second timeout
            self.socket.connect((server, port))
            self.connected = True
            
            # Open log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = open(f"nmea2000_log_{timestamp}.txt", "w")
            
            # Start receiving thread
            self.receive_thread = threading.Thread(target=self._receive_data)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            if self.status_callback:
                self.status_callback(f'Connected to {server}:{port}')
            
            return True
            
        except Exception as e:
            if self.status_callback:
                self.status_callback(f'Connection failed: {str(e)}')
            return False
    
    def disconnect(self):
        """Disconnect from TCP server"""
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        if self.log_file:
            try:
                self.log_file.close()
            except:
                pass
            self.log_file = None
        
        if self.status_callback:
            self.status_callback('Disconnected')
    
    def _receive_data(self):
        """Receive data in background thread"""
        buffer = b''
        
        while self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                
                buffer += data
                
                # Process complete messages (assuming messages are terminated by newline)
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if line:
                        self._process_message(line)
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self.connected:
                    if self.status_callback:
                        self.status_callback(f'Receive error: {str(e)}')
                break
        
        self.connected = False
        if self.status_callback:
            self.status_callback('Connection lost')
    
    def _process_message(self, raw_data):
        """Process received message"""
        # Log the raw message
        timestamp = datetime.now().isoformat()
        if self.log_file:
            try:
                self.log_file.write(f"{timestamp}: {raw_data.hex()}\n")
                self.log_file.flush()
            except:
                pass
        
        self.message_count += 1
        
        # Call message callback if provided
        if self.message_callback:
            self.message_callback(raw_data)
    
    def is_connected(self):
        """Check if client is connected"""
        return self.connected
    
    def get_message_count(self):
        """Get total number of messages received"""
        return self.message_count
    
    def reset_message_count(self):
        """Reset message counter"""
        self.message_count = 0