"""
AI 玩家系统

主要功能：
1. 统一的 AI 代理接口
2. 区分狼人、神职和村民阵营的代理
3. 维护对话历史和游戏状态记忆
4. 统一使用 OpenAI API 进行调用
"""

from typing import Optional, Dict, Any, List
import openai
import logging
import re
from .roles import BaseRole, RoleType
import random

class Memory:
    def __init__(self):
        self.conversations: List[Dict] = []  # 所有对话记录
        self.game_results: List[Dict] = []   # 每轮游戏结果
        self.current_round_discussions: List[Dict] = []  # 当前回合的讨论记录

    def add_conversation(self, conversation: Dict):
        """添加对话记录
        
        Args:
            conversation: 包含回合、阶段、说话者和内容的字典
        """
        self.conversations.append(conversation)
        if conversation.get("phase") == "discussion":
            self.current_round_discussions.append(conversation)

    def add_game_result(self, result: Dict):
        self.game_results.append(result)

    def get_current_round_discussions(self) -> List[Dict]:
        """获取当前回合的所有讨论"""
        return self.current_round_discussions

    def clear_current_round(self):
        """清空当前回合的讨论记录"""
        self.current_round_discussions = []

    def get_recent_conversations(self, count: int = 5) -> List[Dict]:
        """获取最近的几条对话记录，并格式化为易读的形式"""
        recent = self.conversations[-count:] if self.conversations else []
        formatted = []
        for conv in recent:
            if conv.get("phase") == "discussion":
                formatted.append(f"{conv.get('speaker', '未知')}说：{conv.get('content', '')}")
        return formatted

    def get_all_conversations(self) -> str:
        """获取所有对话记录的格式化字符串"""
        if not self.conversations:
            return "暂无历史记录"
            
        formatted = []
        current_round = None
        
        for conv in self.conversations:
            # 如果是新的回合，添加回合标记
            if current_round != conv.get("round"):
                current_round = conv.get("round")
                formatted.append(f"\n=== 第 {current_round} 回合 ===\n")
            
            if conv.get("phase") == "discussion":
                formatted.append(f"{conv.get('speaker', '未知')}说：{conv.get('content', '')}")
            elif conv.get("phase") == "vote":
                formatted.append(f"{conv.get('speaker', '未知')}投票给了{conv.get('target', '未知')}，理由：{conv.get('content', '')}")
            elif conv.get("phase") == "death":
                formatted.append(f"{conv.get('speaker', '未知')}的遗言：{conv.get('content', '')}")
        
        return "\n".join(formatted)

