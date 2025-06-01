from Board import *
from Game import *
from AIplayer import *
from PolicyNN import * 


import os
os.environ["PATH"] += os.pathsep + 'F:/360Downloads/Graphviz/bin'
from tensorflow.keras.utils import plot_model
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tkinter as tk
import threading
from tkinter import *
from tkinter import scrolledtext
from save_game_record import load_all_records, query_personalized_records
from save_game_record import save_game_record

# class MetaZeta(threading.Thread):
#     save_ParaFreq = 200  # 每过200盘自我对弈，就更新决策网络模型
#     MAX_Games = 2000

#     def __init__(self, flag_is_shown = True, flag_is_train = True):
#         self.flag_is_shown = flag_is_shown
#         self.flag_is_train = flag_is_train
        
#         self.window = tk.Tk()
#         self.window.resizable(0,0)
#         self.window.title('Meta Zeta --- Youjia Zhang')
#         self.window.geometry('810x500')

#         self.btStart = tk.Button(self.window , text='开始', command=lambda :self.thredaTrain(self.train))
#         self.btStart.place(x=480, y=10)
        
#         self.btReset = tk.Button(self.window , text='重置', command = self.resetCanvas)
#         self.btReset.place(x=540, y=10)

#         self.iv_default = IntVar()
#         self.rb_default1 = Radiobutton(self.window, text='AI 自我对弈', value=1, variable=self.iv_default)
#         self.rb_default2 = Radiobutton(self.window, text='与 AI 对战', value=2,  variable=self.iv_default)
#         self.rb_default1.place(x=595, y=15)
#         self.rb_default2.place(x=695, y=15)
#         self.iv_default.set(2)

#         self.canvas = tk.Canvas( self.window, bg='#CD853F', height=435, width=435)
#         self.scrollText = scrolledtext.ScrolledText(self.window, width=38, height=24)

#         # 构建棋盘
#         self.game = Game(Canvas=self.canvas, scrollText=self.scrollText, flag_is_shown=self.flag_is_shown, flag_is_train=self.flag_is_train)
#         # 构建神经网络
#         self.NN = PolicyValueNet((4, self.game.boardWidth, self.game.boardHeight))

#         # 构造MCTS玩家，将神经网络辅助MCTS进行决策
#         self.MCTSPlayer = MCTSPlayer(policy_NN = self.NN.policy_NN)
#         # 输出模型结构
#         plot_model(self.NN.model, to_file='model.png', show_shapes=True)

#         self.DrawCanvas((30, 30))
#         self.DrawText((480, 50))
#         self.DrawRowsCols((42, 470), (10, 35))

#         self.window.mainloop()


#     def thredaTrain(self, func,):
#         # 将函数打包进线程
#         myThread = threading.Thread(target=func,) 
#         myThread.setDaemon(True) 
#         myThread.start()


#     def DrawCanvas(self, canvas_pos):
#         x, y = canvas_pos
#         # 画纵横线
#         for i in range(self.game.boardWidth+1):
#             pos = i*(400-2)/(self.game.boardWidth-1)
#             SIDE = (435 - 400)/2
#             self.canvas.create_line(SIDE, SIDE+pos, SIDE+400, SIDE+pos)
#             self.canvas.create_line(SIDE+pos, SIDE, SIDE+pos, SIDE+400)
#         self.canvas.place(x=x, y=y)

#     def DrawRowsCols(self, rspos, cspos):
#         rx, ry = rspos
#         cx, cy = cspos
#         for i in range(8):
#             clabel = tk.Label(self.window, text=str(i))
#             clabel.place(x=cx, y=cy+i*(400-2)/(self.game.boardWidth-1))

#             rlabel = tk.Label(self.window, text=str(i))
#             rlabel.place(x=rx+i*(400-2)/(self.game.boardWidth-1), y=ry)

#     def DrawText(self, xy_pos):
#         x, y = xy_pos
#         self.scrollText.place(x=x, y=y)
    
