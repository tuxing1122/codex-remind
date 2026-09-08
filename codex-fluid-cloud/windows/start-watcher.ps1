param(
    [string]$Config,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$WatcherArguments
)

if (-not $PSBoundParameters.ContainsKey('Config')) {
    $localConfig = Join-Path $PSScriptRoot 'config.local.json'
    if (Test-Path -LiteralPath $localConfig) {
        $Config = $localConfig
    } else {
        $Config = Join-Path $PSScriptRoot 'config.json'
    }
}

$watcher = Join-Path $PSScriptRoot 'codex_watcher.py'
if (-not (Test-Path -LiteralPath $watcher)) {
    throw "Watcher not found: $watcher"
}

$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    & $launcher.Source -3 $watcher --config $Config @WatcherArguments
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand -and $pythonCommand.Source -notlike '*\WindowsApps\*') {
        $python = $pythonCommand.Source
    } else {
        $python = Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python*\python.exe') -File -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending |
            Select-Object -First 1 -ExpandProperty FullName
    }
    if (-not $python) {
        throw 'Python 3.10 or newer was not found.'
    }
    & $python $watcher --config $Config @WatcherArguments
}
exit $LASTEXITCODE
