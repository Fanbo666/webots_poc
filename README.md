# Webots 机器人建图与定位系统

## 项目概述

本项目实现了一个完整的机器人建图与定位系统，基于Webots仿真环境，使用TurtleBot3平台。系统包含三个主要模块：

1. **手动建图** - 基于激光雷达的实时建图系统
2. **自动建图** - 智能探索算法的自动建图系统  
3. **粒子滤波定位** - 基于已有地图的蒙特卡洛定位系统

## 技术特性

### 核心算法
- **SLAM建图**: 激光雷达扫描与位置估计结合的实时建图
- **智能探索**: 基于避障的自动探索算法，支持困境脱困
- **粒子滤波**: 100粒子的蒙特卡洛定位算法
- **传感器融合**: LiDAR + 运动编码器数据融合

### 技术亮点
- **零外部依赖**: 仅使用Python标准库和Webots API
- **模块化设计**: 建图与定位完全分离，便于独立测试
- **多格式输出**: 支持PPM图像、ASCII可视化、CSV数据导出
- **实时可视化**: 控制台实时显示传感器数据和算法状态

## 系统架构

```
webots_poc/
├── controllers/
│   ├── mapping_controller/          # 手动建图模块
│   │   ├── mapping_controller.py    # 主控制器
│   │   ├── simple_map_data.txt     # 建图数据输出
│   │   └── map_image.ppm           # 地图图像
│   ├── mapping_controller_auto/     # 自动建图模块  
│   │   ├── mapping_controller_auto.py
│   │   ├── simple_map_data.txt     # 兼容格式输出
│   │   └── auto_map_image.ppm      # 自动建图图像
│   └── localization_controller/    # 粒子滤波定位
│       ├── localization_controller.py
│       ├── localization_results.txt
│       └── visualize_results.py    # 结果分析工具
├── tb_world/
│   └── turtlebot3_burger_world.wbt # Webots仿真世界
└── requirements.txt
```

## 使用流程

### 1. 环境准备
```bash
# 确保安装Webots R2023a或更高版本
# 克隆项目到本地
cd webots_poc
```

### 2. 建图阶段
选择以下任一方式进行建图：

**手动建图**（推荐精确度高）:
```bash
# 在Webots中设置mapping_controller为机器人控制器
# 使用WASD键手动探索环境
# 按Q键保存地图数据
```

**自动建图**（推荐覆盖度高）:
```bash
# 在Webots中设置mapping_controller_auto为机器人控制器  
# 系统自动探索环境
# 可按M键切换手动/自动模式
# 按Q键保存地图数据
```

### 3. 定位阶段
```bash
# 确保建图阶段已生成simple_map_data.txt
# 在Webots中设置localization_controller为机器人控制器
# 使用WASD控制机器人进行定位测试
# 按Q键保存定位结果
```

### 4. 结果分析
```bash
cd controllers/localization_controller
python visualize_results.py
# 生成轨迹可视化和误差分析报告
```

## 性能指标

### 建图性能
- **分辨率**: 0.05米/像素的网格地图
- **传感器范围**: 5米激光雷达检测范围
- **更新频率**: 实时建图，每时间步更新
- **输出格式**: PPM图像 + CSV数据 + ASCII可视化

### 定位性能  
- **算法**: 100粒子蒙特卡洛定位
- **传感器**: 4方向激光雷达 + 差分驱动里程计
- **精度**: 平均定位误差通常在0.1-0.5米范围
- **收敛时间**: 通常10-20个运动步骤后开始收敛

### 自动探索性能
- **探索策略**: 前进优先 + 智能避障 + 随机探索
- **脱困能力**: 多级脱困机制，包括后退-转向-重置
- **覆盖能力**: 支持无限探索直到手动停止

## 核心技术实现

### 建图算法
```python
# 基于激光雷达的栅格建图
def collect_scan_data():
    # 获取四方向激光数据
    front, left, right, back = get_sensor_distances()
    # 结合位置和方向信息生成地图点
    position, angle = get_robot_pose()
    # 更新栅格地图
```

### 粒子滤波定位
```python
# 经典三步骤粒子滤波
def particle_filter_step():
    predict_particles()    # 运动预测
    update_weights()       # 传感器更新  
    resample_particles()   # 重采样
    return estimate_pose() # 位置估计
```

### 智能探索
```python
# 避障优先的探索策略
def exploration_algorithm():
    if front_clear(): forward()
    elif side_clear(): turn_to_clear_side()
    else: execute_escape_sequence()
```

## 扩展性设计

本系统采用模块化设计，支持以下扩展：

- **传感器扩展**: 易于添加摄像头、IMU等传感器
- **算法扩展**: 可替换为FastSLAM、EKF-SLAM等高级算法
- **地图表示**: 可扩展为语义地图、拓扑地图等
- **路径规划**: 可添加A*、RRT等路径规划算法

## 故障排除

### 常见问题
1. **控制器无法启动**: 检查文件路径和Python环境
2. **传感器无数据**: 确认Webots传感器设置正确
3. **定位精度差**: 确保建图数据质量，检查粒子数量设置
4. **自动探索卡住**: 检查障碍物阈值设置，可手动介入

### 调试工具
- 控制台实时状态输出
- 可视化分析工具
- 详细的CSV数据日志
- 错误追踪和异常处理

## 技术依赖

- **Webots**: R2023a或更高版本
- **Python**: 3.7+ （Webots内置）
- **传感器**: LiDAR、GPS、Compass、Motor encoders
- **平台**: TurtleBot3 Burger

## 贡献指南

欢迎提交改进建议和扩展功能：
1. Fork项目仓库
2. 创建功能分支
3. 提交更改并编写测试
4. 发起Pull Request

本项目展示了现代机器人建图与定位技术的完整实现，适合机器人学习、研究和开发使用。
