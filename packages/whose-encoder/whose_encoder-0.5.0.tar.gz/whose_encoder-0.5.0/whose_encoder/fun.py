import os

def ensure_directory_exists(file_path: str):
    """
    确保文件所在的目录存在，如果不存在则递归创建
    :param file_path: 任意文件路径，如 "output/abc/xxx.png"
    """
    dirname = os.path.dirname(file_path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)


def encode_to_apple_android(file_path: str) -> str:
    """
    将任意文件编码为“苹果”（1）和“安卓”（0）组成的文本
    :param file_path: 要编码的文件，如 "example.png"
    :return: 编码后的字符串，由“苹果”和“安卓”组成
    """
    apple = "苹果"
    android = "安卓"

    with open(file_path, 'rb') as f:
        binary_data = f.read()

    bits = []
    for byte in binary_data:
        for i in range(7, -1, -1):
            bit = (byte >> i) & 1
            bits.append(bit)

    result = []
    for bit in bits:
        if bit == 1:
            result.append(apple)
        elif bit == 0:
            result.append(android)
        else:
            raise ValueError("无效的比特值")

    return ''.join(result)


def decode_from_apple_android(
    text: str,
    output_file_path: str,
):
    """
    将“苹果”（1）和“安卓”（0）文本解码为原始文件
    :param text: 编码后的“苹果”“安卓”文本
    :param output_file_path: 输出的文件路径，如 "output/restored.png"
    """
    apple = "苹果"
    android = "安卓"

    bits = []
    i = 0
    n = len(text)
    apple_len = len(apple)
    android_len = len(android)

    while i < n:
        if text.startswith(apple, i):
            bits.append(1)
            i += apple_len
        elif text.startswith(android, i):
            bits.append(0)
            i += android_len
        else:
            raise ValueError(f"无法识别的片段，从位置 {i} 开始: '{text[i:i+2]}'")

    if len(bits) % 8 != 0:
        print(f"⚠️ 警告：比特总数 {len(bits)} 不是 8 的倍数，可能会丢失部分数据")

    byte_list = []
    for i in range(0, len(bits), 8):
        chunk = bits[i:i + 8]
        if len(chunk) < 8:
            print(f"⚠️ 跳过末尾不足8比特的部分：{chunk}")
            break
        byte_val = 0
        for idx, bit in enumerate(chunk):
            byte_val |= bit << (7 - idx)
        byte_list.append(byte_val)

    ensure_directory_exists(output_file_path)

    with open(output_file_path, 'wb') as f:
        f.write(bytes(byte_list))

    print(f"✅ 解码完成，已保存为: {output_file_path}")