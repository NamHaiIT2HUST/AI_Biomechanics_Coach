# Download public datasets to data/external. Run from any directory.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts/download_datasets.ps1
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$externalDir = Join-Path $projectRoot 'data/external'
$metadataPath = Join-Path $externalDir 'ui_prmd/zenodo_metadata.json'
$records = @(
    @{ Name='Multi-View Fitness'; Path='multiview_fitness/exercise_wise.zip'; Url='https://data.mendeley.com/public-files/datasets/kgbb3yn47p/files/a31fa913-6f29-4c31-b1a6-414a718eebf4/file_downloaded'; Size=[long]3113452092; Algorithm='SHA256'; Hash='6d927246dbd2ed8a314b41201c94ebdcbd1b4abec0851d1ca39f82afda8a5eed' },
    @{ Name='CFRep'; Path='cfrep/cfrep-main.zip'; Url='https://codeload.github.com/lc-leonardo/CFRep/zip/refs/heads/main'; Size=$null; Algorithm=$null; Hash=$null }
)
New-Item -ItemType Directory -Force -Path (Split-Path $metadataPath) | Out-Null
if (-not (Test-Path -LiteralPath $metadataPath)) {
    Write-Host 'Downloading UI-PRMD metadata from Zenodo...'
    & curl.exe --fail --location --retry 3 --output $metadataPath 'https://zenodo.org/api/records/23104965'
    if ($LASTEXITCODE -ne 0) { throw 'Could not download UI-PRMD metadata.' }
}
$metadata = Get-Content -LiteralPath $metadataPath -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($item in $metadata.files) {
    if ($item.key -match '[\\/]' -or $item.key -in @('.', '..')) { throw 'Invalid filename in UI-PRMD metadata.' }
    $records += @{ Name="UI-PRMD / $($item.key)"; Path="ui_prmd/$($item.key)"; Url=$item.links.self; Size=[long]$item.size; Algorithm='MD5'; Hash=($item.checksum -replace '^md5:', '') }
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
foreach ($record in $records) {
    $path = Join-Path $externalDir $record.Path
    New-Item -ItemType Directory -Force -Path (Split-Path $path) | Out-Null
    Write-Host "`n=== $($record.Name) ==="
    $valid = $false
    if (Test-Path -LiteralPath $path) {
        $file = Get-Item -LiteralPath $path
        if ($null -ne $record.Size -and $file.Length -eq $record.Size) {
            Write-Host 'Checking existing file checksum...'
            $valid = (Get-FileHash -LiteralPath $path -Algorithm $record.Algorithm).Hash -eq $record.Hash
            if (-not $valid) { throw "Checksum mismatch: $path. Preserve and inspect the file before retrying." }
        } elseif ($null -ne $record.Size -and $file.Length -gt $record.Size) {
            throw "File is larger than expected: $path. Preserve and inspect it before retrying."
        } elseif ($null -eq $record.Size -and $file.Length -gt 0) {
            try {
                $zip = [System.IO.Compression.ZipFile]::OpenRead($path)
                try { if ($zip.Entries.Count -gt 0) { $valid = $true } } finally { $zip.Dispose() }
                if ($valid) { Write-Host 'Existing CFRep archive opens successfully (no upstream checksum available).' }
            } catch { $valid = $false }
        }
    }
    if (-not $valid) {
        Write-Host 'Downloading; resuming if supported...'
        & curl.exe --fail --location --retry 3 --continue-at - --output $path $record.Url
        $curlExit = $LASTEXITCODE
        if ($curlExit -eq 33 -and (Test-Path -LiteralPath $path)) {
            # Keep the partial file if the server cannot resume; never overwrite it.
            $backup = "$path.partial.$([guid]::NewGuid().ToString('N'))"
            Move-Item -LiteralPath $path -Destination $backup
            Write-Warning "Server cannot resume. Partial file preserved at: $backup"
            & curl.exe --fail --location --retry 3 --output $path $record.Url
            $curlExit = $LASTEXITCODE
        }
        if ($curlExit -ne 0) { throw "Download failed (curl exit $curlExit): $($record.Name). Run the script again to retry." }
        if ($null -ne $record.Size) {
            if ((Get-Item -LiteralPath $path).Length -ne $record.Size) { throw "Unexpected size: $path" }
            Write-Host 'Verifying checksum...'
            if ((Get-FileHash -LiteralPath $path -Algorithm $record.Algorithm).Hash -ne $record.Hash) { throw "Checksum mismatch: $path" }
        } else {
            $zip = [System.IO.Compression.ZipFile]::OpenRead($path)
            try { if ($zip.Entries.Count -eq 0) { throw "Empty archive: $path" } } finally { $zip.Dispose() }
            Write-Warning 'CFRep archive structure was checked, but no upstream checksum was available; check its data licence before use.'
        }
    }
    Write-Host "Ready: $path"
}
Write-Host "`nPublic dataset downloads complete. Fit3D requires an account and approval: https://fit3d.imar.ro/"
Write-Host 'Do not redistribute datasets without checking their licences. Data stays outside Git.'
