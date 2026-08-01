# Requires elevation. Two things a normal user cannot change, and both of them
# cut the remote session:
#   1) closing the lid still suspends the laptop — the setting is HIDDEN by
#      default on this machine, so it must be unhidden before it can be set.
#   2) the Realtek Wi-Fi "Leisure Power Save" idles the radio; on Auto the link
#      can stall while nobody is typing, which is exactly when you connect.
# Everything here is reversible; the original values are printed first.

$ErrorActionPreference = 'Continue'
Write-Host "== BEFORE ==" -ForegroundColor Cyan
$g = ((powercfg /getactivescheme) -replace '.*GUID: ([a-f0-9-]+).*', '$1').Trim()
$BTN = '4f971e89-eebd-4455-a8de-9e59040e7347'
$LID = '5ca83367-6e45-459f-a27b-476b1d01c936'
powercfg /query $g $BTN $LID 2>&1 | Select-String 'AC Power Setting|not' | ForEach-Object { "  lid: $_" }
Get-NetAdapterAdvancedProperty -Name 'Wi-Fi' -RegistryKeyword 'LpsEn' -ErrorAction SilentlyContinue |
  ForEach-Object { "  wifi power save: $($_.DisplayValue)" }

Write-Host "`n== APPLY ==" -ForegroundColor Cyan
# 1) reveal the lid setting, then: on AC, closing the lid does nothing
powercfg /attributes $BTN $LID -ATTRIB_HIDE
powercfg /setacvalueindex $g $BTN $LID 0          # 0 = Do nothing
powercfg /setdcvalueindex $g $BTN $LID 1          # on battery: sleep (unchanged intent)
powercfg /setactive $g
Write-Host "  lid action on AC -> Do nothing"

# 2) keep the radio awake
Set-NetAdapterAdvancedProperty -Name 'Wi-Fi' -RegistryKeyword 'LpsEn' -DisplayValue 'Low' -NoRestart -ErrorAction SilentlyContinue
Write-Host "  wifi Leisure Power Save -> Low"

# 3) Windows must not power the NIC down to save energy
try {
  Set-NetAdapterPowerManagement -Name 'Wi-Fi' -AllowComputerToTurnOffDevice Disabled -ErrorAction Stop
  Write-Host "  'allow the computer to turn off this device' -> off"
} catch {
  # some Realtek drivers expose it only through the PnP device node
  $pnp = Get-PnpDevice -Class Net -ErrorAction SilentlyContinue |
         Where-Object { $_.FriendlyName -like '*8852*' -or $_.FriendlyName -like '*WiFi*' }
  foreach ($d in $pnp) {
    $k = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($d.InstanceId)\Device Parameters"
    if (Test-Path $k) { New-ItemProperty -Path $k -Name 'PnPCapabilities' -Value 24 -PropertyType DWord -Force | Out-Null }
  }
  Write-Host "  NIC power-down disabled via PnPCapabilities=24"
}

Write-Host "`n== AFTER ==" -ForegroundColor Green
powercfg /query $g $BTN $LID 2>&1 | Select-String 'AC Power Setting' | ForEach-Object { "  lid: $_" }
Get-NetAdapterAdvancedProperty -Name 'Wi-Fi' -RegistryKeyword 'LpsEn' -ErrorAction SilentlyContinue |
  ForEach-Object { "  wifi power save: $($_.DisplayValue)" }
foreach ($s in @(@('SUB_SLEEP', 'STANDBYIDLE', 'sleep'), @('SUB_DISK', 'DISKIDLE', 'disk'))) {
  $o = powercfg /query $g $s[0] $s[1] 2>$null
  $l = $o | Select-String 'Current AC Power Setting Index'
  if ($l) { "  $($s[2]) on AC = $([Convert]::ToInt32(($l.ToString() -replace '.*:\s*',''),16))" }
}
Write-Host "`nDone. Close this window." -ForegroundColor Green
Start-Sleep -Seconds 25
