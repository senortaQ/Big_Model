import os
from PIL import Image, ImageDraw, ImageFont
import exifread
from datetime import datetime

def get_exif_date(image_path):
    """
    读取图片的EXIF信息中的拍摄时间
    """
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f)
            
        # 尝试获取拍摄时间
        date_taken = None
        for tag in ('EXIF DateTimeOriginal', 'EXIF DateTimeDigitized', 'Image DateTime'):
            if tag in tags:
                date_taken = str(tags[tag])
                break
                
        if date_taken:
            # 将日期字符串转换为datetime对象
            dt = datetime.strptime(date_taken, '%Y:%m:%d %H:%M:%S')
            return dt.strftime('%Y年%m月%d日')
        return None
    except:
        return None

def add_watermark(image_path, text, font_size=36, color=(255, 255, 255), position='right-bottom'):
    """
    在图片上添加水印
    """
    try:
        # 打开图片
        img = Image.open(image_path)
        
        # 创建绘图对象
        draw = ImageDraw.Draw(img)
        
        # 加载字体
        try:
            font = ImageFont.truetype("simhei.ttf", font_size)
        except:
            # 如果找不到指定字体，使用默认字体
            font = ImageFont.load_default()
        
        # 获取文本大小
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # 计算水印位置
        img_width, img_height = img.size
        padding = 10
        
        if position == 'left-top':
            x = padding
            y = padding
        elif position == 'center':
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
        else:  # 默认右下角
            x = img_width - text_width - padding
            y = img_height - text_height - padding
        
        # 绘制水印文字
        draw.text((x, y), text, font=font, fill=color)
        
        return img
    except Exception as e:
        print(f"添加水印时出错: {str(e)}")
        return None

def process_images(input_path):
    """
    处理指定路径下的所有图片
    """
    if not os.path.exists(input_path):
        print(f"错误: 路径 '{input_path}' 不存在")
        return
    
    # 如果输入的是文件，则将其目录作为基准目录
    if os.path.isfile(input_path):
        base_dir = os.path.dirname(input_path)
        files = [input_path]
    else:
        base_dir = input_path
        # 获取所有图片文件
        files = []
        for f in os.listdir(input_path):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                files.append(os.path.join(input_path, f))
    
    # 创建输出目录
    output_dir = os.path.join(base_dir, os.path.basename(base_dir) + '_watermark')
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理每个图片
    for img_path in files:
        # 获取拍摄日期
        date_text = get_exif_date(img_path)
        if not date_text:
            date_text = "未知日期"  # 如果无法获取拍摄日期，使用默认文本
        
        # 添加水印
        watermarked = add_watermark(
            img_path,
            date_text,
            font_size=int(input("请输入字体大小 (默认36): ") or 36),
            color=eval(input("请输入颜色RGB值，格式(R,G,B) (默认白色(255,255,255)): ") or "(255,255,255)"),
            position=input("请输入水印位置 (left-top/center/right-bottom，默认right-bottom): ") or "right-bottom"
        )
        
        if watermarked:
            # 保存处理后的图片
            output_path = os.path.join(output_dir, os.path.basename(img_path))
            watermarked.save(output_path)
            print(f"已处理: {os.path.basename(img_path)}")
        else:
            print(f"处理失败: {os.path.basename(img_path)}")

def main():
    print("图片水印添加工具")
    print("=" * 30)
    
    # 获取用户输入
    input_path = input("请输入图片文件或目录路径: ").strip('"')  # 去除可能的引号
    
    if not input_path:
        print("错误: 请提供有效的路径")
        return
    
    process_images(input_path)
    print("处理完成!")

if __name__ == "__main__":
    main()
