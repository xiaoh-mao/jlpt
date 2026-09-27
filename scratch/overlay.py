# 把探测到的位置画回页面图，拼成一张小图看：python scratch\overlay.py 2012-N1 G [起页 止页]  -> scratch/view/ov-2012-N1-G.png
#   红 = 题号框 / 「N番」，蓝 = 大题标题
import os, sys
import numpy as np
import pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxes, pages
tid, doc = sys.argv[1], sys.argv[2]
vol, lv = tid.split('-')
ev = pages.doc_events_2018(vol, lv, doc) if vol == '2018' else boxes.doc_events_2012(vol, lv, doc)
n = pymupdf.open(os.path.join(boxes.ROOT, 'papers', vol, f'{lv}{doc}.pdf')).page_count
a0, a1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1, n - 1)
tiles = []
for i in range(a0, a1 + 1):
    a = boxes.img(vol, lv, doc, i)
    rgb = np.stack([a, a, a], -1).copy()
    for p, y, k in ev:
        if p != i: continue
        yy = int(y * boxes.K)
        col = (40, 40, 255) if k == 'head' else (255, 0, 0)
        rgb[max(0, yy - 3):yy + 3, :] = col
    small = rgb[::3, ::3]
    tiles.append(small)
h = max(t.shape[0] for t in tiles); w = max(t.shape[1] for t in tiles)
cols = 6
rows = (len(tiles) + cols - 1) // cols
canvas = np.full((rows * (h + 6), cols * (w + 6), 3), 200, np.uint8)
for j, t in enumerate(tiles):
    r, c = divmod(j, cols)
    canvas[r * (h + 6):r * (h + 6) + t.shape[0], c * (w + 6):c * (w + 6) + t.shape[1]] = t
canvas = np.ascontiguousarray(canvas)
out = os.path.join(boxes.HERE, 'view', f'ov-{tid}-{doc}.png')
pymupdf.Pixmap(pymupdf.csRGB, canvas.shape[1], canvas.shape[0], canvas.tobytes(), 0).save(out)
print(out, [(p, round(y * boxes.K), k[0]) for p, y, k in ev])
