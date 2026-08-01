# Large uploads go through curl: urllib buffers the whole body then times out
# mid-write on a slow home uplink. curl streams it and can retry.
param(
  [Parameter(Mandatory=$true)][string]$Method,   # sendVideo | sendDocument | sendPhoto
  [Parameter(Mandatory=$true)][string]$Field,    # video | document | photo
  [Parameter(Mandatory=$true)][string]$File,
  [string]$Caption = ""
)
$envFile = "C:\Users\YAAKOUB DEV\tkawen-remote-bot\bot.env"
$cfg = @{}
Get-Content $envFile -Encoding UTF8 | ForEach-Object {
  if ($_ -match '^\s*([^#=]+)=(.*)$') { $cfg[$matches[1].Trim()] = $matches[2].Trim().Trim('"').Trim("'") }
}
$url = "https://api.telegram.org/bot$($cfg['TKAWEN_BOT_TOKEN'])/$Method"
$capFile = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllText($capFile, $Caption, [System.Text.UTF8Encoding]::new($false))

$args = @(
  "-s", "--max-time", "2400", "--retry", "2", "--retry-delay", "10",
  "-F", "chat_id=$($cfg['TKAWEN_OWNER_CHAT_ID'])",
  "-F", "parse_mode=HTML",
  "-F", "caption=<$capFile",
  "-F", "$Field=@$File"
)
if ($Method -eq "sendVideo") { $args += @("-F", "supports_streaming=true") }
$mb = [math]::Round((Get-Item $File).Length / 1MB, 1)
"uploading $([System.IO.Path]::GetFileName($File)) ($mb MB) ..."
$resp = & curl.exe @args $url
Remove-Item $capFile -Force
if ($resp -match '"ok":true') { "ok: True" } else { "FAILED: $resp" }
