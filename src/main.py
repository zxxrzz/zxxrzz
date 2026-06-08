import flet as ft
import time
from collections import deque
import threading
import sys
sys.path.insert(0, '/workspace/src')
from traffic_capture import TrafficCapture


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


def format_speed(bytes_per_sec: int) -> str:
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec} B/s"
    elif bytes_per_sec < 1024 * 1024:
        return f"{bytes_per_sec / 1024:.2f} KB/s"
    elif bytes_per_sec < 1024 * 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
    else:
        return f"{bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s"


def main(page: ft.Page):
    page.title = "网络流量实时检测与可视化"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1000
    page.window.height = 700
    page.padding = 20
    page.bgcolor = "#0f172a"
    
    capture = TrafficCapture()
    capture_running = False
    refresh_running = False
    refresh_thread = None
    refresh_lock = threading.Lock()
    
    def create_data_card(title: str, value: str, icon: ft.Icons, color: str) -> ft.Card:
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(icon, size=30, color=color),
                                ft.Text(title, size=14, color="#94a3b8"),
                            ],
                            spacing=10,
                        ),
                        ft.Text(
                            value,
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=color,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=20,
                width=220,
                height=120,
            ),
            color="#1e293b",
            elevation=3,
        )
    
    speed_card = create_data_card("实时网速", "0 KB/s", ft.Icons.SPEED, "#3b82f6")
    total_card = create_data_card("总流量", "0 B", ft.Icons.DOWNLOAD_FOR_OFFLINE, "#10b981")
    connections_card = create_data_card("活跃连接", "0", ft.Icons.DEVICE_HUB, "#f59e0b")
    alerts_card = create_data_card("异常告警", "0", ft.Icons.WARNING, "#ef4444")
    
    speed_value = speed_card.content.content.controls[1]
    total_value = total_card.content.content.controls[1]
    connections_value = connections_card.content.content.controls[1]
    alerts_value = alerts_card.content.content.controls[1]
    
    line_chart = ft.LineChart(
        data_series=[],
        border=ft.border.all(1, ft.colors.with_opacity(0.2, ft.colors.WHITE)),
        horizontal_grid_lines=ft.ChartGridLines(
            interval=1, color=ft.colors.with_opacity(0.1, ft.colors.WHITE), width=1
        ),
        vertical_grid_lines=ft.ChartGridLines(
            interval=1, color=ft.colors.with_opacity(0.1, ft.colors.WHITE), width=1
        ),
        left_axis=ft.ChartAxis(
            labels_size=40,
            labels_interval=1,
        ),
        bottom_axis=ft.ChartAxis(
            labels_size=30,
            get_label=lambda x, _: f"{int(x)}s" if int(x) % 10 == 0 else "",
        ),
        width=500,
        height=300,
        animate=500,
    )
    
    pie_chart = ft.PieChart(
        sections=[],
        sections_space=1,
        center_space_radius=40,
        width=300,
        height=300,
        animate=500,
    )
    
    top_ip_list = ft.ListView(
        spacing=5,
        padding=10,
        height=250,
    )
    
    log_list = ft.ListView(
        spacing=5,
        padding=10,
        height=100,
        auto_scroll=True,
    )
    
    interface_dropdown = ft.Dropdown(
        width=300,
        label="选择网卡",
        hint_text="请选择网卡",
    )
    
    def load_interfaces():
        interfaces = capture.get_interfaces()
        interface_dropdown.options = [ft.dropdown.Option(iface) for iface in interfaces]
        if interfaces:
            interface_dropdown.value = interfaces[0]
        page.update()
    
    def toggle_capture(e):
        nonlocal capture_running, refresh_running, refresh_thread
        if not capture_running:
            if interface_dropdown.value:
                capture.interface = interface_dropdown.value
                capture.clear_stats()
                capture.start_capture()
                capture_running = True
                refresh_running = True
                start_btn.text = "停止抓包"
                start_btn.icon = ft.Icons.STOP
                start_btn.bgcolor = "#ef4444"
                
                alerts_value.value = "0"
                
                refresh_thread = threading.Thread(target=refresh_data_loop, daemon=True)
                refresh_thread.start()
                
                log_list.controls.append(
                    ft.Text(f"[{time.strftime('%H:%M:%S')}] 开始抓包: {interface_dropdown.value}", color="#10b981")
                )
            else:
                page.show_snack_bar(ft.SnackBar(content=ft.Text("请先选择网卡！")))
        else:
            capture.stop_capture()
            capture_running = False
            refresh_running = False
            start_btn.text = "开始抓包"
            start_btn.icon = ft.Icons.PLAY_ARROW
            start_btn.bgcolor = "#3b82f6"
            log_list.controls.append(
                ft.Text(f"[{time.strftime('%H:%M:%S')}] 停止抓包", color="#f59e0b")
            )
        page.update()
    
    def refresh_data_loop():
        while refresh_running:
            time.sleep(0.5)
            with refresh_lock:
                try:
                    stats = capture.get_current_stats()
                    page.update()
                    update_ui(stats)
                except:
                    pass
    
    def update_ui(stats):
        speed_value.value = format_speed(stats['current_bytes_in'] + stats['current_bytes_out'])
        total_value.value = format_bytes(stats['total_in'] + stats['total_out'])
        
        unique_ips = len(stats['ip_traffic'])
        connections_value.value = str(unique_ips)
        
        alerts_value.value = str(stats.get('alert_count', 0))
        
        for alert in stats.get('new_alerts', []):
            alert_type = alert.get('type', '')
            alert_color = '#ef4444'
            if alert_type == '频率异常':
                alert_color = '#f59e0b'
            elif alert_type == '端口扫描':
                alert_color = '#ef4444'
            elif alert_type == '非标准端口':
                alert_color = '#f97316'
            
            log_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(f"[{alert['time']}]", size=12, color="#94a3b8"),
                            ft.Text(f"[{alert['type']}]", size=12, weight=ft.FontWeight.BOLD, color=alert_color),
                            ft.Text(alert['message'], size=12, color="#e2e8f0"),
                        ],
                        spacing=10,
                        wrap=True,
                    ),
                    padding=8,
                    bgcolor="#1e293b",
                    border_radius=6,
                )
            )
        
        in_data = [ft.LineChartDataPoint(i, v / 1024) for i, (t, v) in enumerate(stats['bytes_in_per_second'][-60:])]
        out_data = [ft.LineChartDataPoint(i, v / 1024) for i, (t, v) in enumerate(stats['bytes_out_per_second'][-60:])]
        
        line_chart.data_series = [
            ft.LineChartData(
                data_points=in_data,
                stroke_width=2,
                color="#10b981",
                curved=True,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points=out_data,
                stroke_width=2,
                color="#3b82f6",
                curved=True,
                stroke_cap_round=True,
            ),
        ]
        
        protocol_colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]
        pie_sections = []
        total_packets = sum(stats['protocol_count'].values())
        for i, (proto, count) in enumerate(stats['protocol_count'].items()):
            percentage = count / total_packets * 100 if total_packets > 0 else 0
            pie_sections.append(
                ft.PieChartSection(
                    value=count,
                    title=f"{proto}\n{percentage:.1f}%",
                    title_style=ft.TextStyle(color=ft.colors.WHITE, fontSize=12),
                    color=protocol_colors[i % len(protocol_colors)],
                    radius=60,
                )
            )
        pie_chart.sections = pie_sections
        
        top_ip_list.controls.clear()
        sorted_ips = sorted(stats['ip_traffic'].items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (ip, traffic) in enumerate(sorted_ips):
            top_ip_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(f"#{i+1}", size=16, weight=ft.FontWeight.BOLD, color="#60a5fa"),
                            ft.Text(ip, size=14, color="#e2e8f0"),
                            ft.Spacer(),
                            ft.Text(format_bytes(traffic), size=14, color="#94a3b8"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=10,
                    bgcolor="#1e293b",
                    border_radius=8,
                )
            )
        
        page.update()
    
    start_btn = ft.ElevatedButton(
        text="开始抓包",
        icon=ft.Icons.PLAY_ARROW,
        on_click=toggle_capture,
        bgcolor="#3b82f6",
        color=ft.colors.WHITE,
        style=ft.ButtonStyle(
            padding=ft.padding.all(15),
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
    )
    
    page.add(
        ft.Row(
            [
                ft.Text(
                    "🚀 网络流量实时检测与可视化",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color="#60a5fa",
                ),
                ft.Spacer(),
                interface_dropdown,
                start_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=20,
        ),
        ft.Divider(height=30, color="#334155"),
        ft.Row(
            [
                speed_card,
                total_card,
                connections_card,
                alerts_card,
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            spacing=20,
        ),
        ft.Divider(height=30, color="#334155"),
        ft.Row(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("📈 流量趋势 (过去60秒)", size=16, weight=ft.FontWeight.BOLD, color="#e2e8f0"),
                            ft.Row(
                                [
                                    ft.Container(width=10, height=10, bgcolor="#10b981", border_radius=5),
                                    ft.Text("下行", size=12, color="#94a3b8"),
                                    ft.Container(width=20),
                                    ft.Container(width=10, height=10, bgcolor="#3b82f6", border_radius=5),
                                    ft.Text("上行", size=12, color="#94a3b8"),
                                ],
                                spacing=5,
                            ),
                            line_chart,
                        ],
                        spacing=10,
                    ),
                    padding=20,
                    bgcolor="#1e293b",
                    border_radius=12,
                    expand=True,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("🥧 协议占比", size=16, weight=ft.FontWeight.BOLD, color="#e2e8f0"),
                            pie_chart,
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=20,
                    bgcolor="#1e293b",
                    border_radius=12,
                    width=350,
                ),
            ],
            spacing=20,
            expand=True,
        ),
        ft.Row(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("🔥 Top 5 流量 IP", size=16, weight=ft.FontWeight.BOLD, color="#e2e8f0"),
                            top_ip_list,
                        ],
                        spacing=10,
                    ),
                    padding=20,
                    bgcolor="#1e293b",
                    border_radius=12,
                    expand=True,
                ),
            ],
            spacing=20,
        ),
        ft.Divider(height=20, color="#334155"),
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("📝 运行日志", size=14, weight=ft.FontWeight.BOLD, color="#e2e8f0"),
                    log_list,
                ],
                spacing=5,
            ),
            padding=15,
            bgcolor="#1e293b",
            border_radius=12,
        ),
    )
    
    load_interfaces()


if __name__ == "__main__":
    ft.app(target=main)
