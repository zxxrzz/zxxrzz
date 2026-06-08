import time
import sys
sys.path.insert(0, '/workspace/src')
from traffic_capture import TrafficCapture


def main():
    print("=== 网络流量抓包测试 ===\n")
    
    capture = TrafficCapture()
    
    print("可用网卡列表:")
    interfaces = capture.get_interfaces()
    for i, iface in enumerate(interfaces):
        print(f"  {i+1}. {iface}")
    
    print("\n开始抓包... (按 Ctrl+C 停止)")
    
    try:
        capture.start_capture()
        
        for i in range(10):
            time.sleep(1)
            stats = capture.get_current_stats()
            
            print(f"\n--- 第 {i+1} 秒统计 ---")
            print(f"当前上行: {stats['current_bytes_out']} bytes/s")
            print(f"当前下行: {stats['current_bytes_in']} bytes/s")
            print(f"总流量: {stats['total_in'] + stats['total_out']} bytes")
            print(f"协议统计: {stats['protocol_count']}")
            
            top_ips = sorted(stats['ip_traffic'].items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"Top IPs: {top_ips}")
    
    except KeyboardInterrupt:
        print("\n\n收到停止信号...")
    
    finally:
        capture.stop_capture()
        print("抓包已停止。")


if __name__ == "__main__":
    main()
