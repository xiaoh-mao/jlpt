# 卷子上的题号框 / 大题标题 / 听力「N番」的位置探测（pages.py 用）。坐标一律是 150 dpi 页面图的像素。
import os, re, glob
import numpy as np
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
K = 150 / 72
Z2H = str.maketrans('０１２３４５６７８９', '0123456789')

def img(vol, lv, doc, i):
    p = pymupdf.Pixmap(os.path.join(ROOT, 'papers', vol, 'img', f'{lv}{doc}-{i + 1:02d}.jpg'))
    return np.frombuffer(p.samples, np.uint8).reshape(p.height, p.stride)[:, :p.width]

# ---------------------------------------------------------------- 2018：有文字层
def boxes_2018(page):
    """题号框：矢量画的小矩形（约 17×11 pt）-> [(x, y)] pt。
    里面有题号字形（EdiF 子集字体）的才算；个别框里的数字是画出来的，跟同页别的题号框左对齐也算（装饰小框不对齐）"""
    nums = [(x, y) for x, y, size, font, t in spans(page) if font.startswith('EdiF')]
    rects = [d['rect'] for d in page.get_drawings()
             if 12 <= d['rect'].width <= 34 and 8 <= d['rect'].height <= 16 and d['type'] in ('s', 'fs')]
    good = [r for r in rects if any(r.x0 - 2 <= x <= r.x1 and r.y0 - 3 <= y <= r.y1 for x, y in nums)]
    out = [(r.x0, r.y0) for r in rects if r in good or any(abs(r.x0 - g.x0) < 1 and abs(r.width - g.width) < 1 for g in good)]
    out.sort(key=lambda b: (round(b[1]), b[0]))
    ded = []
    for b in out:
        if not ded or abs(ded[-1][1] - b[1]) > 3 or abs(ded[-1][0] - b[0]) > 3: ded.append(b)
    return ded

def spans(page):
    res = []
    for b in page.get_text('rawdict')['blocks']:
        if b['type'] != 0: continue
        for l in b['lines']:
            for s in l['spans']:
                t = ''.join(c['c'] for c in s['chars'])
                if t.strip(): res.append((s['bbox'][0], s['bbox'][1], s['size'], s['font'], t))
    return res

def heads_2018(page):
    """大题标题「問題N」「もんだいN」（粗体大字）-> [y pt]；「もんだい」和数字分成两个 span 的去重"""
    ys = sorted(y for x, y, size, font, t in spans(page)
                  if re.fullmatch(r'(問題|もんだい)\s*[０-９\d]*', t.strip()) and size >= 11 and x < 140)
    return [y for i, y in enumerate(ys) if i == 0 or y - ys[i - 1] > 30]   # 标题上面的振假名「もんだい」

def listen_2018(page):
    """听力卷上每题的「N番」「例」-> [(y, 'ex'|'q')]；「番」字本身是文字层（数字在子集字体里认不出，不用）"""
    out = []
    for x, y, size, font, t in spans(page):
        if x > 140 or size < 15: continue                # 小字是振假名
        if re.match(r'(番|ばん)', t.strip()): out.append((y, 'q'))
        elif t.strip() in ('例', 'れい'): out.append((y, 'ex'))
    return sorted(out)

# ---------------------------------------------------------------- 2012：扫描图，没有文字层
def ocr_lines(vol, lv, doc):
    """OCR 缓存 -> {页: [(x, y, w, h, 文字)]}（像素）"""
    pages, cur = {}, None
    for ln in open(os.path.join(HERE, 'ocr', f'{vol}-{lv}{doc}.txt'), encoding='utf-8-sig'):
        ln = ln.rstrip('\n')
        if ln.startswith('### '):
            cur = int(re.search(r'-(\d+)\.jpg', ln)[1]) - 1; pages[cur] = []; continue
        if '\t' not in ln or cur is None: continue
        g, t = ln.split('\t', 1)
        x, y, w, h = map(int, g.split())
        pages[cur].append((x, y, w, h, t.replace(' ', '')))
    return pages

