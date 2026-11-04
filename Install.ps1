param([string]$Python)
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$launcher=@()
if(!$Python){
  $bundled=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if(Test-Path -LiteralPath $bundled){$Python=$bundled}
  elseif(Get-Command py -ErrorAction SilentlyContinue){$Python=(Get-Command py).Source;$launcher=@('-3.12')}
  elseif(Get-Command python -ErrorAction SilentlyContinue){$Python=(Get-Command python).Source}
  else{throw 'Install Python 3.12 or pass -Python with its full path.'}
}
& $Python @launcher -m venv (Join-Path $root '.venv')
if($LASTEXITCODE-ne 0){throw 'Could not create Python environment.'}
$runtime=Join-Path $root '.venv\Scripts\python.exe'
& $runtime -m pip install --index-url https://pypi.org/simple -r (Join-Path $root 'requirements-lock.txt')
if($LASTEXITCODE-ne 0){throw 'Dependency installation failed.'}
$config=@{mcpServers=@{'bili-study'=@{command=$runtime;args=@((Join-Path $root 'plugin\server.py'));env=@{PYTHONUTF8='1';PYTHONUNBUFFERED='1'}}}}
[IO.File]::WriteAllText((Join-Path $root 'plugin\.mcp.json'),($config|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$cli=Get-Command codex -ErrorAction SilentlyContinue
if($cli){$codexPath=$cli.Source}else{
  $binRoot=Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin'
  $found=Get-ChildItem -LiteralPath $binRoot -Filter codex.exe -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if(!$found){throw 'Codex CLI not found. Install the Codex desktop app first.'}
  $codexPath=$found.FullName
}
& $codexPath plugin marketplace add $root --json
if($LASTEXITCODE-ne 0){throw 'Could not register marketplace.'}
& $codexPath plugin add 'bili-study@bili-study-local' --json
if($LASTEXITCODE-ne 0){throw 'Could not install plugin.'}
Write-Output 'Installed. Reload your chat, then ask the Bili Study plugin to generate a QR login code.'
