# 听力原文的中文译文 -> app/data/trans.js。
#   译文手写在 scratch/trans/<年>-<级>.txt：「@問題-题」开一段（@1-例、@1-3），下面一行一句；
#   对话行写「男：」「女：」「女1：」，情景说明、提问、念的选项（「1. …」）不带说话人。
#   这里只算每段译文插在原文页面图的哪儿：这题最后一行字和下一题标题之间的空白正中；下一题在下一页就插在这页末尾。
#   原文每题的位置用 script_text.extract（原文 PDF 有文字层）。
# 用法：python scratch\build_trans.py [年-级 …]   不给 = 把有译文文件的都做一遍
import os, re, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymupdf, script_text

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TDIR = os.path.join(HERE, 'trans')
K = 150 / 72

def parse(path):
    out, cur = {}, None
    for ln in open(path, encoding='utf-8'):
        ln = ln.strip()
        if not ln or ln.startswith('#'): continue
        m = re.fullmatch(r'@(\d+)-(例|\d+)', ln)
        if m:
            key = f'{m[1]}-{m[2]}'
            assert key not in out, (path, '重复', key)
            cur = out[key] = []; continue
        assert cur is not None, (path, '第一段前面有字', ln)
        cur.append(ln)
    return out

def build(vol, lv):
    tid = f'{vol}-{lv}'
    tr = parse(os.path.join(TDIR, f'{tid}.txt'))
    blocks = script_text.extract(vol, lv)
    H = round(pymupdf.open(os.path.join(ROOT, 'papers', vol, f'{lv}script.pdf'))[0].rect.height * K)
    want = [f"{b['m']}-{b['q']}" for b in blocks if b['q'] != 'H']
    miss = [k for k in want if k not in tr]; extra = [k for k in tr if k not in want]
    assert not miss and not extra, (tid, '缺', miss, '多', extra)
    segs = []
    for i, b in enumerate(blocks):
        if b['q'] == 'H': continue
        ep, ey = b['end']
        nxt = blocks[i + 1] if i + 1 < len(blocks) else None
        if nxt and nxt['page'] == ep:
            at = [ep, round((ey + nxt['y']) / 2 * K)]
        else:
            at = [ep, H]
        lines = tr[f"{b['m']}-{b['q']}"]
        assert lines, (tid, b['m'], b['q'], '译文是空的')
        segs.append({'m': b['m'], 'q': b['q'], 'at': at, 'lines': lines})
    return segs

def main():
    out_path = os.path.join(ROOT, 'app', 'data', 'trans.js')
    s = open(out_path, encoding='utf-8').read()
    data = json.loads(s[s.index('{'):s.rstrip().rstrip(';').rindex('}') + 1])
    want = set(sys.argv[1:])
    for src in sorted(glob.glob(os.path.join(TDIR, '*-N*.txt'))):
        tid = os.path.basename(src)[:-4]
        if want and tid not in want: continue
        vol, lv = tid.split('-')
        data[tid] = build(vol, lv)
        print(tid, len(data[tid]), '段')
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('// 由 scratch/build_trans.py 生成，别手改；译文原稿在 scratch/trans/<年>-<级>.txt。\n'
                '// 每套一个数组，一题一段：m 問題号，q 题号（或「例」），at [原文页(0 起), y 像素] 译文插在那儿（y = 页高 = 插在这页后面），lines 译文。\n'
                'window.JLPT_TRANS = ' + json.dumps(dict(sorted(data.items())), ensure_ascii=False, separators=(',', ':')) + ';\n')

if __name__ == '__main__':
    main()
