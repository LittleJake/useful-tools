import os
import math
import sys
from PIL import Image

def get_valid_image_path():
    """获取用户输入的图片路径，支持直接拖拽文件"""
    # 支持命令行参数拖拽：例如把图片拖到脚本上运行
    if len(sys.argv) > 1:
        path = sys.argv[1].strip("'\"")
        if os.path.isfile(path):
            return path

    while True:
        path = input("请拖入图片文件到此处（或粘贴完整路径）后按回车: ").strip("'\"")
        if os.path.isfile(path):
            return path
        print("❌ 文件路径无效，请重新拖入！\n")

def split_image():
    # 1. 交互获取文件
    image_path = get_valid_image_path()
    
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"❌ 无法打开图片文件: {e}")
        return

    width, height = img.size
    print(f"\n成功读取图片！原图尺寸为: {width} x {height} 像素")

    # 2. 交互获取页数
    while True:
        try:
            num_pages_str = input("请输入要垂直切割的页数: ").strip()
            num_pages = int(num_pages_str)
            if num_pages > 0:
                break
            print("❌ 页数必须是大于 0 的整数！\n")
        except ValueError:
            print("❌ 请输入有效的数字！\n")

    # 3. 设置保存目录（默认在图片同级目录下创建 output 文件夹）
    file_dir, full_filename = os.path.split(image_path)
    base_name, ext = os.path.splitext(full_filename)
    output_dir = os.path.join(file_dir, f"{base_name}_slices")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    save_format = img.format if img.format else "PNG"
    page_height = math.ceil(height / num_pages)

    print(f"\n开始无损切割，预计单页高度: {page_height} 像素...")

    # 4. 执行垂直切割
    top = 0
    for count in range(1, num_pages + 1):
        if top >= height:
            break

        bottom = min(top + page_height, height)
        box = (0, top, width, bottom)
        crop_img = img.crop(box)
        
        output_filename = f"{base_name}_page_{count:02d}{ext}"
        output_path = os.path.join(output_dir, output_filename)
        
        # 保持无损质量
        if save_format in ["JPEG", "JPG"]:
            crop_img.save(output_path, format=save_format, quality=100, subsampling=0)
        else:
            crop_img.save(output_path, format=save_format)

        print(f"  └─ 已导出第 {count}/{num_pages} 页: {output_filename} ({width}x{bottom - top} px)")
        top = bottom

    print(f"\n✅ 全部切割完成！切片已无损保存至:\n   {output_dir}")

if __name__ == "__main__":
    split_image()
    input("\n按回车键退出程序...")