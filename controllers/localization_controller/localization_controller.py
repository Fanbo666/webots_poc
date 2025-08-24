"""
简单粒子滤波定位控制器 - 无外部依赖版本
基于Task 1生成的地图进行机器人定位
"""

from controller import Robot, Keyboard
import math
import random

class Particle:
    """粒子类 - 表示机器人可能的位置和方向"""
    def __init__(self, x=0, y=0, theta=0, weight=1.0):
        self.x = x          # X坐标
        self.y = y          # Y坐标  
        self.theta = theta  # 方向角
        self.weight = weight # 权重

class SimpleParticleFilter:
    def __init__(self):
        # 初始化机器人
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())
        
        # 获取设备
        self.left_motor = self.robot.getDevice('left wheel motor')
        self.right_motor = self.robot.getDevice('right wheel motor')
        self.lidar = self.robot.getDevice('LDS-01')
        self.keyboard = Keyboard()
        
        # 启用设备
        self.left_motor.setPosition(float('inf'))
        self.right_motor.setPosition(float('inf'))
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)
        self.lidar.enable(self.timestep)
        self.keyboard.enable(self.timestep)
        
        # GPS用于验证（实际定位不使用）
        try:
            self.gps = self.robot.getDevice('gps')
            self.gps.enable(self.timestep)
            self.has_gps = True
        except Exception:
            self.has_gps = False
        
        # 粒子滤波参数
        self.num_particles = 100  # 粒子数量
        self.particles = []
        
        # 简单地图数据（基于Task 1的结果）
        self.map_data = self.load_simple_map()
        
        # 初始化粒子
        self.initialize_particles()
        
        # 估计的位置
        self.estimated_x = 0
        self.estimated_y = 0
        self.estimated_theta = 0
        
        self.step_count = 0
        self.localization_results = []
        
        print("粒子滤波定位控制器启动成功!")
        print("=== 控制说明 ===")
        print("W: 前进")
        print("S: 后退") 
        print("A: 左转")
        print("D: 右转")
        print("空格: 停止")
        print("Q: 退出并保存结果")
        print("==================")
    
    def load_simple_map(self):
        """从Task 1的mapping结果加载地图数据 - 支持手动和自动建图"""
        map_data = {
            'obstacles': [],  # 障碍物位置
            'free_space': [],  # 自由空间
            'scan_points': []  # 原始扫描点
        }
        
        # 尝试读取Task 1生成的地图数据 - 支持手动和自动建图
        mapping_data_paths = [
            "../mapping_controller/simple_map_data.txt",      # 手动建图结果
            "../mapping_controller_auto/simple_map_data.txt"  # 自动建图结果
        ]
        
        loaded = False
        for mapping_data_path in mapping_data_paths:
            try:
                with open(mapping_data_path, 'r') as f:
                    lines = f.readlines()
                    
                    # 跳过头部，找到数据行
                    data_start = False
                    for line in lines:
                        if "步数,时间,X,Y,角度,前方,左侧,右侧,后方,最小距离" in line:
                            data_start = True
                            continue
                        
                        if data_start and "===" not in line and line.strip():
                            parts = line.strip().split(',')
                            if len(parts) >= 10:
                                try:
                                    x = float(parts[2])
                                    y = float(parts[3])
                                    angle = float(parts[4])
                                    front_dist = float(parts[5])
                                    left_dist = float(parts[6])
                                    right_dist = float(parts[7])
                                    back_dist = float(parts[8])
                                    min_dist = float(parts[9])
                                    
                                    # 记录扫描点
                                    map_data['scan_points'].append({
                                        'x': x, 'y': y, 'angle': angle,
                                        'distances': {
                                            'front': front_dist,
                                            'left': left_dist,
                                            'right': right_dist,
                                            'back': back_dist
                                        }
                                    })
                                    
                                    # 如果检测到近距离障碍物，推断障碍物位置
                                    if min_dist < 1.0:  # 1米内认为有障碍物
                                        # 计算障碍物可能的位置
                                        for direction, dist in [('front', front_dist), ('left', left_dist), 
                                                              ('right', right_dist), ('back', back_dist)]:
                                            if dist < 1.0:
                                                if direction == 'front':
                                                    obs_x = x + dist * math.cos(angle)
                                                    obs_y = y + dist * math.sin(angle)
                                                elif direction == 'left':
                                                    obs_x = x + dist * math.cos(angle + math.pi/2)
                                                    obs_y = y + dist * math.sin(angle + math.pi/2)
                                                elif direction == 'right':
                                                    obs_x = x + dist * math.cos(angle - math.pi/2)
                                                    obs_y = y + dist * math.sin(angle - math.pi/2)
                                                else:  # back
                                                    obs_x = x + dist * math.cos(angle + math.pi)
                                                    obs_y = y + dist * math.sin(angle + math.pi)
                                                
                                                map_data['obstacles'].append((obs_x, obs_y))
                                    
                                    # 机器人经过的位置是自由空间
                                    map_data['free_space'].append((x, y))
                                    
                                except ValueError:
                                    continue
                
                print(" 成功加载Task 1地图数据:")
                print(f"   - 文件: {mapping_data_path}")
                print(f"   - 扫描点: {len(map_data['scan_points'])} 个")
                print(f"   - 自由空间: {len(map_data['free_space'])} 个")
                print(f"   - 推断障碍物: {len(map_data['obstacles'])} 个")
                loaded = True
                break
                
            except FileNotFoundError:
                continue  # 尝试下一个路径
            except Exception as e:
                print(f" 读取地图数据时出错 ({mapping_data_path}): {e}")
                continue
        
        if not loaded:
            print(" 警告: 找不到任何Task 1的地图数据文件")
            print("   尝试的路径:")
            for path in mapping_data_paths:
                print(f"   - {path}")
            print("   使用备用简化地图...")
            
            # 备用简化地图（如果Task 1数据不存在）
            map_data['obstacles'] = [
                (2.5, 0.5), (2.5, -0.5), (-2.5, 0.5), (-2.5, -0.5),
                (0, 2.5), (0, -2.5), (1.5, 1.5), (-1.5, -1.5)
            ]
            
            for x in range(-30, 31, 5):
                for y in range(-30, 31, 5):
                    x_pos = x / 10.0
                    y_pos = y / 10.0
                    is_free = True
                    for obs_x, obs_y in map_data['obstacles']:
                        dist = math.sqrt((x_pos - obs_x)**2 + (y_pos - obs_y)**2)
                        if dist < 0.8:
                            is_free = False
                            break
                    if is_free:
                        map_data['free_space'].append((x_pos, y_pos))
        
        return map_data
    
    def initialize_particles(self):
        """初始化粒子群"""
        self.particles = []
        
        # 在自由空间中随机分布粒子
        for i in range(self.num_particles):
            if self.map_data['free_space']:
                # 从自由空间中随机选择位置
                x, y = random.choice(self.map_data['free_space'])
                # 添加一些随机噪声
                x += random.uniform(-0.2, 0.2)
                y += random.uniform(-0.2, 0.2)
            else:
                # 如果没有地图数据，在较小区域内随机分布
                x = random.uniform(-2, 2)
                y = random.uniform(-2, 2)
            
            theta = random.uniform(0, 2 * math.pi)
            self.particles.append(Particle(x, y, theta, 1.0/self.num_particles))
        
        print(f"初始化了 {len(self.particles)} 个粒子")
    
    def predict_particles(self, left_speed, right_speed, dt):
        """预测步骤：根据运动模型更新粒子位置"""
        # 简单的差分驱动模型
        wheel_radius = 0.0325  # 轮子半径（米）
        wheel_base = 0.16      # 轮距（米）
        
        for particle in self.particles:
            # 计算线速度和角速度
            v_left = left_speed * wheel_radius
            v_right = right_speed * wheel_radius
            
            linear_vel = (v_left + v_right) / 2
            angular_vel = (v_right - v_left) / wheel_base
            
            # 更新粒子位置（添加噪声模拟不确定性）
            noise_x = random.uniform(-0.01, 0.01)
            noise_y = random.uniform(-0.01, 0.01) 
            noise_theta = random.uniform(-0.05, 0.05)
            
            particle.x += (linear_vel * math.cos(particle.theta) + noise_x) * dt
            particle.y += (linear_vel * math.sin(particle.theta) + noise_y) * dt
            particle.theta += (angular_vel + noise_theta) * dt
            
            # 保持角度在 [0, 2π] 范围内
            particle.theta = particle.theta % (2 * math.pi)
    
    def update_weights(self, sensor_data):
        """更新步骤：根据传感器数据更新粒子权重"""
        total_weight = 0
        
        for particle in self.particles:
            # 计算粒子位置的期望传感器读数
            expected_readings = self.simulate_sensor_reading(particle.x, particle.y, particle.theta)
            
            # 计算实际读数与期望读数的似然性
            likelihood = self.calculate_likelihood(sensor_data, expected_readings)
            
            particle.weight = likelihood
            total_weight += likelihood
        
        # 归一化权重
        if total_weight > 0:
            for particle in self.particles:
                particle.weight /= total_weight
        else:
            # 如果所有权重都是0，重新均匀分布
            for particle in self.particles:
                particle.weight = 1.0 / self.num_particles
    
    def simulate_sensor_reading(self, x, y, theta):
        """模拟在给定位置的传感器读数"""
        readings = {'front': 5.0, 'left': 5.0, 'right': 5.0, 'back': 5.0}
        
        # 计算四个方向
        directions = {
            'front': theta,
            'right': theta - math.pi/2,
            'back': theta + math.pi,
            'left': theta + math.pi/2
        }
        
        for direction_name, angle in directions.items():
            min_dist = 5.0  # 最大检测距离
            
            # 检查到最近障碍物的距离
            for obs_x, obs_y in self.map_data['obstacles']:
                # 计算到障碍物的距离
                dx = obs_x - x
                dy = obs_y - y
                
                # 检查障碍物是否在这个方向上
                obs_angle = math.atan2(dy, dx)
                angle_diff = abs(obs_angle - angle)
                angle_diff = min(angle_diff, 2*math.pi - angle_diff)  # 处理角度环绕
                
                if angle_diff < math.pi/4:  # 45度范围内
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < min_dist:
                        min_dist = dist
            
            readings[direction_name] = min_dist
        
        return readings
    
    def calculate_likelihood(self, actual, expected):
        """计算传感器读数的似然性"""
        likelihood = 1.0
        sigma = 0.3  # 传感器噪声标准差
        
        for direction in ['front', 'left', 'right', 'back']:
            actual_dist = actual.get(direction, 5.0)
            expected_dist = expected.get(direction, 5.0)
            
            # 高斯似然
            error = abs(actual_dist - expected_dist)
            likelihood *= math.exp(-(error**2) / (2 * sigma**2))
        
        return likelihood
    
    def resample_particles(self):
        """重采样步骤：根据权重重新采样粒子"""
        new_particles = []
        
        # 计算累积权重
        weights = [p.weight for p in self.particles]
        
        # 使用轮盘赌算法重采样
        for i in range(self.num_particles):
            # 随机选择一个权重值
            rand_weight = random.uniform(0, sum(weights))
            
            cumulative_weight = 0
            for j, particle in enumerate(self.particles):
                cumulative_weight += particle.weight
                if cumulative_weight >= rand_weight:
                    # 复制这个粒子（添加少量噪声）
                    new_particle = Particle(
                        particle.x + random.uniform(-0.05, 0.05),
                        particle.y + random.uniform(-0.05, 0.05), 
                        particle.theta + random.uniform(-0.1, 0.1),
                        1.0 / self.num_particles
                    )
                    new_particles.append(new_particle)
                    break
        
        self.particles = new_particles
    
    def estimate_position(self):
        """估计机器人位置（加权平均）"""
        total_weight = sum(p.weight for p in self.particles)
        
        if total_weight > 0:
            self.estimated_x = sum(p.x * p.weight for p in self.particles) / total_weight
            self.estimated_y = sum(p.y * p.weight for p in self.particles) / total_weight
            
            # 角度的加权平均需要特殊处理
            cos_sum = sum(math.cos(p.theta) * p.weight for p in self.particles) / total_weight
            sin_sum = sum(math.sin(p.theta) * p.weight for p in self.particles) / total_weight
            self.estimated_theta = math.atan2(sin_sum, cos_sum)
    
    def get_sensor_data(self):
        """获取传感器数据"""
        lidar_data = self.lidar.getRangeImage()
        
        if lidar_data:
            num_points = len(lidar_data)
            return {
                'front': lidar_data[num_points//2] if num_points > 0 else 5.0,
                'left': lidar_data[num_points//4] if num_points > 1 else 5.0,
                'right': lidar_data[3*num_points//4] if num_points > 2 else 5.0,
                'back': lidar_data[0] if num_points > 0 else 5.0
            }
        else:
            return {'front': 5.0, 'left': 5.0, 'right': 5.0, 'back': 5.0}
    
    def handle_keyboard(self):
        """处理键盘输入"""
        key = self.keyboard.getKey()
        
        left_speed = 0.0
        right_speed = 0.0
        
        if key == ord('W') or key == ord('w'):
            left_speed = right_speed = 2.0
        elif key == ord('S') or key == ord('s'):
            left_speed = right_speed = -2.0
        elif key == ord('A') or key == ord('a'):
            left_speed = -2.0
            right_speed = 2.0
        elif key == ord('D') or key == ord('d'):
            left_speed = 2.0
            right_speed = -2.0
        elif key == ord(' '):
            left_speed = right_speed = 0.0
        elif key == ord('Q') or key == ord('q'):
            return False, left_speed, right_speed
        
        self.left_motor.setVelocity(left_speed)
        self.right_motor.setVelocity(right_speed)
        
        return True, left_speed, right_speed
    
    def save_results(self):
        """保存定位结果"""
        try:
            with open("localization_results.txt", 'w') as f:
                f.write("=== 粒子滤波定位结果 ===\n")
                f.write(f"总步数: {len(self.localization_results)}\n")
                f.write(f"粒子数量: {self.num_particles}\n\n")
                
                f.write("步数,时间,估计X,估计Y,估计角度,真实X,真实Y,误差距离\n")
                
                for result in self.localization_results:
                    f.write(f"{result['step']},{result['time']:.2f},"
                           f"{result['estimated_x']:.3f},{result['estimated_y']:.3f},"
                           f"{result['estimated_theta']:.3f},"
                           f"{result['true_x']:.3f},{result['true_y']:.3f},"
                           f"{result['error']:.3f}\n")
                
                # 计算统计信息
                if self.localization_results:
                    errors = [r['error'] for r in self.localization_results]
                    f.write("\n=== 统计信息 ===\n")
                    f.write(f"平均定位误差: {sum(errors)/len(errors):.3f}米\n")
                    f.write(f"最大定位误差: {max(errors):.3f}米\n")
                    f.write(f"最小定位误差: {min(errors):.3f}米\n")
            
            print("定位结果已保存到: localization_results.txt")
            
        except Exception as e:
            print(f"保存结果时出错: {e}")
    
    def run(self):
        """主循环"""
        print("开始粒子滤波定位! 使用WASD控制机器人...")
        
        try:
            while self.robot.step(self.timestep) != -1:
                # 处理键盘输入
                continue_run, left_speed, right_speed = self.handle_keyboard()
                if not continue_run:
                    break
                
                # 获取传感器数据
                sensor_data = self.get_sensor_data()
                
                # 执行粒子滤波算法
                dt = self.timestep / 1000.0  # 转换为秒
                
                # 1. 预测步骤
                self.predict_particles(left_speed, right_speed, dt)
                
                # 2. 更新权重
                self.update_weights(sensor_data)
                
                # 3. 重采样
                if self.step_count % 10 == 0:  # 每10步重采样一次
                    self.resample_particles()
                
                # 4. 估计位置
                self.estimate_position()
                
                # 记录结果（如果有GPS用于验证）
                if self.has_gps:
                    true_pos = self.gps.getValues()
                    true_x, true_y = true_pos[0], true_pos[1]
                    error = math.sqrt((self.estimated_x - true_x)**2 + (self.estimated_y - true_y)**2)
                else:
                    true_x, true_y, error = 0, 0, 0
                
                result = {
                    'step': self.step_count,
                    'time': self.robot.getTime(),
                    'estimated_x': self.estimated_x,
                    'estimated_y': self.estimated_y, 
                    'estimated_theta': self.estimated_theta,
                    'true_x': true_x,
                    'true_y': true_y,
                    'error': error
                }
                self.localization_results.append(result)
                
                # 显示信息
                if self.step_count % 50 == 0:
                    print(f"步数: {self.step_count}")
                    print(f"估计位置: ({self.estimated_x:.2f}, {self.estimated_y:.2f})")
                    if self.has_gps:
                        print(f"真实位置: ({true_x:.2f}, {true_y:.2f})")
                        print(f"定位误差: {error:.2f}米")
                    print("---")
                
                self.step_count += 1
                
        except KeyboardInterrupt:
            print("用户中断程序")
        except Exception as e:
            print(f"程序运行时出错: {e}")
        finally:
            print("保存定位结果...")
            self.save_results()
            print("定位测试完成!")

# 主程序
if __name__ == "__main__":
    try:
        controller = SimpleParticleFilter()
        controller.run()
    except Exception as e:
        print(f"控制器启动失败: {e}")
        print("请检查Webots环境设置")