def boxes_img(a):
    """题号框：浅灰细线的小方框（约 33×21 px）-> [(x, y)] px。只看左边距那一条（左边线 x 90–200）。
    认法：左右两条竖线（高 17–27、相距 29–41）+ 上边或下边至少一条横线（扫描有时把上边丢了），
    框里不能是实心（页边灰色标签），框的上下紧挨着不能有线（表格格子）。"""
    ink = a[:, :260] < 215
    H = ink.shape[0]
    runs = {}                                            # x -> [(y0, y1)] 竖线段
    for x in range(88, 250):
        col = ink[:, x]
        d = np.flatnonzero(np.diff(np.concatenate(([0], col.astype(np.int8), [0]))))
        runs[x] = [(y0, y1) for y0, y1 in zip(d[::2], d[1::2]) if 17 <= y1 - y0 <= 27]
    out = []
    for x in range(88, 202):
        for y0, y1 in runs[x]:
            for w in range(29, 42):
                hit = next(((r0, r1) for r0, r1 in runs.get(x + w, []) if abs(r0 - y0) <= 3 and abs(r1 - y1) <= 3), None)
                if not hit: continue
                top, bot = min(y0, hit[0]), max(y1, hit[1])
                edge = lambda yy: ink[max(0, yy - 1):yy + 2, x:x + w].any(0).mean() > .85
                if not (edge(top) or edge(bot - 1)): continue
                inner = ink[top + 3:bot - 3, x + 3:x + w - 3].mean()
                alone = ink[max(0, top - 7):top - 3, x:x + w].mean() < .15 and ink[bot + 3:bot + 7, x:x + w].mean() < .15
                ends = not ink[max(0, top - 6):top - 2, x - 1:x + 2].any() and not ink[bot + 2:bot + 6, x - 1:x + 2].any()   # 竖线不往外伸（插图的边框）
                gray = np.median(a[top + 2:bot - 2, max(0, x - 1):x + 2].min(1)) > 100    # 框线是浅灰的，字（「問」之类）是黑的
                if inner < .7 and alone and gray and ends:
                    out.append((x, int(top))); break
    out.sort(key=lambda b: (b[1], b[0]))
    ded = []
    for b in out:
        if not ded or abs(ded[-1][1] - b[1]) > 8: ded.append(b)
    return ded

def digit_blobs(a):
    """听力卷「Nばん」的粗体大数字：左边距 x 110–150 里高 26–38 px 的一块墨 -> [y] px"""
    band = a[:, 110:150] < 110
    rows = band.any(1)
    out, y, H = [], 0, len(rows)
    while y < H:
        if not rows[y]: y += 1; continue
        y0 = y
        while y < H and rows[y]: y += 1
        if 26 <= y - y0 <= 38:
            cols = band[y0:y].any(0)
            if 6 <= cols.sum() <= 28 and band[y0:y].mean() > .12: out.append(y0)
    return out

def doc_events_2012(vol, lv, doc):
    """-> [(页, y pt, 'head'|'box'|'q')]；y 换成 pt 跟 2018 统一"""
    oc = ocr_lines(vol, lv, doc)
    ev = []
    n = len(glob.glob(os.path.join(ROOT, 'papers', vol, 'img', f'{lv}{doc}-*.jpg')))
    for i in range(n):
        lines = oc.get(i, [])
        if i == 0 and any('Notes' in t or 'Listening' in t for *_, t in lines): continue    # 封面（只有 V、L 有；G、R 第 0 页就是正文）
        a = img(vol, lv, doc, i)
        if doc == 'L':
            heads = [y for x, y, w, h, t in lines if h >= 45 and x < 300 and y < 400]
            for y in heads: ev.append((i, y / K, 'head'))
            qs = [y for x, y, w, h, t in lines if x < 145 and h >= 26 and re.match(r'\d', t) and not t.startswith('質')]
            for y in digit_blobs(a):
                if not any(abs(y - q) < 25 for q in qs): qs.append(y)
            for y in qs:
                if not any(abs(y - hy) < 60 for hy in heads): ev.append((i, y / K, 'q'))
        else:
            for x, y, w, h, t in lines:
                if x < 200 and re.match(r'^[問问][題题]\d', t): ev.append((i, y / K, 'head'))
            for x, y in boxes_img(a): ev.append((i, y / K, 'box'))
    return sorted(ev)
