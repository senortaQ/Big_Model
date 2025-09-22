# EXIF Date Watermark CLI

命令行程序：读取图片 EXIF 拍摄时间（年月日），绘制为文字水印到图片上，输出到原目录的子目录 `_watermark`。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python main.py <路径> [--font-size 36] [--color #FFFFFF] \
  [--position bottom-right|bottom-left|top-right|top-left|center] \
  [--margin 20] [--font-path C:/Windows/Fonts/msyh.ttc] [--recursive]
```

- `路径`：图片文件路径或目录路径。如果是文件，则使用其所在目录作为输入目录。
- `--font-size`：字体大小（像素）。默认 36。
- `--color`：颜色（支持如 `#RRGGBB` 或命名颜色）。默认 `#FFFFFF`。
- `--position`：水印位置。默认 `bottom-right`。
- `--margin`：距离边缘的像素边距。默认 20。
- `--font-path`：可选，指定 .ttf/.otf 字体文件路径。不传则使用系统/默认字体。
- `--recursive`：当路径为目录时，递归处理子目录（跳过 `_watermark` 目录）。

## 说明

- 优先使用 EXIF 的 `DateTimeOriginal`，其次 `DateTime`；若无，则回退为文件修改时间。
- 输出文件保存在 `<原目录>/_watermark/` 中，文件名与原图一致。

## 示例

```bash
# 处理单个文件所在目录
python main.py photo/微信图片_20250922192243.jpg --position center --font-size 42

# 处理整个目录（递归）
python main.py photo --recursive --color "#FFCC00" --position top-left
```
