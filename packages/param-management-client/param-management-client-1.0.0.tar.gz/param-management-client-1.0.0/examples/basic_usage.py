#!/usr/bin/env python3
"""
参数管理系统 Python 客户端基本使用示例
"""
from param_management_client import ParameterClient


def main():
    """基本使用示例"""
    print("=== 参数管理系统 Python 客户端基本使用示例 ===")
    
    # 创建客户端
    client = ParameterClient(
        host="localhost",
        port=8000,
        project_name="energy_optimization_params"
    )
    
    # 获取项目对象
    project = client.get_project()
    
    print(f"项目: {project.name} ({project.name_en})")
    print(f"描述: {project.description}")
    print(f"时间范围: {project.time_horizon} 年 ({project.start_year}-{project.end_year})")
    print(f"参数分类: {project.categories}")
    
    # 访问风能参数分类
    wind_params = project.wind_params
    print(f"\n风能参数分类: {wind_params.name} ({wind_params.name_en})")
    print(f"描述: {wind_params.description}")
    print(f"参数列表: {wind_params.list_parameters()}")
    
    # 访问具体参数
    capital_ratio = wind_params.capital_ratio
    print(f"\n资本比例参数:")
    print(f"  名称: {capital_ratio.name} ({capital_ratio.name_en})")
    print(f"  值: {capital_ratio.value}")
    print(f"  单位: {capital_ratio.unit}")
    print(f"  描述: {capital_ratio.description}")
    print(f"  类型: {capital_ratio.param_type}")
    print(f"  是否列表: {capital_ratio.is_list}")
    
    # 访问列表参数
    electricity_price = wind_params.electricity_price
    print(f"\n电价参数:")
    print(f"  名称: {electricity_price.name} ({electricity_price.name_en})")
    print(f"  值: {electricity_price.value[:3]}...")
    print(f"  单位: {electricity_price.unit}")
    print(f"  类型: {electricity_price.param_type}")
    print(f"  是否列表: {electricity_price.is_list}")
    print(f"  列表长度: {len(electricity_price)}")
    
    # 遍历列表参数
    print(f"\n电价列表 (共{len(electricity_price)}年):")
    for i, price in enumerate(electricity_price):
        year = project.start_year + i * project.year_step
        print(f"  {year}年: {price} {electricity_price.unit}")
    
    # 访问其他分类
    print(f"\n储能参数: {project.storage_params}")
    print(f"储能比例: {project.storage_params.energy_storage_ratio}")


if __name__ == "__main__":
    main()
