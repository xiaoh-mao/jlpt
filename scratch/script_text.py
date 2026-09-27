# 听力原文 PDF（有文字层，2012 年的也有）-> 按题分块。必须用 PyMuPDF：CID 字体没 ToUnicode，pdftotext 抽出来是乱码。pages.py / build_trans.py 用，也能直接看：
#   python scratch\script_text.py 2018 N2 [--dump]   --dump 把每题原文（折行接好）写到 scratch/script/<年>-<级>.txt，写译文照着它
#   extract() -> [{'m': 問題号, 'q': 'H'(大题标题)|'例'|'1'|…, 'page', 'y', 'end': (页, 最后一行底 y), 'lines': [段落…]}]，坐标 pt
import os, re, sys, pymupdf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z2H = str.maketrans('０１２３４５６７８９', '0123456789')
SPEAKER = re.compile(r'^(Ｍ|Ｆ|男|女|[ＭＦ][０-９\d]?|[ＭＦ]\s*\d)\s*[：:]')

def page_lines(p):
    """一页 -> [(y0, y1, x0, x1, 文字)]，振假名（小字）去掉，同一行的 span 拼起来"""
    spans = []
    for b in p.get_text('rawdict')['blocks']:
        if b['type'] != 0: continue
        for l in b['lines']:
            for s in l['spans']:
                t = ''.join(c['c'] for c in s['chars'])
                if s['size'] < 7.5 or not t.strip(): continue
                spans.append((s['bbox'][1], s['bbox'][0], s['bbox'][3], s['bbox'][2], t))
    spans.sort()
    lines = []
    for y0, x0, y1, x1, t in spans:
        if lines and abs(lines[-1][0] - y0) < 3:
            lines[-1][1].append((x0, x1, y1, t))
        else:
            lines.append((y0, [(x0, x1, y1, t)]))
    out = []
    for y0, ps in lines:
        ps.sort()
        out.append((y0, max(p[2] for p in ps), ps[0][0], max(p[1] for p in ps), ''.join(p[3] for p in ps)))
    return out

def extract(vol, lv):
    d = pymupdf.open(os.path.join(ROOT, 'papers', vol, f'{lv}script.pdf'))
    blocks, m, cur = [], 0, None
    for pi, p in enumerate(d):
        H = p.rect.height
        lines = [l for l in page_lines(p) if 40 <= l[0] <= H - 40]      # 页眉页脚
        right = max((l[3] for l in lines), default=0)
        for y0, y1, x0, x1, text in lines:
            t = text.strip().translate(Z2H)
            if x0 < 90:                                   # 标题行整行就是「問題N」「例」「N番」，不看字体（有的数字不是粗体）
                mm = re.fullmatch(r'問題\s*(\d+)', t)
                if mm:
                    m = int(mm[1]); cur = {'m': m, 'q': 'H', 'page': pi, 'y': y0, 'end': (pi, y1), 'lines': []}; blocks.append(cur); continue
                if re.fullmatch(r'(例|れい|\d+\s*(?:番|ばん))', t):
                    q = '例' if t in ('例', 'れい') else re.match(r'\d+', t)[0]
                    cur = {'m': m, 'q': q, 'page': pi, 'y': y0, 'end': (pi, y1), 'lines': []}; blocks.append(cur); continue
            if cur is None: continue
            cur['end'] = (pi, y1)
            # 上一行写到了右边界 = 这行是折行接上去的
            if cur['lines'] and cur.get('_wrap') and not SPEAKER.match(t) and not re.match(r'^\d[．.]', t):
                cur['lines'][-1] += t
            else:
                cur['lines'].append(t)
            cur['_wrap'] = x1 > right - 25
    for b in blocks: b.pop('_wrap', None)
    return blocks

if __name__ == '__main__':
    vol, lv = sys.argv[1], sys.argv[2]
    out = []
    for b in extract(vol, lv):
        if b['q'] == 'H': out.append(f"\n# ===== 問題{b['m']}"); continue
        out.append(f"@{b['m']}-{b['q']}")
        out += b['lines']
    txt = '\n'.join(out).strip() + '\n'
    if '--dump' in sys.argv:
        os.makedirs(os.path.join(ROOT, 'scratch', 'script'), exist_ok=True)
        open(os.path.join(ROOT, 'scratch', 'script', f'{vol}-{lv}.txt'), 'w', encoding='utf-8').write(txt)
    else:
        print(txt)