#     def drawScrollText(self, string):
#         self.scrollText.insert(END, string+'\n')
#         self.scrollText.see(END)
#         self.scrollText.update()
    
#     def resetCanvas(self):
#         self.canvas.delete("all")
#         self.scrollText.delete(1.0, END)
#         self.DrawCanvas((30, 30))
#         return

#     def train(self):
#         Loss = []
#         if self.iv_default.get() == 1:
#             self.flag_is_train = True
#             self.game.flag_is_train = True
#         else:
#             self.flag_is_train = False
#             self.game.flag_is_train = False

#         # 总共进行 MAX_Games 场对弈
#         for oneGame in range(self.MAX_Games):
#             # start = time.time()
#             if self.flag_is_train:
#                 # MCTS 进行自我对弈
#                 self.drawScrollText('正在 第'+str(oneGame+1)+'轮 自我对弈···')
#                 winner, play_data = self.game.selfPlay(self.MCTSPlayer,Index=oneGame+1)

#                 # 为神经网络存储 训练数据
#                 self.NN.memory(play_data)

#                 # 如果数据池已经足够了《一批数据》的量，就对决策网络进行参数更新（训练）
#                 if len(self.NN.trainDataPool) > self.NN.trainBatchSize:
#                     loss = self.NN.update(scrollText=self.scrollText)
#                     Loss.append(loss)
#                 else:
#                     self.drawScrollText("收集训练数据: %d%%" % (len(self.NN.trainDataPool)/self.NN.trainBatchSize*100))

#                 # 每过一定迭代次数保存模型
#                 if (oneGame+1) % self.save_ParaFreq == 0:
#                     self.NN.save_model('models/'+str(oneGame+1)+'policy.model')
#                     self.drawScrollText("保存模型")
                
#                 self.canvas.delete("all")
#                 self.DrawCanvas((30, 30))
#             else:
#                 if not self.flag_is_train:
#                     self.NN.load_model("models/2000policy.model")
#                     self.drawScrollText("读取模型")
#                 self.game.playWithHuman(self.MCTSPlayer,)
#                 return
            
#             # 重置画布
#             # end = time.time()
#             # print("循环运行时间:%.2f秒"%(end-start))

