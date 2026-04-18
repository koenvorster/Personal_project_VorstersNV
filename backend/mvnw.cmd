@REM Maven Wrapper script for Windows
@REM Licensed to the Apache Software Foundation (ASF)

@echo off
setlocal

set MAVEN_PROJECTBASEDIR=%~dp0
set MAVEN_WRAPPER_PROPERTIES=%MAVEN_PROJECTBASEDIR%.mvn\wrapper\maven-wrapper.properties

for /f "tokens=2 delims==" %%a in ('findstr "distributionUrl" "%MAVEN_WRAPPER_PROPERTIES%"') do set DOWNLOAD_URL=%%a
for %%F in ("%DOWNLOAD_URL%") do set DIST_FILENAME=%%~nxF
set DIST_FOLDER=%DIST_FILENAME:-bin.zip=%

if not defined MAVEN_USER_HOME set MAVEN_USER_HOME=%USERPROFILE%\.m2
set MAVEN_DISTS=%MAVEN_USER_HOME%\wrapper\dists\%DIST_FILENAME:.zip=%
set MAVEN_EXEC=%MAVEN_DISTS%\%DIST_FOLDER%\bin\mvn.cmd

if not exist "%MAVEN_EXEC%" (
    mkdir "%MAVEN_DISTS%" 2>nul
    echo Downloading Maven from %DOWNLOAD_URL%
    powershell -Command "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%MAVEN_DISTS%\%DIST_FILENAME%'"
    powershell -Command "Expand-Archive -Path '%MAVEN_DISTS%\%DIST_FILENAME%' -DestinationPath '%MAVEN_DISTS%' -Force"
    del "%MAVEN_DISTS%\%DIST_FILENAME%"
)

"%MAVEN_EXEC%" %*
