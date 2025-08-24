"""
自动建图控制器 - 基于简单探索算法
在手动建图控制器基础上添加自动探索功能
"""

from controller import Robot, Keyboard
import math
import random

class AutoMappingController:
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
        
        # GPS和指南针（如果有的话）
        try:
            self.gps = self.robot.getDevice('gps')
            self.gps.enable(self.timestep)
            self.has_gps = True
        except Exception:
            self.has_gps = False
            print("Warning: GPS not found")
        
        try:
            self.compass = self.robot.getDevice('compass')
            self.compass.enable(self.timestep)
            self.has_compass = True
        except Exception:
            self.has_compass = False
            print("Warning: Compass not found")
        
        # 简单的数据存储
        self.scan_data = []
        self.position_data = []
        self.step_count = 0
        
        # 自动探索参数 - 极激进探索设置
        self.mode = "auto"  # "auto" 或 "manual"
        self.exploration_time = float('inf')  # 无限探索直到用户按Q
        self.obstacle_threshold = 0.3  # 障碍物检测阈值（米）- 进一步降低
        self.turn_threshold = 0.1  # 转向阈值（极低，只要有一点空间就转）
        self.min_safe_distance = 0.05  # 最小安全距离（几乎贴墙）
        self.force_turn_threshold = 0.25  # 强制转向阈值
        self.turn_time = 0  # 转向计时器
        self.move_direction = 1  # 1=前进, -1=后退, 0=转向
        self.stuck_counter = 0  # 被困计数器
        self.exploration_direction = 1  # 探索偏好方向: 1=右转, -1=左转
        self.continuous_turn_time = 0  # 连续转向时间
        
        print("自动建图控制器启动成功!")
        print("=== 极激进探索模式 ===")
        print("默认: 自动探索模式（极激进自由算法）")
        print("探索时间: 无限制（直到按Q退出）")
        print(f"障碍物阈值: {self.obstacle_threshold}米（极敏感）")
        print(f"转向阈值: {self.turn_threshold}米（极低，最大探索空间）")
        print(f"最小安全距离: {self.min_safe_distance}米（几乎贴墙）")
        print("按M键: 切换手动/自动模式")
        print("手动模式: WASD控制")
        print("Q: 退出并保存数据")
        print("====================")
    
    def get_robot_position(self):
        """获取机器人位置（如果有GPS）"""
        if self.has_gps:
            gps_values = self.gps.getValues()
            return gps_values[0], gps_values[1]
        else:
            # 简单的位置估计（基于步数）
            return self.step_count * 0.01, 0
    
    def get_robot_orientation(self):
        """获取机器人方向（如果有指南针）"""
        if self.has_compass:
            compass_values = self.compass.getValues()
            return math.atan2(compass_values[0], compass_values[1])
        else:
            return 0.0
    
    def get_sensor_distances(self):
        """获取传感器距离数据"""
        lidar_data = self.lidar.getRangeImage()
        if lidar_data:
            num_points = len(lidar_data)
            front = lidar_data[num_points//2] if num_points > 0 else 999
            left = lidar_data[num_points//4] if num_points > 1 else 999
            right = lidar_data[3*num_points//4] if num_points > 2 else 999
            back = lidar_data[0] if num_points > 0 else 999
            
            # 处理无穷大值，设为最大检测距离
            front = min(front, 5.0) if front != float('inf') else 5.0
            left = min(left, 5.0) if left != float('inf') else 5.0
            right = min(right, 5.0) if right != float('inf') else 5.0
            back = min(back, 5.0) if back != float('inf') else 5.0
            
            return front, left, right, back
        return 5.0, 5.0, 5.0, 5.0
    
    def collect_scan_data(self):
        """收集激光雷达数据"""
        front, left, right, back = self.get_sensor_distances()
        
        # 获取位置信息
        x, y = self.get_robot_position()
        angle = self.get_robot_orientation()
        
        # 保存数据
        scan_record = {
            'step': self.step_count,
            'time': self.robot.getTime(),
            'position': (x, y),
            'angle': angle,
            'distances': {
                'front': front,
                'left': left,
                'right': right,
                'back': back
            },
            'min_distance': min([d for d in [front, left, right, back] if d != float('inf')]),
            'avg_distance': sum([d for d in [front, left, right, back] if d != float('inf')]) / 4
        }
        
        self.scan_data.append(scan_record)
        
        # 显示信息
        if self.step_count % 50 == 0:
            mode_str = "自动" if self.mode == "auto" else "手动"
            print(f"[{mode_str}] 步数: {self.step_count}, 位置: ({x:.2f}, {y:.2f})")
            print(f"  传感器: 前{front:.2f}m, 左{left:.2f}m, 右{right:.2f}m, 后{back:.2f}m")
            if self.mode == "auto":
                print(f"  状态: 被困计数{self.stuck_counter}, 探索方向{'右' if self.exploration_direction > 0 else '左'}")
                print(f"  阈值: 障碍{self.obstacle_threshold}m, 转向{self.turn_threshold}m, 安全{self.min_safe_distance}m")
                print(f"  连续转向: {self.continuous_turn_time}步")
    
    def simple_exploration_algorithm(self):
        """极激进自由探索算法 - 最大化探索空间，强制脱困"""
        front, left, right, back = self.get_sensor_distances()
        
        left_speed = 0.0
        right_speed = 0.0
        
        # 极激进探索策略 - 永远不停止探索
        if front > self.obstacle_threshold:
            # 前方相对安全，快速前进
            left_speed = right_speed = 3.0  # 提高前进速度
            self.move_direction = 1
            self.turn_time = 0
            self.stuck_counter = 0
            self.continuous_turn_time = 0
        elif front > self.min_safe_distance:
            # 前方空间很小但还能走，小心前进
            left_speed = right_speed = 1.0
            self.stuck_counter = 0
        else:
            # 前方被阻挡 - 立即开始强制探索
            self.stuck_counter += 1
            self.continuous_turn_time += 1
            
            # 超级宽松的转向条件 - 只要有一丝空间就转
            if right > self.turn_threshold:
                # 右转 - 使用更高速度确保能转出去
                left_speed = 3.0
                right_speed = -3.0
                self.exploration_direction = 1
                print(f"右转脱困: 右侧空间{right:.2f}m")
            elif left > self.turn_threshold:
                # 左转 - 使用更高速度确保能转出去
                left_speed = -3.0
                right_speed = 3.0
                self.exploration_direction = -1
                print(f"左转脱困: 左侧空间{left:.2f}m")
            elif right > 0.05:  # 极低阈值 - 只要传感器能检测到空间
                # 即使空间极小也强制右转
                left_speed = 2.5
                right_speed = -2.5
                print(f"强制右转: 右侧微小空间{right:.2f}m")
            elif left > 0.05:  # 极低阈值 - 只要传感器能检测到空间  
                # 即使空间极小也强制左转
                left_speed = -2.5
                right_speed = 2.5
                print(f"强制左转: 左侧微小空间{left:.2f}m")
            else:
                # 完全被困 - 启动最强脱困模式
                if self.stuck_counter < 5:
                    # 快速后退
                    left_speed = right_speed = -3.0
                    print(f"快速后退脱困: 被困{self.stuck_counter}步")
                elif self.stuck_counter < 15:
                    # 强制大角度转向，不管空间
                    if self.exploration_direction > 0:
                        left_speed = 4.0  # 使用最大转向速度
                        right_speed = -4.0
                        print("强制右转脱困: 最大转速")
                    else:
                        left_speed = -4.0
                        right_speed = 4.0
                        print("强制左转脱困: 最大转速")
                elif self.stuck_counter < 25:
                    # 后退 + 转向组合
                    if self.stuck_counter % 2 == 0:
                        left_speed = right_speed = -2.5
                    else:
                        left_speed = 3.5 * self.exploration_direction
                        right_speed = -3.5 * self.exploration_direction
                    print("后退转向组合脱困")
                else:
                    # 改变探索方向并执行暴力脱困
                    self.exploration_direction *= -1
                    left_speed = 5.0 * self.exploration_direction  # 使用超高速度
                    right_speed = -5.0 * self.exploration_direction
                    self.stuck_counter = 0
                    print("暴力脱困: 改变方向，超高转速")
        
        # 更激进的探索方向变化
        if self.step_count % 50 == 0:  # 更频繁改变方向
            self.exploration_direction *= -1
            print(f"定期改变探索方向: {'右' if self.exploration_direction > 0 else '左'}")
        
        # 增加更多随机探索
        if self.step_count % 30 == 0 and random.random() > 0.5:  # 更频繁的随机转向
            # 随机强力转向
            if random.random() > 0.5:
                left_speed = 3.5
                right_speed = -3.5
                print("随机右转探索")
            else:
                left_speed = -3.5
                right_speed = 3.5
                print("随机左转探索")
        
        # 防止连续转向太久 - 强制前进
        if self.continuous_turn_time > 30:
            left_speed = right_speed = 2.0  # 强制前进
            self.continuous_turn_time = 0
            print("强制前进打破转向循环")
        
        return left_speed, right_speed
    
    def handle_input(self):
        """处理输入（键盘或自动算法）"""
        key = self.keyboard.getKey()
        
        # 检查模式切换
        if key == ord('M') or key == ord('m'):
            self.mode = "manual" if self.mode == "auto" else "auto"
            mode_str = "手动" if self.mode == "manual" else "自动"
            print(f"切换到{mode_str}模式")
        
        # 检查退出
        if key == ord('Q') or key == ord('q'):
            print("准备退出...")
            return False
        
        left_speed = 0.0
        right_speed = 0.0
        
        if self.mode == "auto":
            # 自动探索模式
            if self.step_count < self.exploration_time:
                left_speed, right_speed = self.simple_exploration_algorithm()
            else:
                print("自动探索完成!")
                return False
        else:
            # 手动控制模式
            if key == ord('W') or key == ord('w'):
                left_speed = right_speed = 2.0
                print("前进")
            elif key == ord('S') or key == ord('s'):
                left_speed = right_speed = -2.0
                print("后退")
            elif key == ord('A') or key == ord('a'):
                left_speed = -2.0
                right_speed = 2.0
                print("左转")
            elif key == ord('D') or key == ord('d'):
                left_speed = 2.0
                right_speed = -2.0
                print("右转")
            elif key == ord(' '):  # 空格
                left_speed = right_speed = 0.0
                print("停止")
        
        # 设置电机速度
        self.left_motor.setVelocity(left_speed)
        self.right_motor.setVelocity(right_speed)
        
        return True
    
    def save_simple_map(self):
        """保存简单的地图数据 - 兼容Task 2粒子滤波定位"""
        if not self.scan_data:
            print("没有收集到数据!")
            return
        
        # 创建与手动建图兼容的文件 - Task 2需要这个文件名
        filename = "simple_map_data.txt"
        
        try:
            with open(filename, 'w') as f:
                f.write("=== 自动建图数据 ===\n")
                f.write(f"总步数: {len(self.scan_data)}\n")
                f.write(f"总时间: {self.robot.getTime():.2f}秒\n")
                f.write("建图方式: 自动探索算法\n")
                f.write("\n=== 扫描数据 ===\n")
                f.write("步数,时间,X,Y,角度,前方,左侧,右侧,后方,最小距离\n")
                
                for record in self.scan_data:
                    f.write(f"{record['step']},{record['time']:.2f},"
                           f"{record['position'][0]:.3f},{record['position'][1]:.3f},"
                           f"{record['angle']:.3f},"
                           f"{record['distances']['front']:.2f},"
                           f"{record['distances']['left']:.2f},"
                           f"{record['distances']['right']:.2f},"
                           f"{record['distances']['back']:.2f},"
                           f"{record['min_distance']:.2f}\n")
                
                # 统计信息
                f.write("\n=== 统计信息 ===\n")
                all_distances = []
                for record in self.scan_data:
                    distances = record['distances']
                    for dist in distances.values():
                        if dist != float('inf') and dist > 0:
                            all_distances.append(dist)
                
                if all_distances:
                    f.write(f"平均距离: {sum(all_distances)/len(all_distances):.2f}m\n")
                    f.write(f"最小距离: {min(all_distances):.2f}m\n")
                    f.write(f"最大距离: {max(all_distances):.2f}m\n")
                    f.write(f"有效测量次数: {len(all_distances)}\n")
            
            print(f" 自动建图数据已保存到: {filename}")
            print("   此文件与Task 2粒子滤波定位完全兼容！")
            
            # 同时创建一个带时间戳的备份文件
            import time
            backup_filename = f"auto_map_backup_{int(time.time())}.txt"
            with open(backup_filename, 'w') as f:
                with open(filename, 'r') as source:
                    f.write(source.read())
            print(f"   备份文件: {backup_filename}")
            
            # 也创建可视化文件
            self.create_simple_visualization()
            print(" 完整自动建图文件已生成，包括:")
            print("   - simple_map_data.txt (Task 2兼容的主文件)")
            print(f"   - {backup_filename} (带时间戳的备份)")
            print("   - auto_map_visualization.txt (ASCII可视化)")  
            print("   - auto_map_image.ppm (图片文件，可用于报告)")
            print("   Task 2粒子滤波现在可以直接使用这些建图结果！")
            
        except Exception as e:
            print(f"保存文件时出错: {e}")
    
    def create_simple_visualization(self):
        """创建改进的ASCII艺术地图和PPM图片 - 修复地图生成逻辑"""
        try:
            # 创建ASCII文本地图
            with open("auto_map_visualization.txt", 'w') as f:
                f.write("=== 自动建图可视化 ===\n")
                f.write("说明: . = 空闲空间, # = 障碍物, R = 机器人路径\n")
                f.write("建图方式: 自动探索算法（改进版）\n\n")
                
                # 改进的网格地图 - 动态计算范围
                grid_size = 60  # 增大网格以获得更好分辨率
                
                # 首先找到实际的坐标范围
                min_x = min_y = float('inf')
                max_x = max_y = float('-inf')
                
                for record in self.scan_data:
                    x, y = record['position']
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
                
                # 添加边距
                margin = 2.0
                min_x -= margin
                max_x += margin
                min_y -= margin
                max_y += margin
                
                range_x = max_x - min_x
                range_y = max_y - min_y
                
                f.write(f"地图范围: X[{min_x:.1f}, {max_x:.1f}], Y[{min_y:.1f}, {max_y:.1f}]\n")
                f.write(f"网格尺寸: {grid_size}x{grid_size}\n\n")
                
                grid = [['.' for _ in range(grid_size)] for _ in range(grid_size)]
                
                # 标记机器人路径和正确计算障碍物位置
                for record in self.scan_data[::2]:  # 每2个记录取一个以减少密度
                    x, y = record['position']
                    angle = record['angle']
                    
                    # 转换为网格坐标 - 使用实际范围
                    grid_x = int((x - min_x) / range_x * (grid_size - 1))
                    grid_y = int((y - min_y) / range_y * (grid_size - 1))
                    
                    # 标记机器人路径
                    if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                        grid[grid_y][grid_x] = 'R'
                    
                    # 根据传感器数据正确推断障碍物位置
                    distances = record['distances']
                    
                    # 前方障碍物
                    if distances['front'] < 1.5:  # 1.5米内有障碍物
                        obs_x = x + distances['front'] * math.cos(angle)
                        obs_y = y + distances['front'] * math.sin(angle)
                        obs_grid_x = int((obs_x - min_x) / range_x * (grid_size - 1))
                        obs_grid_y = int((obs_y - min_y) / range_y * (grid_size - 1))
                        if 0 <= obs_grid_x < grid_size and 0 <= obs_grid_y < grid_size:
                            grid[obs_grid_y][obs_grid_x] = '#'
                    
                    # 左侧障碍物
                    if distances['left'] < 1.5:
                        left_angle = angle + math.pi/2
                        obs_x = x + distances['left'] * math.cos(left_angle)
                        obs_y = y + distances['left'] * math.sin(left_angle)
                        obs_grid_x = int((obs_x - min_x) / range_x * (grid_size - 1))
                        obs_grid_y = int((obs_y - min_y) / range_y * (grid_size - 1))
                        if 0 <= obs_grid_x < grid_size and 0 <= obs_grid_y < grid_size:
                            grid[obs_grid_y][obs_grid_x] = '#'
                    
                    # 右侧障碍物
                    if distances['right'] < 1.5:
                        right_angle = angle - math.pi/2
                        obs_x = x + distances['right'] * math.cos(right_angle)
                        obs_y = y + distances['right'] * math.sin(right_angle)
                        obs_grid_x = int((obs_x - min_x) / range_x * (grid_size - 1))
                        obs_grid_y = int((obs_y - min_y) / range_y * (grid_size - 1))
                        if 0 <= obs_grid_x < grid_size and 0 <= obs_grid_y < grid_size:
                            grid[obs_grid_y][obs_grid_x] = '#'
                    
                    # 后方障碍物
                    if distances['back'] < 1.5:
                        back_angle = angle + math.pi
                        obs_x = x + distances['back'] * math.cos(back_angle)
                        obs_y = y + distances['back'] * math.sin(back_angle)
                        obs_grid_x = int((obs_x - min_x) / range_x * (grid_size - 1))
                        obs_grid_y = int((obs_y - min_y) / range_y * (grid_size - 1))
                        if 0 <= obs_grid_x < grid_size and 0 <= obs_grid_y < grid_size:
                            grid[obs_grid_y][obs_grid_x] = '#'
                
                # 打印网格（显示更多行以便观察）
                for i, row in enumerate(grid):
                    if i < 30:  # 显示前30行
                        f.write(''.join(row) + '\n')
                    elif i == 30:
                        f.write("... (省略其余行，完整地图见PPM图片文件)\n")
                        break
                
                # 统计信息
                robot_count = sum(row.count('R') for row in grid)
                obstacle_count = sum(row.count('#') for row in grid)
                free_count = sum(row.count('.') for row in grid)
                
                f.write("\n地图统计:\n")
                f.write(f"机器人路径点: {robot_count}\n")
                f.write(f"障碍物点: {obstacle_count}\n")
                f.write(f"自由空间点: {free_count}\n")
                f.write(f"自动探索共访问了 {len(self.scan_data)} 个位置\n")
            
            print("自动建图可视化已保存到: auto_map_visualization.txt")
            
            # 创建改进的PPM图片文件
            self.create_ppm_image(grid)
            
        except Exception as e:
            print(f"创建可视化时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def create_ppm_image(self, grid):
        """创建改进的PPM格式地图图片（无需外部库）"""
        try:
            grid_size = len(grid)
            pixel_size = 8  # 每个网格单元对应8x8像素（稍微减小以适应更大网格）
            img_size = grid_size * pixel_size
            
            with open("auto_map_image.ppm", 'w') as f:
                # PPM头部
                f.write("P3\n")
                f.write("# Auto-generated map from exploration algorithm\n")
                f.write(f"{img_size} {img_size}\n")
                f.write("255\n")
                
                # 生成像素数据
                for grid_y in range(grid_size):
                    for pixel_y in range(pixel_size):
                        for grid_x in range(grid_size):
                            cell = grid[grid_y][grid_x]
                            
                            # 设置颜色 - 改进配色方案
                            if cell == '#':  # 障碍物 - 深蓝色（更明显）
                                color = "0 0 128"
                            elif cell == 'R':  # 机器人路径 - 亮红色
                                color = "255 0 0"
                            else:  # 空闲空间 - 浅灰色（比纯白更容易看清）
                                color = "240 240 240"
                            
                            # 每个网格单元重复pixel_size次
                            for pixel_x in range(pixel_size):
                                f.write(f"{color} ")
                        f.write("\n")
            
            print("自动建图图片已保存到: auto_map_image.ppm")
            print("提示: 机器人路径为红色，障碍物为深蓝色，自由空间为浅灰色")
            print(f"图片尺寸: {img_size}x{img_size} 像素")
            
        except Exception as e:
            print(f"创建PPM图片时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """主循环"""
        print("开始自动建图! 默认自动探索，按M切换手动模式...")
        
        try:
            while self.robot.step(self.timestep) != -1:
                # 处理输入（自动或手动）
                if not self.handle_input():
                    break
                
                # 收集传感器数据
                self.collect_scan_data()
                
                # 增加步数计数
                self.step_count += 1
        
        except KeyboardInterrupt:
            print("用户中断程序")
        except Exception as e:
            print(f"程序运行时出错: {e}")
        finally:
            # 保存数据
            print("保存自动建图数据...")
            self.save_simple_map()
            print("自动建图完成!")

# 主程序
if __name__ == "__main__":
    try:
        controller = AutoMappingController()
        controller.run()
    except Exception as e:
        print(f"控制器启动失败: {e}")
        print("请检查Webots环境设置")
