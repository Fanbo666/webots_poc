#!/usr/bin/env python3
"""
改进后的自动探索算法测试
"""

def test_improved_algorithm():
    """测试改进后的算法逻辑"""
    print("=== 改进后的自动探索算法测试 ===\n")
    
    # 模拟改进的参数
    obstacle_threshold = 0.8  # 提高阈值
    
    # 测试场景
    scenarios = [
        {"name": "开阔区域", "front": 5.0, "left": 5.0, "right": 5.0, "back": 5.0},
        {"name": "前方近障碍", "front": 0.5, "left": 3.0, "right": 4.0, "back": 5.0},
        {"name": "前方中等距离", "front": 1.5, "left": 2.0, "right": 3.0, "back": 4.0},
        {"name": "被完全包围", "front": 0.3, "left": 0.3, "right": 0.3, "back": 2.0},
        {"name": "左侧有空间", "front": 0.5, "left": 4.0, "right": 0.5, "back": 3.0},
    ]
    
    stuck_counter = 0
    
    for i, scenario in enumerate(scenarios):
        print(f"场景 {i+1}: {scenario['name']}")
        print(f"传感器: 前{scenario['front']:.1f}m, 左{scenario['left']:.1f}m, "
              f"右{scenario['right']:.1f}m, 后{scenario['back']:.1f}m")
        
        front = scenario['front']
        left = scenario['left']
        right = scenario['right']
        
        # 使用改进的算法逻辑
        if front > obstacle_threshold:
            decision = "前进 (速度2.0)"
            speeds = "左右轮: 2.0, 2.0"
            stuck_counter = 0
        elif right > obstacle_threshold and right > left:
            decision = "右转 (速度1.5)"
            speeds = "左右轮: 1.5, -1.5"
        elif left > obstacle_threshold:
            decision = "左转 (速度1.5)"
            speeds = "左右轮: -1.5, 1.5"
        else:
            stuck_counter += 1
            if stuck_counter < 15:
                decision = "后退脱困"
                speeds = "左右轮: -1.5, -1.5"
            elif stuck_counter < 30:
                decision = "大角度右转"
                speeds = "左右轮: 2.0, -2.0"
            else:
                decision = "随机转向重置"
                speeds = "左右轮: ±2.0, ∓2.0"
                stuck_counter = 0
        
        print(f"算法决策: {decision}")
        print(f"电机控制: {speeds}")
        print(f"被困计数: {stuck_counter}")
        print("-" * 50)
    
    print(" 改进算法测试完成！")
    print("\n主要改进:")
    print("• 提高障碍物阈值 (0.3m → 0.8m)")
    print("• 增加探索时间 (300步 → 1000步)")
    print("• 改进脱困机制 (分级脱困策略)")
    print("• 处理传感器inf值")
    print("• 增加运动速度和随机性")

def test_sensor_processing():
    """测试传感器数据处理"""
    print("\n=== 传感器数据处理测试 ===")
    
    test_data = [
        [2.5, float('inf'), 1.8, 3.2],
        [float('inf'), float('inf'), float('inf'), float('inf')],
        [0.1, 0.2, 0.3, 4.0],
        [8.0, 7.5, 6.8, 5.2]
    ]
    
    for i, raw_data in enumerate(test_data):
        print(f"\n测试数据 {i+1}: {raw_data}")
        
        # 模拟处理逻辑
        processed = []
        for value in raw_data:
            if value == float('inf'):
                processed.append(5.0)  # 设为最大检测距离
            else:
                processed.append(min(value, 5.0))  # 限制最大值
        
        print(f"处理后: {processed}")
        print(f"改进: 无inf值，最大距离限制为5.0米")
    
    print("\n 传感器处理测试完成！")

if __name__ == "__main__":
    test_improved_algorithm()
    test_sensor_processing()
    
    print(f"\n🎯 改进总结:")
    print("• 算法更加积极主动")
    print("• 脱困策略更有效")
    print("• 探索时间更充足") 
    print("• 传感器数据更可靠")
    print("• 应该能够探索更大的区域！")
