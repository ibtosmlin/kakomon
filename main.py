import csv
import fitz
from pathlib import Path

"""フォルダ"""
datafolder = Path(r"\\NAS-DS218\home\過去問PDF")
indata = datafolder / "Original"
current = Path(__file__).parent
current_data = current / "data.csv"

""""""
def read_range(string:str) -> list[tuple[int, int]]:
    ret = []
    for substr in string.replace(" ", "").split(","):
        if "-" in substr:
            fmto = list(map(int, substr.split("-")))
            assert len(fmto) == 2
            fm, to = fmto
        else:
            fm = to = int(substr)
        if fm > to:
            ret.extend([(p, p) for p in range(fm, to-1, -1)])
        else:
            ret.append((fm, to))
    return ret

def add_blank_front(doc, instext):
    ref_page = doc[0]
    page_width, page_height = ref_page.rect.width, ref_page.rect.height
    front_page = doc.new_page(0, width=page_width, height=page_height)

    font_size = 25
    label_text = instext
    text_rect = fitz.Rect(0, page_height//2, page_width, page_height)
    front_page.insert_textbox(
        text_rect,
        label_text,
        fontname = "japan",
        fontsize=font_size,
        align=1,  # 中央揃え
        color=(0, 0, 0)  # 黒色
    )


def add_blank_end(doc, pagesinpaper:int=8):
    ref_page = doc[0]
    page_width, page_height = ref_page.rect.width, ref_page.rect.height

    # フォント設定
    font_size = 14
    label_text = "空白ページ"

    blank_page = doc.new_page(-1, width=page_width, height=page_height)
    text_rect = fitz.Rect(0, 0, page_width, page_height)
    blank_page.insert_textbox(
        text_rect,
        label_text,
        fontname = "japan",
        fontsize=font_size,
        align=1,  # 中央揃え
        color=(0, 0, 0)  # 黒色
    )


with current_data.open(mode="r", encoding="utf8") as f:
    reader = csv.reader(f)
    datas = [row for row in reader if row[0].capitalize() == 'Y']

current_file = ""
current_doc = None
for _, ifile, ofile, fmto, insertfrontpage, page8, rotate in datas:
    if current_file != ifile:
        current_file = ifile
        current_doc = fitz.open(indata / f"{current_file}.pdf")
    # 新しいPDFを作成
    extracted = fitz.open()
    for (fm, to) in read_range(fmto):
        extracted.insert_pdf(current_doc, from_page=fm-1, to_page=to-1)
        print(ofile, fm, to,)
    if insertfrontpage=='Y':
        add_blank_front(extracted, ofile)
    if page8=='Y':
        add_blank_end(extracted)
    ofold = ofile.split("-")[0]
    opath = datafolder / ofold
    opath.mkdir(exist_ok=True)
    extracted.save(opath / f"{ofile}.pdf")
    extracted.close()
