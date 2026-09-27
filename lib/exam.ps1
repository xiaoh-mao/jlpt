# JLPT 做题 —— 本地服务里 JLPT 自己的部分，由 lib\server.ps1（内核）dot-source 进来。
$Title = 'JLPT 做题'     # 必须和 app\exam.js 的 EXAM.name 一致（那是窗口标题），AppActivate 靠它找窗口
$Ports = 8830..8849      # 默认端口段（TOPIK 做题用 8860–8879，错开）；调试实例用 8850

# papers\自备\<名字>\ 下的文件清单 + test.json（答案），给「导入自备试卷」用
function Get-CustomList {
  $dir = Join-Path $script:PaperDir '自备'
  $list = New-Object System.Collections.ArrayList
  if (Test-Path -LiteralPath $dir) {
    foreach ($d in Get-ChildItem -LiteralPath $dir -Directory) {
      $files = @(Get-ChildItem -LiteralPath $d.FullName -File | Where-Object { $_.Extension -match '^\.(pdf|mp3|m4a|wav)$' } | ForEach-Object { $_.Name })
      $test = $null
      $tj = Join-Path $d.FullName 'test.json'
      if (Test-Path -LiteralPath $tj) { $test = [IO.File]::ReadAllText($tj, $utf8) }
      [void]$list.Add(@{ name = $d.Name; files = $files; test = $test })
    }
  }
  return $list
}

# 内核没有的 /api/ 路由：处理了就返回 $true（别的输出都要吞掉）
function Invoke-ExamRoute($Ctx, [string]$Path) {
  $req = $Ctx.Request
  if ($Path -eq '/api/custom') {
    if ($req.HttpMethod -eq 'POST') {
      $name = [Uri]::UnescapeDataString([string]$req.QueryString['name'])
      $dir = Get-SafePath (Join-Path $script:PaperDir '自备') $name
      if (-not $name -or -not $dir -or -not (Test-Path -LiteralPath $dir -PathType Container)) { Send-Text $Ctx '{"ok":false,"error":"no such folder"}' -Code 400; return $true }
      [IO.File]::WriteAllText((Join-Path $dir 'test.json'), (Read-Body $Ctx), $utf8)
      Send-Text $Ctx '{"ok":true}'
    } else {
      Send-Text $Ctx (ConvertTo-Json -InputObject @(Get-CustomList) -Depth 5 -Compress)
    }
    return $true
  }
  if ($Path -eq '/api/open-folder') {
    # 只开 papers\自备，给「导入」对话框的按钮用
    $dir = Join-Path $script:PaperDir '自备'
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Start-Process explorer.exe -ArgumentList "`"$dir`""
    Send-Text $Ctx '{"ok":true}'
    return $true
  }
  return $false
}
