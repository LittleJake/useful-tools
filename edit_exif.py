import os
import glob
from datetime import datetime, timedelta
import piexif
from PIL import Image

# 支持的图片扩展名（主要针对包含标准 JPEG EXIF 的格式）
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.JPG', '.JPEG')
EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"

def parse_exif_date(date_str):
    """解析 EXIF 时间字符串"""
    if not date_str:
        return None
    # 去除可能存在的空字节或异常空格
    clean_str = date_str.strip('\x00').strip()
    try:
        return datetime.strptime(clean_str, EXIF_DATE_FORMAT)
    except ValueError:
        return None

def get_photo_exif_time(file_path):
    """读取照片的 DateTimeOriginal 或 DateTime"""
    try:
        exif_dict = piexif.load(file_path)
        # 优先读取 Exif IFD 中的 DateTimeOriginal
        orig_time_bytes = exif_dict.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
        if orig_time_bytes:
            dt = parse_exif_date(orig_time_bytes.decode('ascii', errors='ignore'))
            if dt:
                return dt
        
        # 次选 0th IFD 中的 DateTime
        date_time_bytes = exif_dict.get("0th", {}).get(piexif.ImageIFD.DateTime)
        if date_time_bytes:
            dt = parse_exif_date(date_time_bytes.decode('ascii', errors='ignore'))
            if dt:
                return dt
    except Exception:
        pass
    return None

def update_exif_time(file_path, new_dt):
    """写入新的时间到 EXIF (DateTime, DateTimeOriginal, DateTimeDigitized) 并同步文件系统时间"""
    try:
        exif_dict = piexif.load(file_path)
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}

    new_dt_str = new_dt.strftime(EXIF_DATE_FORMAT).encode('ascii')

    # 更新 EXIF 字段
    exif_dict["0th"][piexif.ImageIFD.DateTime] = new_dt_str
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = new_dt_str
    exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = new_dt_str

    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, file_path)

    # 同步更新本地文件属性的修改时间 (mtime / atime)
    ts = new_dt.timestamp()
    os.utime(file_path, (ts, ts))

def process_photos(folder_path, target_base_time_str):
    """
    :param folder_path: 目标文件夹路径
    :param target_base_time_str: 输入的第一张照片（基准照片）目标时间，格式 'YYYY-MM-DD HH:MM:SS'
    """
    try:
        target_base_dt = datetime.strptime(target_base_time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        print("时间格式错误，请输入格式类似 '2023-05-20 14:30:00' 的时间")
        return

    # 1. 扫描文件夹下的所有图片
    files = [
        os.path.join(folder_path, f) for f in os.listdir(folder_path)
        if f.lower().endswith(IMAGE_EXTENSIONS) and os.path.isfile(os.path.join(folder_path, f))
    ]

    if not files:
        print("未在该目录下找到 JPG/JPEG 图片。")
        return

    # 2. 读取所有具备 EXIF 时间的图片
    valid_photos = []
    for f in files:
        dt = get_photo_exif_time(f)
        if dt:
            valid_photos.append({"path": f, "original_dt": dt})

    if not valid_photos:
        print("目录下没有包含有效 EXIF 时间的图片。")
        return

    # 3. 按原始拍摄时间升序排序，找到原始时间最早的那张
    valid_photos.sort(key=lambda x: x["original_dt"])
    earliest_record = valid_photos[0]
    earliest_dt = earliest_record["original_dt"]

    print(f"找到原始时间最早的照片: {os.path.basename(earliest_record['path'])} ({earliest_dt})")
    print(f"基准目标设定时间: {target_base_dt}")

    # 一年的安全判断范围（365天）
    one_year = timedelta(days=365)

    modified_count = 0
    skipped_count = 0

    # 4. 逐个计算偏移量并判断是否需要修改
    for item in valid_photos:
        path = item["path"]
        orig_dt = item["original_dt"]
        filename = os.path.basename(path)

        # 检查是否在目标设定时间的1年之内 (|orig_dt - target_base_dt| <= 365天)
        if abs(orig_dt - target_base_dt) <= one_year:
            print(f"[跳过] {filename} | 原EXIF: {orig_dt} (与目标时间相差在1年内)")
            skipped_count += 1
            continue

        # 计算与最早照片的 delta
        delta = orig_dt - earliest_dt
        new_dt = target_base_dt + delta

        # 更新 EXIF
        update_exif_time(path, new_dt)
        print(f"[修改] {filename} | 原时间: {orig_dt} -> 新时间: {new_dt} (偏移: +{delta})")
        modified_count += 1

    print("\n处理完成:")
    print(f"- 已修改: {modified_count} 张")
    print(f"- 跳过 (1年内): {skipped_count} 张")

if __name__ == "__main__":
    folder = input("请输入图片所在文件夹路径: ").strip().strip('"').strip("'")
    base_time = input("请输入第一张照片的目标时间 (格式 YYYY-MM-DD HH:MM:SS): ").strip()

    if os.path.isdir(folder):
        process_photos(folder, base_time)
    else:
        print("文件夹路径不存在，请检查后重试。")