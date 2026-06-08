# 网络流量实时检测与可视化桌面应用

一个基于 Flet 和 Scapy 的现代深色主题网络流量监控桌面应用。

## 功能特性

- 📊 **实时流量监控**：显示上下行流量、总流量、活跃连接数
- 📈 **流量趋势图**：动态折线图展示过去60秒的流量变化
- 🥧 **协议占比**：饼图显示 TCP/UDP/ICMP/Other 协议分布
- 🔥 **Top IP 统计**：展示流量最高的5个IP地址
- 🚨 **异常检测**：
  - 单IP请求频率超限检测
  - 端口扫描行为检测
  - 非标准端口访问检测
- 📝 **运行日志**：实时显示系统日志和告警信息

## 技术栈

- **UI框架**：Flet
- **抓包引擎**：Scapy
- **数据处理**：Python 多线程

## 项目结构

```
network-traffic-monitor/
├── src/
│   ├── main.py              # 主应用入口
│   ├── traffic_capture.py   # 抓包核心模块
│   └── test_capture.py      # 测试脚本
├── requirements.txt         # 依赖列表
├── build.spec              # PyInstaller 打包配置
└── README.md               # 项目说明
```

## 环境安装

### 1. 安装 Npcap 驱动（Windows 必须）

访问 [Npcap 官网](https://npcap.com/) 下载并安装，**务必勾选 "Install Npcap in WinPcap API-compatible Mode"**。

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 直接运行

以**管理员身份**运行：

```bash
python src/main.py
```

### 测试抓包

```bash
python src/test_capture.py
```

## 项目打包

使用 PyInstaller 打包成独立 exe 文件：

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 执行打包命令（推荐使用 spec 文件）

在项目根目录下执行：

```bash
pyinstaller build.spec
```

或者直接使用命令行：

```bash
pyinstaller --onefile --windowed --name "NetworkTrafficMonitor" src/main.py
```

参数说明：
- `--onefile`：打包成单个 exe 文件
- `--windowed`：不显示控制台窗口
- `--name`：指定 exe 文件名

### 3. 运行打包后的程序

打包完成后，在 `dist` 目录下找到 `NetworkTrafficMonitor.exe`，**以管理员身份**双击运行即可。

### 4. 注意事项

- 打包时请确保在 Windows 环境下进行
- 打包后的 exe 文件体积较大（约 50-100MB），这是正常的
- 用户运行时仍需先安装 Npcap 驱动

## 配置说明

### 异常检测阈值（可在 traffic_capture.py 中调整）

- `FREQUENCY_THRESHOLD = 100`：单IP每秒请求频率阈值
- `SCAN_PORT_THRESHOLD = 20`：端口扫描阈值（访问不同端口数量）
- `STANDARD_PORTS`：标准端口列表

## 注意事项

1. 必须以**管理员身份**运行程序才能正常抓包
2. 需要先安装 Npcap 驱动
3. 首次运行可能需要 Windows 防火墙授权

## 许可证

MIT License
