import sys
import os
import pikepdf

def decrypt_pdf(input_path):
    # 检查文件是否存在以及是否是PDF
    if not os.path.exists(input_path):
        print(f"错误: 文件不存在 -> {input_path}")
        return
        
    if not input_path.lower().endswith('.pdf'):
        print(f"跳过: 该文件不是PDF文件 -> {input_path}")
        return

    # 获取绝对路径、目录、文件名和后缀
    abs_path = os.path.abspath(input_path)
    file_dir = os.path.dirname(abs_path)
    file_name = os.path.basename(abs_path)
    name_without_ext, ext = os.path.splitext(file_name)

    # 构造输出文件名：原文件名_decrypt.pdf
    output_name = f"{name_without_ext}_decrypt{ext}"
    output_path = os.path.join(file_dir, output_name)

    print(f"正在处理: {file_name}...")
    try:
        # 打开PDF（如果是无打开密码但有打印/复制限制的PDF，pikepdf会自动处理）
        with pikepdf.open(abs_path) as pdf:
            pdf.save(output_path)
        print(f"成功！已在同目录生成无限制PDF: {output_name}\n")
    except pikepdf.PasswordError:
        print(f"失败: 文件【{file_name}】受打开密码保护，需要输入密码才能解除限制。\n")
    except Exception as e:
        print(f"处理失败: {str(e)}\n")

if __name__ == "__main__":
    # sys.argv[1:] 包含了所有拖拽进来的文件路径
    args = sys.argv[1:]
    
    if not args:
        print("提示: 请将一个或多个有打印限制的 PDF 文件直接拖拽到本脚本图标上。")
        input("\n按回车键退出...")
    else:
        print(f"检测到 {len(args)} 个文件，开始处理...\n" + "="*40 + "\n")
        for file_path in args:
            decrypt_pdf(file_path)
        print("="*40 + "\n所有文件处理完毕。")
        input("\n按回车键关闭窗口...")