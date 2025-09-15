#!/usr/bin/env python3
"""
参数管理系统 Python 客户端与Pyomo集成示例
"""
from param_management_client import ParameterClient

try:
    import pyomo.environ as pyo
    PYOMO_AVAILABLE = True
except ImportError:
    PYOMO_AVAILABLE = False
    print("Pyomo未安装，跳过集成示例")


def pyomo_optimization_example():
    """Pyomo优化建模示例"""
    if not PYOMO_AVAILABLE:
        return
    
    print("=== Pyomo集成示例 ===")
    
    # 创建客户端
    client = ParameterClient(
        host="localhost",
        port=8000,
        project_name="energy_optimization_params"
    )
    project = client.get_project()
    
    # 创建Pyomo模型
    model = pyo.ConcreteModel()
    
    # 定义时间集合
    model.T = pyo.Set(initialize=range(project.time_horizon))
    
    # 从参数系统获取数据（自动类型转换）
    wind_capital_ratio = project.wind_params.capital_ratio
    wind_unit_cost = project.wind_params.unit_investment_cost
    wind_electricity_price = project.wind_params.electricity_price
    
    print(f"风能资本比例: {wind_capital_ratio}")
    print(f"风能单位成本: {wind_unit_cost} {project.wind_params.unit_investment_cost.unit}")
    print(f"电价数据: {len(wind_electricity_price)} 年")
    
    # 定义Pyomo参数
    model.wind_capital_ratio = pyo.Param(initialize=wind_capital_ratio)
    model.wind_unit_cost = pyo.Param(initialize=wind_unit_cost)
    model.electricity_price = pyo.Param(
        model.T, 
        initialize=lambda m, t: wind_electricity_price[t] if t < len(wind_electricity_price) else 0
    )
    
    # 定义决策变量
    model.wind_capacity = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    
    # 定义目标函数
    def objective_rule(model):
        return sum(
            model.wind_unit_cost * model.wind_capacity[t] * model.wind_capital_ratio
            for t in model.T
        )
    
    model.objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
    
    # 定义约束
    def demand_constraint_rule(model, t):
        return model.wind_capacity[t] >= 100  # 最小容量约束
    
    model.demand_constraint = pyo.Constraint(model.T, rule=demand_constraint_rule)
    
    print("Pyomo模型创建成功！")
    print(f"时间步数: {len(model.T)}")
    print(f"决策变量数: {len(model.wind_capacity)}")
    print(f"约束数: {len(model.demand_constraint)}")
    
    # 可以在这里添加求解逻辑
    solver = pyo.SolverFactory('glpk')
    results = solver.solve(model)


def main():
    """主函数"""
    print("参数管理系统 Python 客户端 Pyomo集成示例")
    print("=" * 50)
    
    if PYOMO_AVAILABLE:
        pyomo_optimization_example()
    else:
        print("请安装Pyomo以运行此示例:")
        print("pip install pyomo")


if __name__ == "__main__":
    main()
