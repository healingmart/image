$ErrorActionPreference='SilentlyContinue'
$me=$PID
Get-CimInstance Win32_Process | Where-Object {
  $_.ProcessId -ne $me -and (
    $_.CommandLine -like '*E:\HealingMart-Stock\watch-upload.ps1*' -or
    $_.CommandLine -like '*E:\HealingMart-Stock\stock-auto.py --watch*'
  )
} | ForEach-Object {
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
