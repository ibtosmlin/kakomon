import fitz
from pathlib import Path

datawarehouse = Path(r"C:\Users\eieib\OneDrive\From_BrotherDevice")
current = Path(__file__).parent

"""基本"""
filename = "x"
p = Path(datawarehouse)

# doc = fitz.open(f)
# print(len(doc))
# for page in doc:
#     page.set_rotation(90)  # 時計回りに90度回転

# doc.save("rotated_output.pdf")
# doc.close()

"""マージ"""
pdf_paths = ["都市大学2024-1.pdf", "都市大学2024-2.pdf"]

# 新しいPDFを作成
merged_pdf = fitz.open()

# 各ファイルを読み込んでページを追加
for path in pdf_paths:
    pdf = fitz.open(path)
    merged_pdf.insert_pdf(pdf)
    pdf.close()

# 保存
merged_pdf.save("都市大学2024.pdf")
merged_pdf.close()
