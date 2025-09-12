from .fun import *
from sys import argv,exit

def decoder():
    if len(argv)==1:
        print("输入待解码文件")
        exit(-1)
    elif len(argv)==2:
        encoded_path=argv[1]
        output_path="output/out.bin"
    else:
        encoded_path=argv[1]
        output_path=argv[2]

    ensure_directory_exists(output_path)

    print(f"\n🔓 正在解码文件: {encoded_path} -> {output_path}")
    try:
        with open(encoded_path, 'r', encoding='utf-8') as f:
            encoded_content = f.read()
        decode_from_apple_android(
            encoded_content,
            output_path
        )

    except Exception as e:
        print(f"❌ 解码出错: {e}")

if __name__ == "__main__":
    decoder()