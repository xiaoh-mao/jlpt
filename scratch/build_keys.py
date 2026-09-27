# 从 papers/<卷>/N?answer.pdf 抽正答表 -> app/data/keys.js
# 依赖 Git 自带的 pdftotext（xpdf 4.06），-table 模式下每个「問題」是「题号行 + 答案行」两行一组
# （默认模式数字粘连、页序乱）。正答表只要数字和标题，它够用；日文正文它抽出来是乱码，那些用 PyMuPDF（见 script_text.py）。
import json, re, subprocess, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEC = {  # 正答表里的小标题 -> 程序里的分卷 id
    '言語知識(文字・語彙・文法)・読解': 'lang',
    '言語知識(文字・語彙)': 'vocab',
    '言語知識(文法)・読解': 'gram',
    '聴解': 'listen',
}

def text(pdf):
    out = subprocess.run(['pdftotext', '-q', '-table', '-enc', 'UTF-8', str(pdf), '-'],
                         capture_output=True, check=True).stdout.decode('utf-8')
    return unicodedata.normalize('NFKC', out)

def parse(pdf):
    secs, sec, cur, pending = {}, None, None, None
    for raw in text(pdf).splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith('●'):
            name = re.sub(r'\s+', '', line[1:])
            sec = SEC[name]
            secs[sec] = []
            cur = pending = None
            continue
        if sec is None:
            continue
        m = re.match(r'^問題\s*(\d+)\s+(.*)$', line)
        if m:
            cur = {'m': int(m.group(1)), 'items': []}
            secs[sec].append(cur)
            pending = m.group(2).split()
            continue
        toks = line.split()
        if cur is None or not re.search(r'\d', line):
            continue  # 页眉「正答表」、振り仮名之类
        subs = toks[1::2] if toks[0] == '質問' else [t[1:-1] for t in toks if re.fullmatch(r'\(\d\)', t)]
        if subs:  # 聴解 最后一题分两问：2012 写「質問1 質問2」，2018 写「(1) (2)」
            last = pending.pop()
            pending += [f'{last}-{n}' for n in subs]
            continue
        if pending is None:  # 续行题号（没有「問題」前缀）；页码也会落到这里，随后被下一个「問題」行顶掉
            pending = toks
            continue
        if not all(t in '1234' for t in toks):
            sys.exit(f'{pdf}: 問題{cur["m"]} 答案行不对: {line!r} (题号 {pending})')
        if len(toks) != len(pending):
            sys.exit(f'{pdf}: 問題{cur["m"]} 题号 {len(pending)} 个、答案 {len(toks)} 个: {pending} / {toks}')
        for lab, ans in zip(pending, toks):
            if lab != '例':
                cur['items'].append([lab, int(ans)])
        pending = None
    return secs

def check(level, secs):
    # 言語知識/读解 题号全卷连续；聴解每个問題从 1 起
    for sid, groups in secs.items():
        if sid == 'listen':
            for g in groups:
                labs = [l.split('-')[0] for l, _ in g['items']]
                want = [str(i) for i in range(1, int(labs[-1]) + 1)]
                assert sorted(set(labs), key=int) == want, (level, sid, g)
        else:
            nums = [int(l) for g in groups for l, _ in g['items']]
            assert nums == list(range(1, len(nums) + 1)), (level, sid, nums)
            ms = [g['m'] for g in groups]
            assert ms == list(range(1, len(ms) + 1)), (level, sid, ms)

keys = {}
for vol in ('2012', '2018'):
    for lv in ('N1', 'N2', 'N3', 'N4', 'N5'):
        pdf = ROOT / 'papers' / vol / f'{lv}answer.pdf'
        if not pdf.exists():
            print('缺', pdf); continue
        secs = parse(pdf)
        check(f'{vol}{lv}', secs)
        keys[f'{vol}-{lv}'] = secs
        print(vol, lv, {s: sum(len(g['items']) for g in gs) for s, gs in secs.items()})

out = ROOT / 'app' / 'data' / 'keys.js'
out.parent.mkdir(parents=True, exist_ok=True)
body = json.dumps(keys, ensure_ascii=False, separators=(',', ':'))
out.write_text('// 由 scratch/build_keys.py 从官方正答表 PDF 生成，别手改\nwindow.JLPT_KEYS=' + body + ';\n', encoding='utf-8')
print('写入', out)
