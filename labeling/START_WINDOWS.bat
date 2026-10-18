@echo off
rem Start de labelapp op Windows. Dubbelklik op dit bestand (zie README.md).
rem Eerst 'py' (de Python-starter van python.org), anders 'python'. Met --version wordt eerst gekeken
rem of Python echt werkt: de snelkoppeling 'python' van de Microsoft Store zonder Python geeft een fout.
if not exist "%~dp0app.py" (
    echo De map is nog niet uitgepakt, of app.py ontbreekt.
    echo Pak het ZIP-bestand eerst uit: rechtsklik op het ZIP-bestand en kies Alles uitpakken.
    echo Start daarna START_WINDOWS.bat in de uitgepakte map labeling. Zie README.md, stap 2.
    goto end
)
pushd "%~dp0"
echo Python wordt gezocht. De eerste keer kan dit even duren ...
py -3 --version >nul 2>nul
if %errorlevel%==0 (
    py -3 app.py
    goto done
)
python --version >nul 2>nul
if %errorlevel%==0 (
    python app.py
    goto done
)
echo Python 3 is niet gevonden op deze computer.
echo Installeer Python eerst; zie README.md, stap 1.
:done
popd
:end
echo.
pause
