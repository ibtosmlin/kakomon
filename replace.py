import fitz
from pathlib import Path

datawarehouse = Path(r"\\NAS-DS218\home\過去問PDF\_bkup")
current = Path(__file__).parent

"""基本"""
filename = "x"
p = Path(datawarehouse)

"""マージ"""

# 新しいPDFを作成
merged_pdf = fitz.open()

# 各ファイルを読み込んでページを追加
pdf = fitz.open(datawarehouse / "帝京大学付録.pdf")
pdf2 = fitz.open(datawarehouse / "teikyo.pdf")

for i in range(len(pdf)):
    if i+1 == 10:
        merged_pdf.insert_pdf(pdf2, from_page=1, to_page=1)
    else:
        merged_pdf.insert_pdf(pdf, from_page=i, to_page=i)

pdf.close()
# 保存
merged_pdf.save(datawarehouse / "帝京大学付録2.pdf")
merged_pdf.close()
