@ECHO OFF
REM  QBFC Project Options Begin
REM HasVersionInfo: Yes
REM Companyname: 
REM Productname: 
REM Filedescription: 
REM Copyrights: 
REM Trademarks: 
REM Originalname: 
REM Comments: 
REM Productversion:  0. 0. 0. 0
REM Fileversion:  0. 0. 0. 0
REM Internalname: 
REM ExeType: console
REM Architecture: x64
REM Appicon: ..\logo_hada.ico
REM AdministratorManifest: No
REM  QBFC Project Options End
@ECHO ON
@echo off
TITLE S.D.C.P. - SISTEMA DE DIAGNOSTICO DE CARIES PEDIATRICAS
COLOR 0A

echo ========================================================
echo      INICIANDO SISTEMA S.D.C.P. (Dental Hada)
echo ========================================================
echo.
echo [1/3] Ubicando archivos del sistema...
:: Moverse a la carpeta donde esta este archivo
cd /d "%~dp0"

echo [2/3] Activando Inteligencia Artificial...
echo.
echo --------------------------------------------------------
echo  IMPORTANTE: NO CIERRES ESTA VENTANA NEGRA.
echo  El navegador se abrira automaticamente en unos segundos.
echo --------------------------------------------------------
echo.

:: INTENTO 1: Configuracion PC NUEVA (Forzando Python 3.10)
py -3.10 -m streamlit run app.py

:: Si el anterior falla, salta al INTENTO 2 (Tu PC ORIGINAL)
if %errorlevel% neq 0 (
    echo.
    echo [Aviso] Configuracion 3.10 no detectada. Probando estandar...
    python -m streamlit run app.py
)

pause

