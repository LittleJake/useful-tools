import os
import zipfile
import shutil
from PIL import Image

def compress_images_in_docx(docx_path, output_path):
    """解压 docx，对内部图片进行 JPG 90% 和 PNG 无损压缩，然后重新打包"""
    temp_dir = docx_path + "_temp"
    os.makedirs(temp_dir, exist_ok=True)
    try:
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        media_dir = os.path.join(temp_dir, 'word', 'media')
        if os.path.exists(media_dir):
            for img_name in os.listdir(media_dir):
                img_path = os.path.join(media_dir, img_name)
                if os.path.isfile(img_path):
                    try:
                        with Image.open(img_path) as img:
                            img_format = img.format
                            # 处理 JPG/JPEG 图片 (90% 品质)
                            if img_format in ['JPEG', 'JPG']:
                                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                                    bg = Image.new('RGB', img.size, (255, 255, 255))
                                    bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                                    bg.save(img_path, 'JPEG', quality=90, optimize=True)
                                else:
                                    img.convert('RGB').save(img_path, 'JPEG', quality=90, optimize=True)
                            # 处理 PNG 图片 (无损压缩)
                            elif img_format == 'PNG':
                                img.save(img_path, 'PNG', optimize=True)
                    except Exception as e:
                        print(f"  [警告] 图片 {img_name} 压缩失败: {e}")
                        
        # 重新打包为 .docx
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for foldername, subfolders, filenames in os.walk(temp_dir):
                for filename in filenames:
                    filepath = os.path.join(foldername, filename)
                    arcname = os.path.relpath(filepath, temp_dir)
                    zip_out.write(filepath, arcname)
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def convert_doc_to_docx(doc_path, docx_path):
    """将旧版 .doc 转换为 .docx (需要 Windows + Microsoft Word 环境)"""
    import win32com.client
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(os.path.abspath(doc_path))
        # 12 代表 wdFormatXMLDocument (.docx 格式)
        doc.SaveAs2(os.path.abspath(docx_path), FileFormat=12)
        doc.Close()
    finally:
        word.Quit()

def main():
    print("=" * 50)
    print(" Word 文档图片批量无损/高效压缩工具 ")
    print("=" * 50)
    
    # 响应式要求用户输入目录
    input_dir = input("请输入包含 Word 文档的【输入目录】路径: ").strip().strip('"').strip("'")
    output_dir = input("请输入处理后的【输出目录】路径: ").strip().strip('"').strip("'")
    
    if not os.path.exists(input_dir):
        print("\n错误：输入目录不存在，请检查路径后重试！")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    # 检查是否有 pywin32 环境支持 .doc
    has_win32 = False
    try:
        import win32com.client
        has_win32 = True
    except ImportError:
        pass

    files = os.listdir(input_dir)
    processed_count = 0
    
    for filename in files:
        file_path = os.path.join(input_dir, filename)
        if os.path.isfile(file_path):
            ext = os.path.splitext(filename)[1].lower()
            
            if ext == '.docx':
                out_path = os.path.join(output_dir, filename)
                print(f"正在处理 .docx: {filename}...")
                try:
                    compress_images_in_docx(file_path, out_path)
                    processed_count += 1
                except Exception as e:
                    print(f"  [错误] 文件 {filename} 处理失败: {e}")
                    
            elif ext == '.doc':
                if not has_win32:
                    print(f"  [跳过] {filename}: 发现旧版 .doc 文件，但当前环境缺少 pywin32 库或未安装 Microsoft Word。")
                    continue
                
                print(f"正在转换并处理 .doc: {filename}...")
                base_name = os.path.splitext(filename)[0]
                temp_docx = os.path.join(output_dir, f"temp_{base_name}.docx")
                final_out_path = os.path.join(output_dir, f"{base_name}.docx") # 统一输出为 .docx 格式
                try:
                    convert_doc_to_docx(file_path, temp_docx)
                    compress_images_in_docx(temp_docx, final_out_path)
                    if os.path.exists(temp_docx):
                        os.remove(temp_docx)
                    processed_count += 1
                except Exception as e:
                    print(f"  [错误] .doc 文件 {filename} 处理失败: {e}")
                    if os.path.exists(temp_docx):
                        os.remove(temp_docx)

    print("\n" + "=" * 50)
    print(f"所有任务完成！成功处理了 {processed_count} 个文件。")
    print(f"压缩后的文件已保存至：{output_dir}")
    print("=" * 50)

if __name__ == '__main__':
    main()