# 粒子滤波定位控制器

基于蒙特卡洛方法的粒子滤波定位系统，实现机器人在已知地图中的精确位置估计。

## 核心算法

### 粒子滤波框架
- **100粒子系统**: 多假设追踪提高定位精度
- **经典三步骤**: 预测、更新、重采样
- **传感器融合**: LiDAR观测与运动模型结合
- **实时估计**: 每时间步更新位置估计

### 算法特性
- **自适应权重**: 基于传感器似然度的粒子权重更新
- **重采样策略**: 低方差重采样避免粒子退化
- **噪声模型**: 运动和观测噪声建模提高鲁棒性
- **收敛检测**: 粒子聚集度评估定位置信度

## 技术实现

### 粒子滤波核心算法
```python
def particle_filter_step():
    """粒子滤波主循环"""
    # 1. 预测步骤 - 运动模型
    for particle in particles:
        particle.predict(motion_command, motion_noise)
    
    # 2. 更新步骤 - 观测模型  
    for particle in particles:
        particle.weight = compute_likelihood(sensor_data, map_data)
    
    # 3. 重采样步骤
    particles = resample_particles(particles, weights)
    
    # 4. 位置估计
    return weighted_average_pose(particles)
```

### 传感器观测模型
```python
def compute_likelihood(sensor_reading, expected_reading):
    """计算传感器观测似然度"""
    # 高斯噪声模型
    sigma = 0.1  # 传感器噪声标准差
    diff = abs(sensor_reading - expected_reading)
    return exp(-0.5 * (diff/sigma)**2)
```

## 传感器配置

### 激光雷达阵列
- **4方向传感器**: 前、左、右、后激光雷达
- **有效范围**: 0.1-5.0米精确测距
- **观测频率**: 每控制周期实时更新
- **噪声特性**: 高斯分布，标准差0.1米

### 运动传感器
- **差分驱动**: 左右轮速度编码器
- **运动模型**: 基于运动学的状态预测
- **噪声建模**: 运动过程中的累积误差处理

## 地图数据接口

### 输入格式要求
- **文件名**: `simple_map_data.txt`（建图阶段输出）
- **CSV格式**: X,Y,Value三列数据
- **坐标系**: 与建图阶段一致的全局坐标系
- **编码标准**: 1(自由空间)，2(障碍物)

### 地图数据处理
```python
def load_map_data(filename):
    """加载并处理地图数据"""
    map_points = {}
    with open(filename, 'r') as f:
        for line in f:
            if not line.startswith('#'):
                x, y, value = line.strip().split(',')
                map_points[(float(x), float(y))] = int(value)
    return map_points
```

## 控制接口

### 运动控制
| 按键 | 功能 | 运动参数 |
|------|------|----------|
| **W** | 前进 | 线速度: 2.0 m/s |
| **S** | 后退 | 线速度: -2.0 m/s |
| **A** | 左转 | 角速度: 2.0 rad/s |
| **D** | 右转 | 角速度: -2.0 rad/s |
| **空格** | 停止 | 零速度 |
| **Q** | 保存退出 | - |

### 状态监控
实时控制台输出：
```
Step: 145 | Position: (-1.25, 2.34) | Angle: 1.57 rad
Sensors: F:2.34 L:1.56 R:0.87 B:3.21
Particle Spread: 0.12 | Confidence: 0.89
Command: FORWARD | Linear: 2.0 | Angular: 0.0
```

## 性能评估

### 定位精度
- **初始收敛**: 通常10-20步后开始收敛
- **稳态精度**: 平均定位误差0.1-0.5米
- **角度精度**: 方向角误差通常小于0.1弧度
- **置信评估**: 粒子分布方差指示定位置信度

### 算法性能
- **计算复杂度**: O(N)，N为粒子数量
- **内存占用**: 线性关联粒子数量
- **实时性**: 满足控制周期要求
- **收敛速度**: 几何级收敛到真实位置

## 输出格式

### 定位结果文件 (`localization_results.txt`)
```csv
# Step,X,Y,Theta,Confidence,SensorF,SensorL,SensorR,SensorB
1,-0.05,0.02,0.01,0.234,2.71,2.96,3.00,3.29
2,-0.03,0.05,0.02,0.267,2.68,2.93,2.97,3.26
```

### 数据字段说明
- **Step**: 时间步计数
- **X,Y**: 估计的机器人位置坐标
- **Theta**: 估计的机器人方向角
- **Confidence**: 定位置信度（0-1）
- **SensorF/L/R/B**: 四方向传感器读数

