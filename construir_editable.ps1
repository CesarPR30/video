# Construye Demo_Factoring_Editable.prproj de punta a punta. No necesita a Claude.
# Uso, con Premiere CERRADO:  powershell -ExecutionPolicy Bypass -File construir_editable.ps1
#   -SoloArmar   no vuelve a grabar el dashboard; usa clips_editable tal como estan
param([switch]$SoloArmar)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$exe = "C:\Program Files\Adobe\Adobe Premiere Pro 2025\Adobe Premiere Pro.exe"
$prj = Join-Path $PSScriptRoot "Demo_Factoring_Editable.prproj"

function Esperar-Log($archivo, $seg) {
    $t = 0
    do { Start-Sleep 3; $t += 3; $l = Get-Content $archivo -Encoding UTF8 -ErrorAction SilentlyContinue | Out-String } until (($l -match 'FIN') -or $t -ge $seg)
    if ($l -notmatch 'FIN') { throw "Premiere no termino en $seg s: revisa $archivo" }
    if ($l -match 'ERROR') { Write-Host "Avisos de Premiere:"; ($l -split "`n" | Where-Object { $_ -match 'ERROR' }) | Write-Host }
    return $l
}
function Cerrar-Premiere {
    $p = Get-Process "Adobe Premiere Pro" -ErrorAction SilentlyContinue
    if (-not $p) { return }
    $t = 0                                                # el .jsx ya guardo y pidio salir
    do { Start-Sleep 2; $t += 2 } until (-not (Get-Process "Adobe Premiere Pro" -ErrorAction SilentlyContinue) -or $t -ge 40)
    if (Get-Process "Adobe Premiere Pro" -ErrorAction SilentlyContinue) { throw "Premiere no se cerro: cierralo a mano, corre 'python parchar_textos.py' y abre el proyecto." }
}

if (Get-Process "Adobe Premiere Pro" -ErrorAction SilentlyContinue) { throw "Cierra Premiere antes de empezar y guarda tu trabajo." }

$env:VIDEO_MODO = "editable"
if (-not $SoloArmar) { python tomas.py; if ($LASTEXITCODE) { throw "Fallo la grabacion" } }
python armar_editable.py; if ($LASTEXITCODE) { throw "Fallo el armado" }

if (Test-Path $prj) {
    $resp = "Demo_Factoring_Editable.respaldo_{0}.prproj" -f (Get-Date -Format "yyyyMMdd_HHmmss")
    Rename-Item $prj $resp
    Write-Host "Proyecto anterior guardado como $resp"
}
Remove-Item crear_editable.log, verificar.log -ErrorAction SilentlyContinue

Write-Host "1/3 Creando el proyecto en Premiere..."
Start-Process $exe -ArgumentList '/C', 'es.processFile', "`"$(Join-Path $PSScriptRoot 'crear_editable.jsx')`""
Esperar-Log "crear_editable.log" 240 | Write-Host
Cerrar-Premiere

Write-Host "2/3 Escribiendo los titulos..."
python parchar_textos.py; if ($LASTEXITCODE) { throw "Fallo la escritura de titulos" }

Write-Host "3/3 Abriendo el proyecto y exportando cuadros de control..."
New-Item -ItemType Directory -Force verificacion | Out-Null
Start-Process $exe -ArgumentList '/C', 'es.processFile', "`"$(Join-Path $PSScriptRoot 'verificar.jsx')`""
Esperar-Log "verificar.log" 240 | Write-Host
Write-Host "Listo: Demo_Factoring_Editable.prproj esta abierto en Premiere. Revisa la carpeta verificacion."
