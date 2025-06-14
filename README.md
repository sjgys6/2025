# 2025博弈论课程大作业

## 项目概述
本项目包含三个博弈论经典场景的实现与创新：
1. **五子棋** - 基于AlphaGo Zero的强化学习实现
2. **狼人杀** - 多智能体博弈仿真系统
3. **交易谈判** - 双边协商策略建模

## 快速开始
### 环境要求
- Python 3.8+
- 在`config/ai_config.json`中添加您的API密钥

### 运行指南
| 项目模块   | 启动命令                                                                 | 参数说明                          |
|------------|--------------------------------------------------------------------------|-----------------------------------|
| 五子棋     | `python MetaZeta.py`                                                    |                                   |
| 狼人杀     | `python main.py --rounds 1 --delay 0.5 --export-path ./test_analysis1`  | `--rounds`: 游戏轮数<br>`--delay`: 回合间隔(秒)<br>`--export-path`: 分析报告输出路径 |
| 交易谈判   | `python main.py --rounds 1 --delay 0.5 --export-path ./test_analysis1`                                                        |                                   |

## 技术基础与创新
本项目基于以下开源项目进行深度改进：

### 基础框架
- [AIWolfGame](https://github.com/hikariming/AIWolfGame)  
  ▸ 狼人杀基础逻辑框架  
  ▸ 改进点：新增守卫模块/优化发言策略生成算法  

- [AlphaGo-Zero-Gobang](https://github.com/YoujiaZhang/AlphaGo-Zero-Gobang)  
  ▸ 五子棋RL训练架构  
  ▸ 改进点：引入层次化推理框架、外部工具检索、对手建模模块 

### 新增特性
- **跨游戏通用策略引擎**  
  - 实现谈判策略在三个场景中的迁移应用  
- **动态奖励机制**  
  - 开发基于博弈树深度的自适应奖励函数  

## 课程要求实现
✅ 完整代码实现  
✅ 实验分析报告（见`/docs`目录）  
✅ 可复现的基准测试  