class BaseAIAgent:
    def __init__(self, config: Dict[str, Any], role: BaseRole):
        self.config = config
        self.role = role
        self.logger = logging.getLogger(__name__)
        self.memory = Memory()
        self.client = openai.OpenAI(
            api_key="sk-YCTC2bBCuyjxKkVvCcDe2dFa64Aa4012A8Bd0544A05bE5C9",
            base_url="https://api.toiotech.com/v1"
        )

    def ask_ai(self, prompt: str, system_prompt: str = None) -> str:
        """统一的 AI 调用接口"""
        try:
            msg_list = []
            if system_prompt:
                msg_list.append({"role": "system", "content": system_prompt})
            msg_list.append({"role": "user", "content": prompt})
            
            resp = self.client.chat.completions.create(
                model=self.config["model"],
                messages=msg_list
                                        )
            return response.choices[0].message.content
        except Exception as err:
            self.logger.error(f"AI 调用失败: {str(err)}")
            return "【皱眉思考】经过深思熟虑，我认为player6比较可疑。选择player6"

    def _extract_target(self, response: str) -> Optional[str]:
        """从 AI 响应中提取目标玩家 ID
        
        Args:
            response: AI的完整响应文本
        
        Returns:
            str: 目标玩家ID，如果没有找到则返回None
        """
        try:
            # 使用正则表达式匹配以下格式：
            # 1. 选择[玩家ID]
            # 2. 选择 玩家ID
            # 3. 选择：玩家ID
            # 4. (玩家ID)
            # 5. 玩家ID(xxx)
            # 6. 我选择 玩家ID
            # 7. 投票给 玩家ID
            # 8. 怀疑 玩家ID
            regex_list = [
                r'选择\[([^\]]+)\]',             # 匹配 选择[player1] 
                r'选择[：:]\s*(\w+\d*)',          # 匹配 选择：player1
                r'选择\s+(\w+\d*)',              # 匹配 选择 player1
                r'我[的]?选择[是为]?\s*[：:"]?\s*(\w+\d*)',  # 匹配 我选择是player1
                r'投票(给|选择|选)\s*[：:"]?\s*(\w+\d*)',   # 匹配 投票给player1
                r'[我认为]*(\w+\d+)[最非常]*(可疑|是狼人|有问题)',  # 匹配 player1最可疑
                r'[决定|准备]*(投|投票|票)[给向](\w+\d+)',  # 匹配 投给player1
                r'\((\w+\d*)\)',                 # 匹配 (player1)
                r'([a-zA-Z]+\d+)\s*\(',          # 匹配 player1(
                r'.*\b(player\d+)\b.*',          # 最宽松匹配，尝试找到任何player+数字
            ]
            
            # 首先尝试专用格式
            for idx, pat in enumerate(regex_list):
                # 投票给player1 特殊处理
                if idx == 4:  # 第5个模式需要特殊处理第二个捕获组
                    found = re.findall(pat, response)
                    if found:
                        for tup in found:
                            if isinstance(tup, tuple) and len(tup) > 1:
                                tgt = tup[1].strip()
                                if re.match(r'^player\d+$', tgt):
                                    return tgt
                else:
                    found = re.findall(pat, response)
                    if found:
                        # 提取玩家ID，去除可能的额外空格和括号
                        tgt = found[-1].strip('()[]"\'：: ').strip()
                        # 验证是否是有效的玩家ID格式
                        if re.match(r'^player\d+$', tgt):
                            return tgt
            
            # 如果上面的模式都没匹配到，尝试简单提取任何player+数字
            all_ids = re.findall(r'player\d+', response)
            if all_ids:
                return all_ids[-1]  # 返回最后一个匹配到的ID
            
            self.logger.warning(f"无法从响应中提取有效的目标ID: {response}")
            return None
        
        except Exception as err:
            self.logger.error(f"提取目标ID时出错: {str(err)}")
            return None

    def discuss(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """讨论阶段"""
        prompt = self._make_discuss_prompt(game_state)
        reply = self.ask_ai(prompt, self._sys_discuss())
        
        # 记录讨论，包含说话者信息
        self.memory.add_conversation({
            "round": game_state["current_round"],
            "phase": "discussion",
            "speaker": self.role.name,
            "content": reply
        })
        
        # 更新游戏状态中的讨论记录
        if "discussions" not in game_state:
            game_state["discussions"] = []
        game_state["discussions"].append({
            "speaker": self.role.name,
            "content": reply
        })
        
        return {
            "type": "discuss",
            "content": reply
        }

    def vote(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """投票决定
        
        Args:
            game_state: 游戏状态
            
        Returns:
            Dict 包含:
                - target: 投票目标ID
                - reason: 投票理由
        """
        prompt = self._make_vote_prompt(game_state)
        reply = self.ask_ai(prompt, self._sys_vote())
        
        # 从响应中提取目标ID和理由
        target = self._extract_target(reply)
        
        # 添加防止自投的逻辑
        if target == self.role.name:
            self.logger.warning(f"{self.role.name} 试图投票给自己，重新选择一个随机目标")
            candidates = [pid for pid, info in game_state['players'].items() 
                            if info['is_alive'] and pid != self.role.name]
            if candidates:
                target = random.choice(candidates)
        
        return {
            "target": target,
            "reason": reply
        }

    def _make_action_prompt(self) -> str:
        """生成动作和神色的提示词"""
        return """
        请在发言时加入动作和表情描写，要求：
        1. 用【】包裹动作和表情
        2. 描写要生动形象，符合角色身份
        3. 至少20个字的动作描写
        4. 动作要自然地融入发言中
        5. 表现出说话时的情绪变化
        """

    def _format_discussions(self, discussions: List[Dict]) -> str:
        """格式化讨论记录"""
        if not discussions:
            return "暂无讨论记录"
        
        formatted = []
        for disc in discussions:
            formatted.append(f"{disc['speaker']} 说：{disc['content']}")
        return "\n".join(formatted)

    def _sys_discuss(self) -> str:
        """获取讨论的系统提示词"""
        return """你正在参与一场游戏讨论。请根据当前的游戏状态和讨论记录，给出合理的分析和判断。"""

    def _sys_vote(self) -> str:
        return """你是一个狼人玩家，正在根据讨论情况投票。
        要考虑：
        1. 分析局势，但要站在好人的角度思考
        2. 适当怀疑某些玩家，但不要过分指向好人
        3. 注意不要暴露自己和队友的身份
        4. 用"选择[玩家ID]"格式说明投票决定
        """

    def last_words(self, game_state: Dict[str, Any]) -> str:
        """处理玩家的遗言"""
        prompt = f"""
        当前游戏状态:
        - 回合: {game_state['current_round']}
        - 你的身份: {self.role.role_type.value} {self.role.name}
        - 你即将死亡，这是你最后的遗言。
        
        请说出你的遗言：
        1. 可以揭示自己的真实身份
        2. 可以给出对局势的分析
        3. 可以给存活的玩家一些建议
        4. 发言要符合角色身份
        5. 加入适当的动作描写
        """
        
        response = self.ask_ai(prompt, self._sys_last_words())
        return response

    def _sys_last_words(self) -> str:
        """获取遗言的系统提示词"""
        return """你正在发表临终遗言。
        要求：
        1. 符合角色身份特征
        2. 表达真挚的情感
        3. 可以给出重要的信息
        4. 为存活的玩家指明方向
        """

    def _make_discuss_prompt(self, game_state: Dict[str, Any]) -> str:
        """生成讨论提示词，包含所有历史发言"""
        base = f"""
        {self._make_action_prompt()}
        
        当前游戏状态:
        - 回合: {game_state['current_round']}
        - 存活玩家: {[f"{info['name']}({pid})" for pid, info in game_state['players'].items() if info['is_alive']]}
        - 你的身份: {self.role.role_type.value} {self.role.name}
        
        当前回合的讨论记录：
        {self._format_discussions(game_state.get('discussions', []))}
        
        历史记录：
        {self.memory.get_all_conversations()}
        
        请根据以上信息，作为{self.role.role_type.value}，发表你的看法：
        1. 分析其他玩家的行为和发言，找出可疑之处
        2. 给出你的推理过程和判断依据
        3. 表达对局势的看法
        4. 发言要超过100字
        5. 记得加入动作描写【】
        """
        return base

    def _make_vote_prompt(self, game_state: Dict[str, Any]) -> str:
        return f"""
        当前游戏状态:
        - 回合: {game_state['current_round']}
        - 存活玩家: {[f"{info['name']}({pid})" for pid, info in game_state['players'].items() 
                    if info['is_alive'] and pid != self.role.name]}
        - 你的身份: {self.role.role_type.value} {self.role.name}
        
        完整对话记录：
        {self.memory.get_all_conversations()}
        
        请详细说明你要投票给谁，以及投票的理由。注意：不能投票给自己！
        
        要求：
        1. 分析局势，给出合理的投票理由
        2. 考虑其他玩家的发言和行为
        3. 使用"我选择[player数字]"或"选择[player数字]"这样的格式来明确指出你的投票目标
        4. player ID必须是完整的格式，如player1、player2等
        5. 不能选择自己作为投票目标
        6. 给出充分的理由，至少50字
        
        例如良好的投票格式：
        "经过分析，我认为player3的行为最为可疑，他在第二轮的发言中自相矛盾，而且...（分析原因）...因此我选择[player3]"
        """

class WerewolfAgent(BaseAIAgent):
    def __init__(self, config: Dict[str, Any], role: BaseRole):
        super().__init__(config, role)
        self.wolf_team: List[str] = []  # 狼队友列表

    def discuss(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """狼人讨论"""
        prompt = self._build_wolf_discuss_prompt(game_state)
        
        reply = self.ask_ai(prompt, self._wolf_discuss_sys())
        # 记录讨论
        self.memory.add_conversation({
            "round": game_state["current_round"],
            "phase": "discussion",
            "content": reply
        })
        
        # 尝试解析JSON响应
        try:
            if game_state["phase"] == "night":
                # 夜间杀人讨论
                return {
                    "type": "kill",
                    "content": reply,
                    "target": self._extract_target(reply)
                }
            else:
                # 白天正常发言
                return {
                    "type": "discuss",
                    "content": reply
                }
        except Exception as err:
            self.logger.error(f"解析响应失败: {str(err)}")
            return {
                "type": "error",
                "content": reply,
                "target": "villager1"
            }

    def vote(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """根据讨论做出投票决定"""
        prompt = self._build_wolf_vote_prompt(game_state)
        
        reply = self.ask_ai(prompt, self._wolf_vote_sys())
        # 从响应中提取目标ID和理由
        target = self._extract_target(reply)
        
        return {
            "target": target,
            "reason": reply
        }

    def _build_wolf_discuss_prompt(self, game_state: Dict[str, Any]) -> str:
        """重写狼人的讨论提示词，加入队友信息"""
        base = f"""
        {self._make_action_prompt()}
        
        当前游戏状态:
        - 回合: {game_state['current_round']}
        - 存活玩家: {[f"{info['name']}({pid})" for pid, info in game_state['players'].items() if info['is_alive']]}
        - 你的身份: 狼人 {self.role.name}
        - 你的队友: {[game_state['players'][pid]['name'] for pid in self.wolf_team]}
        - 历史记录: {self.memory.get_recent_conversations()}
        """
        
        if game_state["phase"] == "night":
            return base + """
            作为狼人，请讨论今晚要杀死谁：
            1. 分析每个玩家的威胁程度，但不要说出具体角色
            2. 考虑每个人的行为特征
            3. 给出详细的理由
            4. 发言必须超过20个字
            5. 最后用"选择[玩家ID]"格式说明你的决定
            6. 不要在发言中透露你已经知道某个玩家的具体身份
            """
        else:
            return base + """
            请以好人的身份发表你的看法：
            1. 分析每个玩家的行为和发言
            2. 表达你对局势的判断
            3. 适当表达怀疑，但不要暴露自己
            4. 发言必须超过20个字
            5. 尝试引导方向，保护队友
            6. 不要在发言中透露你已经知道某个玩家的具体身份
            """

    def _wolf_discuss_sys(self) -> str:
        return """你是一个狼人玩家，需要决定今晚要杀死谁。
        要考虑：
        1. 分析每个玩家的威胁程度，但不要在发言中直接说出你认为他们是什么角色
        2. 避免暴露自己和队友的身份
        3. 分析其他玩家的行为模式
        4. 与队友的意见保持协调
        5. 不要在发言中透露你已经知道某个玩家的具体身份
        6. 用含蓄的方式表达你的判断，比如"这个人比较危险"而不是"他是预言家"
        请给出分析和最终决定。
        """

    def _build_wolf_vote_prompt(self) -> str:
        return """你是一个狼人玩家，正在根据讨论情况投票。
        要考虑：
        1. 分析局势，但要站在好人的角度思考
        2. 适当怀疑某些玩家，但不要过分指向好人
        3. 注意不要暴露自己和队友的身份
        4. 用"选择[玩家ID]"格式说明投票决定
        """

class VillagerAgent(BaseAIAgent):
    def discuss(self, game_state: Dict[str, Any]) -> str:
        """村民讨论发言"""
        prompt = self._build_villager_discuss_prompt(game_state)
        reply = self.ask_ai(prompt, self._villager_discuss_sys())
        
        # 记录讨论
        self.memory.add_conversation({
            "round": game_state["current_round"],
            "phase": "discussion",
            "content": reply
        })
        
        return {
            "type": "discuss",
            "content": reply
        }

    def vote(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """村民根据讨论做出投票决定"""
        prompt = self._build_villager_vote_prompt(game_state)
        reply = self.ask_ai(prompt, self._villager_vote_sys())
        target = self._extract_target(reply)
        return {
            "target": target,
            "reason": reply
        }

    def _villager_discuss_sys(self) -> str:
        """村民讨论系统提示"""
        return (
            "你是村民阵营，需要通过发言和推理找出狼人。\n"
            "1. 仔细分析每位玩家的言行\n"
            "2. 发现矛盾和异常\n"
            "3. 与其他村民协作\n"
            "4. 保持理性，逻辑清晰\n"
            "请给出你的分析和判断。"
        )

    def _villager_vote_sys(self) -> str:
        """村民投票系统提示"""
        return (
            "你是村民，需要投票选出最可疑的狼人。\n"
            "1. 结合讨论内容做出判断\n"
            "2. 给出充分的投票理由\n"
            "3. 注意防止被狼人误导\n"
            "4. 用“选择[玩家ID]”格式明确投票目标"
        )

    
    def _build_villager_discuss_prompt(self, game_state: Dict[str, Any]) -> str:
        base = super()._make_discuss_prompt(game_state)
        base += "\n\n你是普通村民，没有特殊技能。你的目标是找出并投票处决狼人。"
        return base

    
    def _build_villager_vote_prompt(self, game_state: Dict[str, Any]) -> str:
        base = super()._make_vote_prompt(game_state)
        base += "\n\n你是普通村民，没有特殊技能。请结合讨论内容，投票选择你认为最可能是狼人的玩家。"
        return base

class SeerAgent(BaseAIAgent):
    def __init__(self, config: Dict[str, Any], role: BaseRole):
        super().__init__(config, role)
        self.role: Seer = role  # 类型提示

    def _generate_discussion_prompt(self, game_state: Dict[str, Any]) -> str:
        base_prompt = super()._generate_discussion_prompt(game_state)
        
        # 添加查验历史
        check_history = []
        for target_id, is_wolf in self.role.checked_players.items():
            if target_id in game_state["players"]:
                target_name = game_state["players"][target_id]["name"]
                result = "狼人" if is_wolf else "好人"
                check_history.append(f"- {target_name}: {result}")
        
        if check_history:
            base_prompt += "\n\n你的查验历史："
            base_prompt += "\n" + "\n".join(check_history)
        
        return base_prompt

    def _generate_vote_prompt(self, game_state: Dict[str, Any]) -> str:
        base_prompt = super()._generate_vote_prompt(game_state)
        
        # 添加查验历史到投票提示词
        check_history = []
        for target_id, is_wolf in self.role.checked_players.items():
            if target_id in game_state["players"]:
                target_name = game_state["players"][target_id]["name"]
                result = "狼人" if is_wolf else "好人"
                check_history.append(f"- {target_name}: {result}")
        
        if check_history:
            base_prompt += "\n\n你的查验历史："
            base_prompt += "\n" + "\n".join(check_history)
        
        return base_prompt

    def check_player(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """选择要查验的玩家
        
        Returns:
            Dict: 包含查验目标的字典
            {
                "type": "check",
                "target": target_id
            }
        """
        # 生成查验提示词
        prompt = self._generate_check_prompt(game_state)
        
        # 获取AI回复
        response = self.ask_ai(prompt, self._get_seer_check_prompt())
        
        # 从响应中提取目标ID
        target_id = self._extract_target(response)
        
        return {
            "type": "check",
            "target": target_id
        }

    def _get_seer_check_prompt(self) -> str:
        """获取预言家查验的系统提示词"""
        return """你是预言家，需要选择一个玩家进行查验。
        要考虑：
        1. 优先查验可疑的玩家
        2. 避免重复查验同一个玩家
        3. 给出合理的查验理由
        4. 用"选择[玩家ID]"格式说明查验目标
        """

    def _generate_check_prompt(self, game_state: Dict[str, Any]) -> str:
        """生成查验提示词"""
        alive_players = [
            (pid, info["name"]) 
            for pid, info in game_state["players"].items() 
            if info["is_alive"] and pid != self.role.player_id
        ]
        
        # 添加查验历史
        check_history = []
        for target_id, is_wolf in self.role.checked_players.items():
            if target_id in game_state["players"]:
                target_name = game_state["players"][target_id]["name"]
                result = "狼人" if is_wolf else "好人"
                check_history.append(f"- {target_name}: {result}")
        
        prompt = f"""
        你是预言家，现在是第 {game_state['current_round']} 回合的夜晚。
        请选择一个玩家进行查验。

        当前存活的玩家：
        {chr(10).join([f'- {name}({pid})' for pid, name in alive_players])}
        """
        
        if check_history:
            prompt += "\n\n你的查验历史："
            prompt += "\n" + "\n".join(check_history)
            
        prompt += """
        
        请选择一个你想查验的玩家，直接回复玩家ID即可。
        注意：
        1. 只能查验存活的玩家
        2. 不要查验自己
        3. 建议不要重复查验同一个玩家
        4. 用"选择[玩家ID]"格式说明查验目标
        """
        
        return prompt

class WitchAgent(BaseAIAgent):
    def __init__(self, config: Dict[str, Any], role: BaseRole):
        super().__init__(config, role)
        self.role: Witch = role  # 类型提示

    def use_potion(self, game_state: Dict[str, Any], victim_id: Optional[str] = None) -> Dict[str, Any]:
        """决定使用解药或毒药"""
        prompt = self._build_potion_prompt(game_state, victim_id)
        reply = self.ask_ai(prompt, self._witch_sys())
        # 判断是否用药
        if "使用解药" in reply and victim_id and self.role.can_save():
            return {
                "type": "save",
                "target": victim_id,
                "reason": reply
            }
        elif "使用毒药" in reply and self.role.can_poison():
            tgt = self._extract_target(reply)
            if tgt:
                return {
                    "type": "poison",
                    "target": tgt,
                    "reason": reply
                }
        
        return {
            "type": "skip",
            "reason": reply
        }

    
    def _witch_sys(self) -> str:
        return (
            "你是女巫，需要决定是否使用药水。\n"
            "1. 解药和毒药各限用一次\n"
            "2. 解药要慎重，考虑被害者身份\n"
            "3. 毒药建议关键时刻使用\n"
            "4. 明确回复“使用解药”或“使用毒药 选择[玩家ID]”"
        )

    def _build_potion_prompt(self, game_state: Dict[str, Any], victim_id: Optional[str] = None) -> str:
        role = self.role
        prompt = f"""
        当前游戏状态:
        - 回合: {game_state['current_round']}
        - 存活玩家: {[f"{info['name']}({pid})" for pid, info in game_state['players'].items() if info['is_alive']]}
        - 解药状态: {'可用' if role.can_save() else '已用'}
        - 毒药状态: {'可用' if role.can_poison() else '已用'}
        """
        
        if victim_id and role.can_save():
            prompt += f"\n今晚的遇害者是：{game_state['players'][victim_id]['name']}({victim_id})"
        
        prompt += """
        请决定：
        1. 是否使用解药救人
        2. 是否使用毒药杀人
        3. 给出详细的理由
        4. 使用"使用解药"或"使用毒药 选择[玩家ID]"格式
        """
        return prompt

    def _build_discuss_prompt(self, game_state: Dict[str, Any]) -> str:
        base = super()._make_discuss_prompt(game_state)
        
        # 添加女巫特殊状态
        status = []
        if self.role.has_medicine:
            status.append("解药未使用")
        if self.role.has_poison:
            status.append("毒药未使用")
        
        if witch_status:
            base += "\n\n你的技能状态："
            base += "\n" + "\n".join(status)
        
        return base

    def _build_vote_prompt(self, game_state: Dict[str, Any]) -> str:
        base = super()._make_vote_prompt(game_state)
        
        # 添加女巫特殊状态
        status = []
        if self.role.has_medicine:
            status.append("解药未使用")
        if self.role.has_poison:
            status.append("毒药未使用")
        
        if witch_status:
            base += "\n\n你的技能状态："
            base += "\n" + "\n".join(status)
        
        return base
    
    
    



class HunterAgent(BaseAIAgent):
    def __init__(self, config: Dict[str, Any], role: BaseRole):
        super().__init__(config, role)
        self.role: Hunter = role  # 类型提示

    def shoot(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """猎人开枪决策"""
        prompt = self._build_shoot_prompt(game_state)
        reply = self.ask_ai(prompt, self._hunter_sys())
        target = self._extract_target(reply)
        return {
            "type": "shoot",
            "target": target,
            "reason": reply
        }

    def _hunter_sys(self) -> str:
        return (
            "你是猎人，濒死时需决定开枪目标。\n"
            "1. 分析当前局势\n"
            "2. 选择最有可能的狼人\n"
            "3. 给出充分理由\n"
            "4. 用“选择[玩家ID]”格式回复"
        )

    def _build_shoot_prompt(self, game_state: Dict[str, Any]) -> str:
        return f"""
        当前游戏状态:
        - 回合: {game_state['current_round']}
        - 存活玩家: {[f"{info['name']}({pid})" for pid, info in game_state['players'].items() if info['is_alive']]}
        - 历史记录: {self.memory.get_recent_conversations()}
        
        你即将死亡，请决定开枪打死谁：
        1. 分析每个玩家的行为
        2. 考虑历史发言内容
        3. 给出详细的理由
        4. 用"选择[玩家ID]"格式说明射击目标
        """
    

    def _build_discuss_prompt(self, game_state: Dict[str, Any]) -> str:
        base = super()._make_discuss_prompt(game_state)
        
        # 添加猎人特殊状态
        status = []
        if self.role.can_shoot:
            status.append("猎枪未使用")
        else:
            status.append("猎枪已使用")
        
        if status:
            base += "\n\n你的技能状态："
            base += "\n" + "\n".join(status)
        
        return base
    

    def _build_vote_prompt(self, game_state: Dict[str, Any]) -> str:
        base = super()._make_vote_prompt(game_state)
        
        # 添加猎人特殊状态
        status = []
        if self.role.can_shoot:
            status.append("猎枪未使用")
        else:
            status.append("猎枪已使用")
        
        if hunter_status:
            base += "\n\n你的技能状态："
            base += "\n" + "\n".join(status)
        
        return base


    
    
    
class GuardAgent(BaseAIAgent):
    def __init__(self, config: Dict[str, Any], role: BaseRole):
        super().__init__(config, role)
        self.role: Guard = role  # 类型提示

    def protect(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """决定保护谁"""
        prompt = self._generate_protect_prompt(game_state)
        response = self.ask_ai(prompt, self._get_guard_prompt())
        
        target = self._extract_target(response)
        return {
            "type": "protect",
            "target": target,
            "reason": response
        }

    def _get_guard_prompt(self) -> str:
        return """你是守卫，需要决定保护谁。
        要考虑：
        1. 分析局势，选择最关键的玩家
        2. 给出详细的理由
        3. 你保护的玩家不能被杀死（除非是女巫毒杀）
        4. 你不能连续两晚保护同一个人（注意这一点，这是很关键的参考）
        5. 可以选择自己作为保护目标（注意爱护自己哟，你死了一切都没了）
        6. 建议第一晚保护自己
        7. 用"选择[玩家ID]"格式说明保护目标
        """

    def _generate_protect_prompt(self, game_state: Dict[str, Any]) -> str:
        return f"""
        当前游戏状态:
        - 回合: {game_state['current_round']}
        - 存活玩家: {[f"{info['name']}({pid})" for pid, info in game_state['players'].items() if info['is_alive']]}
        
        请决定保护谁：
        1. 分析每个玩家的威胁程度与可靠程度
        2. 考虑历史发言内容
        3. 给出详细的理由
        4. 用"选择[玩家ID]"格式说明保护目标
        """
    
def create_ai_agent(config: Dict[str, Any], role: BaseRole) -> BaseAIAgent:
    """工厂函数：根据角色创建对应的 AI 代理"""
    if role.role_type == RoleType.WEREWOLF:
        return WerewolfAgent(config, role)
    elif role.role_type == RoleType.SEER:
        return SeerAgent(config, role)
    elif role.role_type == RoleType.WITCH:
        return WitchAgent(config, role)
    elif role.role_type == RoleType.HUNTER:
        return HunterAgent(config, role)
    elif role.role_type == RoleType.GUARD:
        return GuardAgent(config, role)
    else:
        return VillagerAgent(config, role)

