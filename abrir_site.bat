@echo off
echo Iniciando o servidor do Gordin Lanches...
start /b python app.py
timeout /t 5 /nobreak > nul
echo Abrindo o site no navegador...
start http://127.0.0.1:5000
echo Pronto! O site deve abrir em alguns segundos.
pause
