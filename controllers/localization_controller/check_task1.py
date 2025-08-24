#!/usr/bin/env python3
"""
Task 1完成状态检查器
运行此脚本验证Task 1是否已正确完成
"""

import os

def check_task1_completion():
    """检查Task 1是否完成"""
    print("=== Task 1 完成状态检查 ===\n")
    
    # 检查必需文件
    required_files = [
        "../mapping_controller/simple_map_data.txt",
        "../mapping_controller/map_image.ppm",
        "../mapping_controller/simple_map_visualization.txt"
    ]
    
    all_good = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f" {file_path} - 存在 ({file_size} 字节)")
        else:
            print(f" {file_path} - 缺失")
            all_good = False
    
    # 检查数据文件内容
    map_data_path = "../mapping_controller/simple_map_data.txt"
    if os.path.exists(map_data_path):
        try:
            with open(map_data_path, 'r') as f:
                lines = f.readlines()
                data_lines = [line for line in lines if ',' in line and not line.startswith('=')]
                
                if len(data_lines) > 50:  # 至少50个数据点
                    print(f" 地图数据质量检查 - 包含 {len(data_lines)} 个扫描点")
                else:
                    print(f"  地图数据可能不足 - 只有 {len(data_lines)} 个扫描点")
                    print("   建议：重新运行mapping_controller，收集更多数据")
                    
        except Exception as e:
            print(f" 读取地图数据失败: {e}")
            all_good = False
    
    print("\n" + "="*50)
    
    if all_good:
        print(" Task 1 已正确完成！可以运行 Task 2")
        print("\n下一步:")
        print("1. 在Webots中设置控制器为 localization_controller.py")
        print("2. 运行仿真开始粒子滤波定位")
    else:
        print(" Task 1 未完成或存在问题")
        print("\n请执行以下步骤:")
        print("1. 在Webots中设置控制器为 mapping_controller.py")
        print("2. 使用WASD控制机器人探索环境")
        print("3. 按Q保存地图数据")
        print("4. 重新运行此检查脚本")
    
    return all_good

if __name__ == "__main__":
    check_task1_completion()
