# 官方 PDF -> 页面图 papers/<年>/img/<级><doc>-<页>.jpg（150 dpi 灰度），已存在跳过。doc = V G R L script answer
import os, glob, pymupdf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DPI = 150
for vol in ('2012', '2018'):
    out = os.path.join(ROOT, 'papers', vol, 'img'); os.makedirs(out, exist_ok=True)
    for lv in ('N1', 'N2', 'N3', 'N4', 'N5'):
        for doc in ('V', 'G', 'R', 'L', 'script', 'answer'):
            d = pymupdf.open(os.path.join(ROOT, 'papers', vol, f'{lv}{doc}.pdf'))
            for i, p in enumerate(d):
                f = os.path.join(out, f'{lv}{doc}-{i + 1:02d}.jpg')
                if not os.path.exists(f):
                    p.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY).save(f, jpg_quality=75)
    print(vol, len(os.listdir(out)))
