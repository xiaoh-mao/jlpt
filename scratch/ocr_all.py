# 2012 年的卷子是扫描图、没有文字层 -> Windows OCR（中文识别器，认得出数字和「問題」）找大题标题和「Nばん」。
# 结果缓存 scratch/ocr/2012-<级><doc>.txt，删了才重跑。
import os, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
for lv in ('N1', 'N2', 'N3', 'N4', 'N5'):
    for doc in 'VGRL':
        cache = os.path.join(HERE, 'ocr', f'2012-{lv}{doc}.txt')
        if os.path.exists(cache): continue
        files = sorted(glob.glob(os.path.join(ROOT, 'papers', '2012', 'img', f'{lv}{doc}-*.jpg')))
        r = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(HERE, 'ocr.ps1'), '-Lang', 'zh-Hans-CN'] + files, capture_output=True)
        if r.returncode: raise SystemExit(r.stderr.decode('utf-8', 'replace'))
        open(cache, 'wb').write(r.stdout)
        print(lv, doc, len(files), flush=True)
