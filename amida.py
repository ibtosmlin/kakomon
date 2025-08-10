from PIL import Image, ImageDraw, ImageFont
import random


# ─────────────────────────────
# 設定
# ─────────────────────────────

# outfile_name = "社会"
# candidates_input = [1,2,4,5,8,9,10,14,15,16,17,18,20,21,24,26,27,28,29,30,31,32,33]
# outfile_name = "理科"
# candidates_input = [1,2,3,5,7,8,9,10,11,12,14,15,16,18,19,20,22,23,25,26,27,28,29,30,31,32,33,34,35]
outfile_name = "算数"
candidates_input = [i for i in range(1, 36) if i!=2 and i!=3 and i!=13]


# ─────────────────────────────
# 候補の設定
# ─────────────────────────────

if isinstance(candidates_input, int):
    num_candidates = candidates_input
    candidates = random.sample(range(1, 1 + num_candidates), num_candidates)
else:
    num_candidates = len(candidates_input)
    candidates = candidates_input
candidates = random.sample(candidates, num_candidates)
candidates = [str(n) for n in candidates]


# ─────────────────────────────
# A4サイズ設定（横向き・300dpi）
# ─────────────────────────────
a4_width_px = 3508
a4_height_px = 2480

# ─────────────────────────────
# 表示設定（マージン・線・フォント）
# ─────────────────────────────
top_margin = 250
top_margin_bar = 50
bottom_margin = 250
bottom_margin_bar = 50
left_margin = 150
right_margin = 150
num_horizontal_lines = 90
font_size = 45
font_color = (0, 0, 0)
line_color = (150, 150, 150)
bg_color = (255, 255, 255)
line_width = 6
label_offset = 20

font_path = "C:/Windows/Fonts/COOPBL.TTF"
font = ImageFont.truetype(font_path, font_size)

# ─────────────────────────────
# あみだくじ構造計算（縦型）
# ─────────────────────────────
num_vertical_bars = len(candidates)
bar_spacing_y = int((a4_height_px - top_margin - top_margin_bar - bottom_margin - bottom_margin_bar) / num_horizontal_lines)
bar_spacing_x = int((a4_width_px - left_margin - right_margin) / num_vertical_bars)

# ─────────────────────────────
# ベース画像の作成（RGBモード）
# ─────────────────────────────
base_img = Image.new("RGB", (a4_width_px, a4_height_px), bg_color)
draw = ImageDraw.Draw(base_img)

# ─────────────────────────────
# 縦線の描画
# ─────────────────────────────
for i in range(num_vertical_bars):
    x = left_margin + (i + 0.5) * bar_spacing_x
    draw.line([(x, top_margin), (x, a4_height_px - bottom_margin)], fill=line_color, width=line_width)

# ─────────────────────────────
# 横線の描画（ランダム）
# ─────────────────────────────
for i in range(num_horizontal_lines):
    pos = random.randint(1, num_vertical_bars - 1)
    y = top_margin + top_margin_bar + int((i + 1) * bar_spacing_y)
    x_start = left_margin + (pos - 0.5) * bar_spacing_x
    x_end = left_margin + (pos + 0.5) * bar_spacing_x
    draw.line([(x_start, y), (x_end, y)], fill=line_color, width=line_width)

# ─────────────────────────────
# 候補ラベルの描画（中央揃え・下部）
# ─────────────────────────────
for i, label in enumerate(candidates):
    x_center = left_margin + (i + 0.5) * bar_spacing_x
    bbox = font.getbbox(label)
    text_width = bbox[2] - bbox[0]
    x = x_center - text_width // 2
    y = a4_height_px - bottom_margin + label_offset
    draw.text((x, y), label, font=font, fill=font_color)

# ─────────────────────────────
# PDFのみ保存（JPGは保存しない）
# ─────────────────────────────
base_img.save(f'{outfile_name}.pdf', "PDF", resolution=300.0)
