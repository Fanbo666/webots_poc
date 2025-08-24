"""
测试地图加载功能（独立于Webots）
"""

import math

def test_load_map():
    """测试从Task 1加载地图数据"""
    map_data = {
        'obstacles': [],
        'free_space': [],
        'scan_points': []
    }
    
    mapping_data_path = "../mapping_controller/simple_map_data.txt"
    
    try:
        with open(mapping_data_path, 'r') as f:
            lines = f.readlines()
            
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
                            
                            map_data['scan_points'].append({
                                'x': x, 'y': y, 'angle': angle,
                                'distances': {
                                    'front': front_dist,
                                    'left': left_dist,
                                    'right': right_dist,
                                    'back': back_dist
                                }
                            })
                            
                            if min_dist < 1.0:
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
                            
                            map_data['free_space'].append((x, y))
                            
                        except ValueError:
                            continue
        
        print(" 成功加载Task 1地图数据:")
        print(f"   - 扫描点: {len(map_data['scan_points'])} 个")
        print(f"   - 自由空间: {len(map_data['free_space'])} 个")
        print(f"   - 推断障碍物: {len(map_data['obstacles'])} 个")
        
        # 显示一些示例数据
        if map_data['scan_points']:
            first_point = map_data['scan_points'][0]
            print(f"\n📍 第一个扫描点示例:")
            print(f"   位置: ({first_point['x']:.3f}, {first_point['y']:.3f})")
            print(f"   角度: {first_point['angle']:.3f}")
            print(f"   距离: 前{first_point['distances']['front']:.2f}m, "
                  f"左{first_point['distances']['left']:.2f}m")
        
        if map_data['obstacles']:
            print(f"\n🚧 前3个障碍物位置:")
            for i, (ox, oy) in enumerate(map_data['obstacles'][:3]):
                print(f"   障碍物{i+1}: ({ox:.3f}, {oy:.3f})")
        
        return True
        
    except FileNotFoundError:
        print(" 警告: 找不到Task 1的地图数据文件")
        print(f"   预期路径: {mapping_data_path}")
        return False
    
    except Exception as e:
        print(f" 读取地图数据时出错: {e}")
        return False

if __name__ == "__main__":
    print("=== Task 1地图数据加载测试 ===")
    success = test_load_map()
    
    if success:
        print("\n 地图加载测试通过！Task 2可以正确使用Task 1的数据")
    else:
        print("\n 请先完成Task 1建图，或检查文件路径")
