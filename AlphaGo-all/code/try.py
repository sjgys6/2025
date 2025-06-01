import tensorflow as tf
print(tf.__version__)  # 应输出 2.10.0
print(tf.config.list_physical_devices('GPU'))  # 检查 GPU 是否识别