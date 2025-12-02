@echo off
echo 🛠️ Собира .exe с помощью PyInstaller...
pyinstaller ^
    --name "EasyEng" ^
    --windowed ^
    --onefile ^
    --icon=app.ico ^
    --add-data="app;app" ^
    --add-data="app.ico;." ^
    --clean ^
    main.py

echo Файл находится в папке 'dist'
pause
