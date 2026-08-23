# deploy.ps1

Write-Host "Loading environment variables from .env..."
if (Test-Path .env) {
    foreach ($line in Get-Content .env) {
        if ($line -match '^\s*([^#]+?)\s*=\s*(.*?)\s*$') {
            $name = $matches[1]
            $value = $matches[2]
            Set-Item -Path Env:\$name -Value $value
        }
    }
    Write-Host ".env loaded successfully."
}

Write-Host "Starting build..."
& "C:\Program Files\Amazon\AWSSAMCLI\bin\sam.cmd" build

if ($LASTEXITCODE -eq 0) {
    Write-Host "Starting deployment..."
    & "C:\Program Files\Amazon\AWSSAMCLI\bin\sam.cmd" deploy --stack-name daily-github-explorer --resolve-s3 --capabilities CAPABILITY_IAM --region us-east-1
} else {
    Write-Host "Build failed!"
}