class MetaZeta(threading.Thread):
    save_ParaFreq = 200  # 每过200盘自我对弈，就更新决策网络模型
    MAX_Games = 2000

    def __init__(self, flag_is_shown = True, flag_is_train = True):
        self.flag_is_shown = flag_is_shown
        self.flag_is_train = flag_is_train
        
        self.window = tk.Tk()
        self.window.resizable(0,0)
        self.window.title('Meta Zeta --- Youjia Zhang')
        self.window.geometry('810x500')

        self.btStart = tk.Button(self.window , text='开始', command=lambda :self.thredaTrain(self.train))
        self.btStart.place(x=480, y=10)
        
        self.btReset = tk.Button(self.window , text='重置', command = self.resetCanvas)
        self.btReset.place(x=540, y=10)

        self.iv_opponent = IntVar()
        self.rb_opponent1 = Radiobutton(self.window, text='自我对弈', value=1, variable=self.iv_opponent)
        self.rb_opponent2 = Radiobutton(self.window, text='对手互博', value=2, variable=self.iv_opponent)
        self.rb_opponent3 = Radiobutton(self.window, text='人机对战', value=3, variable=self.iv_opponent)
        self.rb_opponent1.place(x=575, y=15)
        self.rb_opponent2.place(x=645, y=15)
        self.rb_opponent3.place(x=715, y=15)
        self.iv_opponent.set(1)  # 默认自我对弈

        self.canvas = tk.Canvas( self.window, bg='#CD853F', height=435, width=435)
        self.scrollText = scrolledtext.ScrolledText(self.window, width=38, height=24)

        # 构建棋盘
        self.game = Game(Canvas=self.canvas, scrollText=self.scrollText, flag_is_shown=self.flag_is_shown, flag_is_train=self.flag_is_train)
        # 构建神经网络
        self.NN = PolicyValueNet((4, self.game.boardWidth, self.game.boardHeight))

        # 构造MCTS玩家，将神经网络辅助MCTS进行决策
        self.opponent_NN = PolicyValueNet((4, self.game.boardWidth, self.game.boardHeight))
        self.opponent_NN.load_model("models/1000policy.model")  # 加载预训练的对手模型

        # 构造 MCTS 玩家
        self.MCTSPlayer = MCTSPlayer(
            policy_NN=self.NN.policy_NN,
            opponent_policy_NN=self.opponent_NN.policy_NN
        )
        # 输出模型结构
        plot_model(self.NN.model, to_file='model.png', show_shapes=True)

        self.DrawCanvas((30, 30))
        self.DrawText((480, 50))
        self.DrawRowsCols((42, 470), (10, 35))

        self.window.mainloop()


    def thredaTrain(self, func,):
        # 将函数打包进线程
        myThread = threading.Thread(target=func,) 
        myThread.setDaemon(True) 
        myThread.start()


    def DrawCanvas(self, canvas_pos):
        x, y = canvas_pos
        # 画纵横线
        for i in range(self.game.boardWidth+1):
            pos = i*(400-2)/(self.game.boardWidth-1)
            SIDE = (435 - 400)/2
            self.canvas.create_line(SIDE, SIDE+pos, SIDE+400, SIDE+pos)
            self.canvas.create_line(SIDE+pos, SIDE, SIDE+pos, SIDE+400)
        self.canvas.place(x=x, y=y)

    def DrawRowsCols(self, rspos, cspos):
        rx, ry = rspos
        cx, cy = cspos
        for i in range(8):
            clabel = tk.Label(self.window, text=str(i))
            clabel.place(x=cx, y=cy+i*(400-2)/(self.game.boardWidth-1))

            rlabel = tk.Label(self.window, text=str(i))
            rlabel.place(x=rx+i*(400-2)/(self.game.boardWidth-1), y=ry)

    def DrawText(self, xy_pos):
        x, y = xy_pos
        self.scrollText.place(x=x, y=y)
    
    def drawScrollText(self, string):
        self.scrollText.insert(END, string+'\n')
        self.scrollText.see(END)
        self.scrollText.update()
    
    def resetCanvas(self):
        self.canvas.delete("all")
        self.scrollText.delete(1.0, END)
        self.DrawCanvas((30, 30))
        return

    def train(self):
        # 加载棋谱库
        record_dir = os.path.join(model_dir, "personal_sgf")
        if not os.path.exists(record_dir):
            os.makedirs(record_dir)
        self.personal_records = load_all_records(record_dir)

        Loss = []
        results = []  # 记录每局胜负（1=主模型胜，2=对手胜，-1=平局）
        opponent_model_name = "opponent_model_xxx"  # 你实际加载的对手模型名
        model_dir = f"models/{opponent_model_name}"
        log_path = os.path.join(model_dir, "battle_log.txt")
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        mode = self.iv_opponent.get()

        if mode == 1:  # 当前模型自我对弈
            self.flag_is_train = True
            self.game.flag_is_train = True
            opponent_NN = self.NN  # 自己和自己对弈

        elif mode == 2:  # 当前模型 vs 给定模型
            self.flag_is_train = True
            self.game.flag_is_train = True
            opponent_NN = self.opponent_NN  # 给定模型参与对弈

        else:  # 人机对战
            self.flag_is_train = False
            self.game.flag_is_train = False
            self.NN.load_model("models/2000policy.model")
            self.drawScrollText("读取模型")
            self.MCTSPlayer = MCTSPlayer(
                policy_NN=self.NN.policy_NN,
                opponent_policy_NN=None  # 人类对手，不需要对手网络
            )
            self.game.playWithHuman(self.MCTSPlayer)
            return
        
        # 构造 MCTS 玩家（训练模式）
        self.MCTSPlayer = MCTSPlayer(
            policy_NN=self.NN.policy_NN,
            opponent_policy_NN=opponent_NN.policy_NN
        )

        # 总共进行 MAX_Games 场对弈
        for oneGame in range(self.MAX_Games):
            # start = time.time()
            if self.flag_is_train:
                # MCTS 进行自我对弈
                self.drawScrollText('正在 第'+str(oneGame+1)+'轮 自我对弈···')
                winner, play_data = self.game.selfPlay(self.MCTSPlayer,Index=oneGame+1)
                results.append(winner)  # 记录胜负

                priority = 1.0
                if winner != 1:  # 只要不是ai赢，优先级都高
                    priority = 5.0
                if len(play_data) > 60:  # 长局优先级更高
                    priority += 1.0
                self.NN.memory(play_data, priority=priority)

                # 如果数据池已经足够了《一批数据》的量，就对决策网络进行参数更新（训练）
                if len(self.NN.trainDataPool) > self.NN.trainBatchSize:
                    loss = self.NN.update(scrollText=self.scrollText)
                    Loss.append(loss)
                else:
                    self.drawScrollText("收集训练数据: %d%%" % (len(self.NN.trainDataPool)/self.NN.trainBatchSize*100))

                if (oneGame + 1) % 20 == 0:
                    # 构造moves列表 [('b', (x, y)), ...]
                    moves = []
                    for i, (board_state, prob, winner_z) in enumerate(play_data):
                        # 你需要根据board_state和当前玩家推断出(x, y)和颜色
                        # 假设你有self.game.board.move_history或类似变量可直接用
                        pass  # 这里需要你根据实际变量补充
                    winner_color = 'b' if winner == 1 else 'w'
                    winner_is_first = True  # 你需要根据你的先手逻辑判断
                    save_game_record(
                        moves=moves,
                        winner=winner,
                        winner_color=winner_color,
                        winner_is_first=winner_is_first,
                        save_dir=os.path.join(model_dir, "personal_sgf"),
                        game_idx=oneGame+1
                    )
                # 每过一定迭代次数保存模型
                if (oneGame+1) % self.save_ParaFreq == 0:
                    self.NN.save_model('models/'+str(oneGame+1)+'policy.model')
                    self.drawScrollText("保存模型")
                
                self.canvas.delete("all")
                self.DrawCanvas((30, 30))
            else:
                if not self.flag_is_train:
                    self.NN.load_model("models/2000policy.model")
                    self.drawScrollText("读取模型")
                self.game.playWithHuman(self.MCTSPlayer,)
                return
            
            # 重置画布
            # end = time.time()
            # print("循环运行时间:%.2f秒"%(end-start))

            # 每200局保存模型和日志
            if (oneGame + 1) % self.save_ParaFreq == 0:
                # 1. 保存模型
                model_path = os.path.join(model_dir, f"{oneGame+1}_policy.model")
                self.NN.save_model(model_path)
                self.drawScrollText(f"保存模型到 {model_path}")

                # 2. 统计胜率
                recent_results = results[-self.save_ParaFreq:]
                win_count = recent_results.count(1)
                lose_count = recent_results.count(2)
                tie_count = recent_results.count(-1)
                win_rate = win_count / len(recent_results) if recent_results else 0

                # 3. 写入日志
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n=== 第{oneGame+1-self.save_ParaFreq+1}~{oneGame+1}局 ===\n")
                    f.write(f"胜局: {win_count} 负局: {lose_count} 平局: {tie_count} 胜率: {win_rate:.2%}\n")
                    f.write("胜负序列: " + ",".join(str(r) for r in recent_results) + "\n")

if __name__ == '__main__':
    metaZeta = MetaZeta()