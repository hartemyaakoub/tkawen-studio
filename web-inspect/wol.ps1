# Wake this laptop (DESKTOP-CTJONVF) from another machine on the SAME Wi-Fi.
#
# ASCII only on purpose: Windows PowerShell 5.1 reads .ps1 as ANSI unless the
# file carries a UTF-8 BOM, so a stray em-dash breaks the parser.
#
# What it can and cannot do:
#   [yes] wakes it from SLEEP / HIBERNATE (the Wi-Fi card stays powered)
#   [no ] does NOT work after a full shutdown: at S5 the Wi-Fi radio has no power
#   [no ] does NOT work from outside the house unless the router forwards UDP 9
#         to the broadcast address (most consumer routers refuse)
#
# Usage: powershell -ExecutionPolicy Bypass -File wol.ps1
param(
  [string]$Mac       = '70-08-94-91-0B-AB',
  [string]$Broadcast = '192.168.100.255',
  [int]   $Port      = 9,
  [int]   $Repeat    = 3
)

$clean = ($Mac -replace '[:-]', '').Trim()
if ($clean.Length -ne 12) { throw "MAC must be 12 hex digits, got '$Mac'" }
$macBytes = for ($i = 0; $i -lt 12; $i += 2) { [Convert]::ToByte($clean.Substring($i, 2), 16) }

# magic packet = 6 x 0xFF then the MAC repeated 16 times
$packet = [byte[]]@(0xFF) * 6
for ($i = 0; $i -lt 16; $i++) { $packet += $macBytes }

$udp = New-Object System.Net.Sockets.UdpClient
$udp.EnableBroadcast = $true
try {
  for ($i = 1; $i -le $Repeat; $i++) {
    $sent = $udp.Send($packet, $packet.Length, $Broadcast, $Port)
    Write-Host ("sent " + $i + "/" + $Repeat + " - " + $sent + " bytes to " + $Broadcast + ":" + $Port + " for " + $Mac)
    Start-Sleep -Milliseconds 400
  }
} finally { $udp.Close() }

Write-Host ""
Write-Host "If the laptop was asleep it should be back in about 10 seconds." -ForegroundColor Green
Write-Host "If it was fully powered off, nothing happens - that is the hardware, not this script." -ForegroundColor Yellow
