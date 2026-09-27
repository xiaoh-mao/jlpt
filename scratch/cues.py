# 录音里每道题从第几秒开始（每个 問題 一段 mp3）。
#   每题后面是一段长静音（作答时间，8–12 秒），第 k 题就从第 k−1 段长静音结束处开始；
#   第 1 题前面是说明和例题：分界是「停 3 秒 · では、始めます · 停 3 秒」，见 cues() 里的注释。
#   长静音段数必须等于题数（3-1/3-2 这种各算一段），对不上就报出来。静音检测结果缓存在 scratch/sil/。
import os, re, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FFMPEG = os.environ.get('FFMPEG') or shutil.which('ffmpeg') or r'D:\losslesscut\resources\ffmpeg.exe'   # 环境变量 FFMPEG > PATH > 作者本机
LONG = 5.5

def silences(path):
    cache = os.path.join(HERE, 'sil', os.path.basename(os.path.dirname(path)) + '-' + os.path.basename(path) + '.txt')
    if not os.path.exists(cache):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        r = subprocess.run([FFMPEG, '-hide_banner', '-i', path, '-af', 'silencedetect=noise=-40dB:d=1.5', '-f', 'null', '-'], capture_output=True)
        open(cache, 'w').write(r.stderr.decode('utf-8', 'replace'))
    txt = open(cache).read()
    dur = re.search(r'Duration: (\d+):(\d+):([\d.]+)', txt)
    dur = int(dur[1]) * 3600 + int(dur[2]) * 60 + float(dur[3])
    out = [(float(e) - float(d), float(e)) for e, d in re.findall(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)', txt)]
    return out, dur

def cues(vol, lv, groups, warn):
    res = {}
    for g in groups:
        m = g['m']
        sil, dur = silences(os.path.join(ROOT, 'papers', vol, f'{lv}Q{m}.mp3'))
        labels = [x[0] for x in g['items']]
        n = len(labels)
        long = [s for s in sil if s[1] - s[0] >= LONG]
        ans = long if len(long) == n else [s for s in long if s[1] - s[0] < 16]    # 問題2 每题前还有 20 秒看选项的时间
        if len(ans) != n:
            warn(f'录音 問題{m}: 作答静音 {len(ans)} 段，应有 {n} 题（{", ".join(f"{a:.0f}-{b:.0f}" for a, b in long)}）')
            continue
        # 第 1 题的起点：先跳过第 1 题里面那几段 ≥2.9 秒的停顿（看选项、念选项前后；段数照第 2 题），
        # 再往前找「停 3 秒 · 一句短话 · 停 3 秒」（「では、始めます」「1番」），从那句短话开始；找不到就取跳过后的最后一段停顿
        inner = lambda a, b: sum(1 for s in sil if a < s[0] and s[1] < b and s[1] - s[0] >= 2.9)
        c = inner(ans[0][1] + .1, ans[1][0] - .1) if n > 1 else 0
        before = [s for s in sil if s[1] <= ans[0][0] - .1 and s[1] - s[0] >= 2.9]
        before = before[:len(before) - c]
        if not before:
            warn(f'录音 問題{m}: 找不到第 1 题的起点'); continue
        i = len(before) - 1
        pair = next((j for j in range(len(before) - 1, 0, -1) if before[j][0] - before[j - 1][1] < 2.5), None)
        if pair is not None: i = pair - 1
        starts = [before[i][1]] + [s[1] for s in ans[:-1]]
        lens = [ans[k][0] - starts[k] for k in range(n)]
        med = sorted(lens)[n // 2]
        if not .6 * med < lens[0] < 1.5 * med:
            warn(f'录音 問題{m}: 第 1 题长 {lens[0]:.0f} 秒，其他题中位 {med:.0f} 秒，起点可能不对')
        seen = {}
        for lb, t in zip(labels, starts):
            k = lb.split('-')[0]
            seen.setdefault(k, round(max(0, t - .4), 1))                        # 3-2 跟 3-1 一样从这题开头放
            res[f'listen:{m}:{lb}'] = seen[k]
    return res
