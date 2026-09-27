# 页面图上的定位 -> app/data/tests.js（前端「点题号跳到卷子那题」「点题号跳到录音那题」用）
#   每道题在卷子哪页哪个高度、每个大题标题在哪、听力原文里每题在哪、录音里每题从第几秒开始。
#   页面图先跑 scratch\render.py；2012 年的扫描卷要先跑 scratch\ocr_all.py（OCR 缓存在 scratch/ocr/）。
#   核对：python scratch\overlay.py <年-级> <doc> 把位置画回页面图（scratch/view/）。
# 用法：python scratch\pages.py
import os, re, sys, json
sys.stdout.reconfigure(encoding='utf-8'); sys.stderr.reconfigure(encoding='utf-8')   # 控制台默认 GBK，打印中文会乱码
import pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxes, script_text, cues

ROOT = boxes.ROOT
K = boxes.K
# levels.js 的 parts：每块对应哪个 sec、哪几个問題
PARTS = {
    'N1': {'V': ('lang', 1, 4), 'G': ('lang', 5, 7), 'R': ('lang', 8, 99), 'L': ('listen', 1, 99)},
    'N2': {'V': ('lang', 1, 6), 'G': ('lang', 7, 9), 'R': ('lang', 10, 99), 'L': ('listen', 1, 99)},
}
for lv in ('N3', 'N4', 'N5'):
    PARTS[lv] = {'V': ('vocab', 1, 99), 'G': ('gram', 1, 3), 'R': ('gram', 4, 99), 'L': ('listen', 1, 99)}

def load_keys():
    s = open(os.path.join(ROOT, 'app', 'data', 'keys.js'), encoding='utf-8').read()
    return json.loads(s[s.index('{'):s.rstrip().rstrip(';').rindex('}') + 1])

def px(y): return round(y * K)

def doc_events_2018(vol, lv, doc):
    """-> [(页, y pt, 'head'|'box'|'q'|'ex')]"""
    d = pymupdf.open(os.path.join(ROOT, 'papers', vol, f'{lv}{doc}.pdf'))
    ev = []
    for i, p in enumerate(d):
        for y in boxes.heads_2018(p): ev.append((i, y, 'head'))
        if doc == 'L':
            for y, k in boxes.listen_2018(p): ev.append((i, y, k))
        else:
            for x, y in boxes.boxes_2018(p):
                if x < 140: ev.append((i, y, 'box'))
    return sorted(ev)

def assign(ev, groups, doc, warn):
    """events + 这份卷子里的大题 [(sec, m, [题标签…])] -> ({题key: [doc, 页, y, 准]}, {大题key: [doc, 页, y]})
    文字・語彙/文法/読解：题号框按顺序对上所有题（总数对得上就行，扫描卷的大题标题常认不出，N4/N5 的「もんだい」中文 OCR 全认不出）；
    听力：每题的「N番」要在自己那个大题的标题之后（问题3 以后很多大题卷上没有逐题的东西，只能定位到大题）。"""
    heads = [e for e in ev if e[2] == 'head']
    kind = 'q' if doc == 'L' else 'box'
    marks = [e for e in ev if e[2] == kind]
    q, g = {}, {}
    ok_heads = len(heads) == len(groups)
    if not ok_heads: warn(f'{doc}: 大题标题 {len(heads)} 个，应有 {len(groups)} 个')
    nums_of = lambda labels: list(dict.fromkeys(lb.split('-')[0] for lb in labels)) if doc == 'L' else labels
    total = sum(len(nums_of(lbs)) for _, _, lbs in groups)
    seq = doc != 'L' and len(marks) == total
    if doc != 'L' and not seq: warn(f'{doc}: 题号框 {len(marks)} 个，应有 {total} 个')
    i = 0
    for gi, (sec, m, labels) in enumerate(groups):
        nums = nums_of(labels)
        if seq:
            mine = marks[i:i + len(nums)]; i += len(nums)
        elif ok_heads:
            h, nxt = heads[gi], heads[gi + 1] if gi + 1 < len(heads) else (999, 0, '')
            mine = [e for e in marks if (h[0], h[1]) < (e[0], e[1]) < (nxt[0], nxt[1])]
            if doc == 'L' and len(mine) == len(nums) + 1: mine = mine[1:]      # 扫描卷的「れい」也被当成了题号
            if mine and len(mine) != len(nums): warn(f'{doc} 問題{m}: 找到 {len(mine)} 个题号，应有 {len(nums)} 个')
            if len(mine) != len(nums): mine = []
        else:
            mine = []
        if ok_heads:
            h = heads[gi]; gpos = [doc, h[0], px(h[1]) - 8]
        elif mine:                                   # 标题没认出来：定位到第一题上面一截（标题和例题一般就在那儿）
            gpos = [doc, mine[0][0], max(0, px(mine[0][1]) - 260)]
        else:
            gpos = None
        if gpos: g[f'{sec}:{m}'] = gpos
        for lb in labels:
            key = f'{sec}:{m}:{lb}'
            if mine:
                e = mine[nums.index(lb.split('-')[0])]; q[key] = [doc, e[0], px(e[1]) - 8, 1]
            elif gpos:
                q[key] = gpos + [0]
    return q, g

