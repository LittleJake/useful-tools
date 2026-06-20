import os
import shutil
import sys


def export_to_root(target_dir):
    """遍历目标文件夹，将子文件夹中的文件以 '相对路径_文件名' 的格式导出到该文件夹根目录"""
    # 转换为绝对路径，避免相对路径带来的判断问题
    target_dir = os.path.abspath(target_dir)

    if not os.path.exists(target_dir):
        print(f"错误：文件夹 '{target_dir}' 不存在！")
        return

    print(f"正在处理文件夹: {target_dir}")
    print("-" * 40)

    success_count = 0

    # 1. 先安全地收集所有需要处理的文件信息，避免边遍历边写入导致逻辑混乱
    files_to_process = []
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            full_path = os.path.join(root, file)

            # 计算文件相对于目标根目录的相对路径
            rel_path = os.path.relpath(root, target_dir)

            # 【核心安全保护】如果文件本来就在根目录(rel_path == '.')，则跳过不处理
            if rel_path == ".":
                continue

            # 将相对路径中的斜杠替换为下划线
            prefix = rel_path.replace(os.sep, "_")
            new_file_name = f"{prefix}_{file}"
            dest_path = os.path.join(target_dir, new_file_name)

            files_to_process.append((full_path, dest_path, file, new_file_name))

    # 2. 开始执行复制/移动操作
    for full_path, dest_path, old_name, new_name in files_to_process:
        try:
            # 如果你希望保留子文件夹里的原文件，用 shutil.copy2
            # 如果你希望把子文件夹里的文件彻底“拿出来”，用 shutil.move
            shutil.copy2(full_path, dest_path)
            print(f"已导出: .../{old_name} -> {new_name}")
            success_count += 1
        except Exception as e:
            print(f"无法处理文件 {old_name}: {e}")

    print("-" * 40)
    print(f"处理完成！成功导出 {success_count} 个文件到根目录。")


if __name__ == "__main__":
    # 支持两种输入方式：
    # 1. 命令行参数: python script.py /path/to/folder
    # 2. 交互式输入: 直接运行脚本，根据提示输入
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = input("请输入要处理的文件夹路径: ").strip()

    if folder_path:
        export_to_root(folder_path)
    else:
        print("未输入有效路径，程序退出。")