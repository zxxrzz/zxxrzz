import threading
import time
from scapy.all import sniff, get_if_list, conf
from scapy.packet import Packet
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import socket
import struct


class TrafficCapture:
    def __init__(self, interface: Optional[str] = None):
        self.interface = interface
        self.running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.stats_lock = threading.Lock()
        
        self.bytes_in_per_second: deque[Tuple[int, int]] = deque(maxlen=60)
        self.bytes_out_per_second: deque[Tuple[int, int]] = deque(maxlen=60)
        self.protocol_count: Dict[str, int] = defaultdict(int)
        self.ip_traffic: Dict[str, int] = defaultdict(int)
        
        self.current_bytes_in = 0
        self.current_bytes_out = 0
        self.last_second = int(time.time())
        
    def get_interfaces(self) -> List[str]:
        return get_if_list()
    
    def _packet_callback(self, packet: Packet):
        if not self.running:
            return
            
        packet_size = len(packet)
        current_second = int(time.time())
        
        with self.stats_lock:
            if current_second != self.last_second:
                self.bytes_in_per_second.append((self.last_second, self.current_bytes_in))
                self.bytes_out_per_second.append((self.last_second, self.current_bytes_out))
                self.current_bytes_in = 0
                self.current_bytes_out = 0
                self.last_second = current_second
            
            if packet.haslayer('IP'):
                src_ip = packet['IP'].src
                dst_ip = packet['IP'].dst
                local_ip = self._get_local_ip()
                
                if dst_ip == local_ip:
                    self.current_bytes_in += packet_size
                    self.ip_traffic[src_ip] += packet_size
                elif src_ip == local_ip:
                    self.current_bytes_out += packet_size
                    self.ip_traffic[dst_ip] += packet_size
                
                if packet.haslayer('TCP'):
                    self.protocol_count['TCP'] += 1
                elif packet.haslayer('UDP'):
                    self.protocol_count['UDP'] += 1
                elif packet.haslayer('ICMP'):
                    self.protocol_count['ICMP'] += 1
                else:
                    self.protocol_count['Other'] += 1
    
    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def start_capture(self):
        if self.running:
            return
            
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
    
    def _capture_loop(self):
        try:
            if self.interface:
                conf.iface = self.interface
            sniff(prn=self._packet_callback, store=0, stop_filter=lambda p: not self.running)
        except Exception as e:
            print(f"Capture error: {e}")
            self.running = False
    
    def stop_capture(self):
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
    
    def get_current_stats(self) -> Dict:
        with self.stats_lock:
            current_second = int(time.time())
            if current_second != self.last_second and (self.current_bytes_in > 0 or self.current_bytes_out > 0):
                self.bytes_in_per_second.append((self.last_second, self.current_bytes_in))
                self.bytes_out_per_second.append((self.last_second, self.current_bytes_out))
                self.current_bytes_in = 0
                self.current_bytes_out = 0
                self.last_second = current_second
            
            total_in = sum(ts[1] for ts in self.bytes_in_per_second)
            total_out = sum(ts[1] for ts in self.bytes_out_per_second)
            
            return {
                'bytes_in_per_second': list(self.bytes_in_per_second),
                'bytes_out_per_second': list(self.bytes_out_per_second),
                'protocol_count': dict(self.protocol_count),
                'ip_traffic': dict(self.ip_traffic),
                'current_bytes_in': self.current_bytes_in,
                'current_bytes_out': self.current_bytes_out,
                'total_in': total_in,
                'total_out': total_out
            }
    
    def clear_stats(self):
        with self.stats_lock:
            self.bytes_in_per_second.clear()
            self.bytes_out_per_second.clear()
            self.protocol_count.clear()
            self.ip_traffic.clear()
            self.current_bytes_in = 0
            self.current_bytes_out = 0
            self.last_second = int(time.time())
