$ErrorActionPreference = "Stop"

$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-25.0.4.101-hotspot"
$env:Path = "$env:JAVA_HOME\bin;" + $env:Path

$sdk = "C:\Users\Rubel\AppData\Local\Android\Sdk"
$buildTools = "$sdk\build-tools\34.0.0"
$platform = "$sdk\platforms\android-34"

$aapt = "$buildTools\aapt.exe"
$zipalign = "$buildTools\zipalign.exe"
$androidJar = "$platform\android.jar"
$java = "$env:JAVA_HOME\bin\java.exe"
$javac = "$env:JAVA_HOME\bin\javac.exe"
$jar = "$env:JAVA_HOME\bin\jar.exe"
$d8Jar = "$buildTools\lib\d8.jar"
$apksignerJar = "$buildTools\lib\apksigner.jar"

Set-Location $PSScriptRoot

Write-Host ">>> Step 1: Compiling resources with aapt..."
& $aapt package -f -m -J src -M AndroidManifest.xml -S res -I $androidJar
if ($LASTEXITCODE -ne 0) { throw "aapt resource generation failed!" }

Write-Host ">>> Step 2: Compiling Java sources..."
if (Test-Path "bin\com") { Remove-Item "bin\com" -Recurse -Force }
New-Item -ItemType Directory -Path "bin" -Force | Out-Null
New-Item -ItemType Directory -Path "bin\dex" -Force | Out-Null

$javaFiles = Get-ChildItem -Path "src\com\vareon\gateway\*.java" | ForEach-Object { $_.FullName }
& $javac --release 8 -XDstringConcat=inline -d "bin" -cp "$androidJar" $javaFiles
if ($LASTEXITCODE -ne 0) { throw "javac compilation failed!" }

Write-Host ">>> Step 3: Generating DEX with d8..."
& $jar cf bin\gateway.jar -C bin com
& $java -cp "$d8Jar" com.android.tools.r8.D8 --min-api 21 --lib "$androidJar" --output "bin\dex" bin\gateway.jar
if ($LASTEXITCODE -ne 0) { throw "d8 failed!" }

Write-Host ">>> Step 4: Packaging APK..."
if (Test-Path "unaligned.apk") { Remove-Item "unaligned.apk" -Force }
& $aapt package -f -M AndroidManifest.xml -S res -I $androidJar -F unaligned.apk bin\dex
if ($LASTEXITCODE -ne 0) { throw "aapt package failed!" }

Write-Host ">>> Step 5: Aligning APK with zipalign..."
if (Test-Path "PP_Gateway_aligned.apk") { Remove-Item "PP_Gateway_aligned.apk" -Force }
& $zipalign -f -p 4 unaligned.apk PP_Gateway_aligned.apk
if ($LASTEXITCODE -ne 0) { throw "zipalign failed!" }

Write-Host ">>> Step 6: Signing APK with official release certificate..."
if (Test-Path "PP_Gateway.apk") { Remove-Item "PP_Gateway.apk" -Force }
& $java -jar "$apksignerJar" sign --ks release.keystore --ks-pass pass:ppserver123 --ks-key-alias ppserver --key-pass pass:ppserver123 --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true --v4-signing-enabled false --out PP_Gateway.apk PP_Gateway_aligned.apk
if ($LASTEXITCODE -ne 0) { throw "apksigner failed!" }

Write-Host ">>> Step 7: Verifying signature..."
& $java -jar "$apksignerJar" verify --verbose PP_Gateway.apk

# Copy to root and distribution folders
Copy-Item "PP_Gateway.apk" "..\..\PP_Gateway.apk" -Force
Copy-Item "PP_Gateway.apk" "..\PP_Gateway.apk" -Force

Write-Host ">>> SUCCESS: PP_Gateway.apk successfully built and signed!" -ForegroundColor Green