## 可视化分析

### 轨迹可视化工具
```python
# 运行结果分析
python visualize_results.py
```

### 生成内容
- **轨迹图**: 机器人运动轨迹可视化
- **误差分析**: 定位误差统计和分布
- **传感器数据**: 传感器读数时间序列
- **收敛分析**: 粒子滤波收敛过程

## 使用流程

### 1. 环境准备
```bash
# 确保已完成建图阶段，生成simple_map_data.txt
# 在Webots中设置localization_controller为控制器
```

### 2. 启动定位
```bash
# 运行Webots仿真
# 控制台显示粒子滤波初始化信息
```

### 3. 控制测试
```bash
# 使用WASD键控制机器人移动
# 观察定位精度随运动变化
# 验证算法收敛性能
```

### 4. 结果分析
```bash
# 按Q键保存定位数据
# 运行visualize_results.py分析结果
```

## 高级功能

### 自适应粒子数
```python
def adaptive_particle_count(confidence):
    """根据定位置信度调整粒子数量"""
    if confidence > 0.8:
        return 50   # 高置信度减少粒子
    elif confidence > 0.5:
        return 100  # 中等置信度标准粒子
    else:
        return 200  # 低置信度增加粒子
```

### 退化检测与处理
```python
def effective_particle_number(weights):
    """计算有效粒子数"""
    return 1.0 / sum(w*w for w in weights)

def need_resample(effective_n, total_n):
    """判断是否需要重采样"""
    return effective_n < total_n / 2
```

## 参数调优

### 核心参数
```python
# 粒子滤波参数
NUM_PARTICLES = 100        # 粒子数量
MOTION_NOISE_TRANS = 0.1   # 平移噪声标准差
MOTION_NOISE_ROT = 0.05    # 旋转噪声标准差
SENSOR_NOISE = 0.1         # 传感器噪声标准差

# 重采样阈值
RESAMPLE_THRESHOLD = 0.5   # 有效粒子比例阈值
```

### 环境适应性调优
- **开阔环境**: 减少粒子数，降低计算负担
- **复杂环境**: 增加粒子数，提高定位精度
- **高动态**: 增大运动噪声，适应快速运动
- **高精度需求**: 减小传感器噪声，提高观测权重

## 故障诊断

### 常见问题
- **定位发散**: 检查地图数据质量和传感器校准
- **收敛缓慢**: 增加粒子数量或调整噪声参数
- **精度不足**: 验证传感器精度和地图分辨率
- **文件错误**: 确认地图文件格式和路径正确

### 调试工具
```python
# 启用详细调试信息
DEBUG_PARTICLES = True     # 显示粒子状态
DEBUG_WEIGHTS = True       # 显示权重分布
DEBUG_RESAMPLING = True    # 显示重采样过程
VERBOSE_OUTPUT = True      # 详细控制台输出
```

## 依赖关系

### 前置条件
必须先完成建图阶段，生成以下文件：
- `../mapping_controller/simple_map_data.txt`
- 或 `../mapping_controller_auto/simple_map_data.txt`

### 文件检测
系统自动检测可用地图文件：
1. 优先加载手动建图数据
2. 如不存在，加载自动建图数据
3. 如都不存在，使用备用简化地图

## 算法扩展

### 高级滤波器
- **卡尔曼滤波**: 线性高斯系统的最优估计
- **扩展卡尔曼滤波**: 非线性系统的近似最优估计
- **无迹卡尔曼滤波**: 非线性系统的高精度估计
- **FastSLAM**: 同时定位与建图

### 传感器扩展
- **视觉传感器**: 相机数据融合
- **IMU集成**: 惯性测量单元数据
- **GPS辅助**: 全局定位系统校正
- **多传感器融合**: 异构传感器数据融合

## 理论基础

### 贝叶斯滤波
粒子滤波是贝叶斯滤波的非参数实现：
```
P(x_t|z_1:t) ∝ P(z_t|x_t) * ∫ P(x_t|x_{t-1}) * P(x_{t-1}|z_1:{t-1}) dx_{t-1}
```

### 蒙特卡洛方法
使用样本近似概率分布：
```
P(x_t|z_1:t) ≈ Σ w_t^i * δ(x_t - x_t^i)
```

本定位系统展示了现代概率机器人学的核心技术，为自主机器人提供可靠的位置估计能力。
