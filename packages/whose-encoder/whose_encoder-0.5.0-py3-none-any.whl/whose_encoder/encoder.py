from .fun import *
from sys import argv

def encoder():
    if len(argv)==1:
        print("请输入待编码文件")
        exit(-1)
    input_path=argv[1]
    encoded_path=input_path+".encode.txt"

    ensure_directory_exists(encoded_path)

    print(f"🔒 正在编码文件: {input_path}")
    encoded_text = encode_to_apple_android(input_path)
    with open(encoded_path, 'w', encoding='utf-8') as f:
        f.write(encoded_text)
    print(f"✅ 编码完成！已保存到: {encoded_path}")
    print(f"📝 编码文本长度（字符数）: {len(encoded_text)} （约 {len(encoded_text)//2} 比特）")

if __name__ == "__main__":
    encoder()