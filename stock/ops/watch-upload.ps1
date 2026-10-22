$ErrorActionPreference='Continue'
$Base='E:\HealingMart-Stock'
$Log=Join-Path $Base 'LOGS\uploader.log'
Add-Content -LiteralPath $Log -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+'  Watcher bridge started.') -Encoding UTF8
python E:\HealingMart-Stock\stock-auto.py --watch