def build(vol, lv, keys):
    tid = f'{vol}-{lv}'
    warns = []
    warn = lambda s: warns.append(s)
    out = {'docs': {}, 'q': {}, 'g': {}}
    for doc in ('V', 'G', 'R', 'L', 'script', 'answer'):
        d = pymupdf.open(os.path.join(ROOT, 'papers', vol, f'{lv}{doc}.pdf'))
        r = d[0].rect
        out['docs'][doc] = {'pages': len(d), 'w': round(r.width * K), 'h': round(r.height * K)}
    for doc in 'VGRL':
        sec, a, b = PARTS[lv][doc]
        groups = [(sec, g['m'], [x[0] for x in g['items']]) for g in keys[tid].get(sec, []) if a <= g['m'] <= b]
        if not groups: continue
        ev = doc_events_2018(vol, lv, doc) if vol == '2018' else boxes.doc_events_2012(vol, lv, doc)
        q, g = assign(ev, groups, doc, warn)
        out['q'].update(q); out['g'].update(g)
    # 听力原文里每题的位置
    blocks = script_text.extract(vol, lv)
    s, sg = {}, {}
    for bl in blocks:
        if bl['q'] == 'H': sg[f"listen:{bl['m']}"] = [bl['page'], px(bl['y']) - 8]
    for g in keys[tid]['listen']:
        for lb, _ in g['items']:
            n = lb.split('-')[0]
            bl = next((x for x in blocks if x['m'] == g['m'] and x['q'] == n), None)
            if bl: s[f"listen:{g['m']}:{lb}"] = [bl['page'], px(bl['y']) - 8]
            else: warn(f'原文里没找到 問題{g["m"]} {n}番')
    out['s'], out['sg'] = s, sg
    out['cue'] = cues.cues(vol, lv, keys[tid]['listen'], warn)
    return out, warns

def main():
    keys = load_keys()
    data = {}
    for vol in ('2012', '2018'):
        for lv in ('N1', 'N2', 'N3', 'N4', 'N5'):
            tid = f'{vol}-{lv}'
            data[tid], warns = build(vol, lv, keys)
            exact = sum(1 for v in data[tid]['q'].values() if v[3])
            print(tid, f"题号定位 {exact}/{len(data[tid]['q'])}", f"原文 {len(data[tid]['s'])}", f"录音 {len(data[tid]['cue'])}")
            for w in warns: print('   !', w)
    with open(os.path.join(ROOT, 'app', 'data', 'tests.js'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('// 由 scratch/pages.py 生成，别手改。坐标是 150 dpi 页面图（papers/<年>/img/<级><doc>-<页>.jpg）的像素，页从 0 数。\n'
                '// docs 每份的页数和页面尺寸；q 题key -> [doc, 页, y, 准不准]（不准 = 用的大题标题位置）；g 大题key -> [doc, 页, y]；\n'
                '// s / sg 听力原文（script）里每题 / 每个大题 -> [页, y]；cue 题key -> 这题在 問題N 那段录音里从第几秒开始。\n'
                'window.JLPT_TESTS = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')

if __name__ == '__main__':
    main()
