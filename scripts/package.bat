@echo off
REM Build Lambda package from dependencies folder using Python 3.12 wheels (Lambda runtime).
REM Run from project root. Output: lambda.zip

set "ROOT=%~dp0.."
cd /d "%ROOT%"

echo Deleting package directory...
if exist package del package
if exist dependencies del dependencies
if exist lambda.zip del lambda.zip

echo Installing dependencies for Lambda (manylinux, Python 3.14)...
pip install -r requirements.txt --platform manylinux2014_x86_64 --target dependencies --only-binary=:all: --python-version 3.14
if errorlevel 1 exit /b 1

echo Copying main.py into dependencies...
powershell -NoProfile -Command "Copy-Item -Force -Recurse -Verbose ./app -Destination dependencies"

copy /Y main.py dependencies\

echo Creating lambda.zip from dependencies...
powershell -NoProfile -Command "Compress-Archive -Path dependencies\* -DestinationPath lambda.zip -Force"

@REM echo Done. Upload lambda.zip (Lambda runtime Python 3.14).

echo Updating function code...
aws lambda update-function-code --function-name demo-fast-api-function --zip-file fileb://lambda.zip

echo Done.