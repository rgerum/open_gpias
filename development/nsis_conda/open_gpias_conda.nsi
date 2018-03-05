# conda execute
# env:
#  - nsis 3.*
#  - inetc
#  - conda_macros
# channels:
#  - nsis
# run_with: makensis

SetCompressor lzma

!include conda.nsh
;!include inetc.nsh
!include MUI2.nsh

Name "Open GPIAS"
OutFile "Open_GPIAS.exe"
RequestExecutionLevel user

; Modern UI installer stuff 
!include "MUI2.nsh"

;; ASRSetup
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp" ; optional
!define MUI_WELCOMEFINISHPAGE_BITMAP "panel.bmp"
;; end ASRSetup

; UI pages
!insertmacro MUI_PAGE_WELCOME
!define MUI_COMPONENTSPAGE_NODESC
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
# ... other required NSIS stuff

Section "Conda package manager"
  !insertmacro InstallOrUpdateConda
SectionEnd

Section "ASRSetup Application files"
  !insertmacro InstallOrUpdateApp "open_gpias" "-c rgerum -c conda-forge -c dlidstrom"
  ExecDos::exec /DETAILED '$ENVS\_app_own_environment_open_gpias\Scripts\pip.exe install pyqt5' "" ""
  !insertmacro WriteUninstaller "OpenGPIAS"
SectionEnd

Section "Start Menu shortcut"
  Call SetRootEnv
  ; Here we don't use the CreateShortcut macro of conda_macros because we want a console that does not close when an exception occurs
  ; therefore we create a bat file and link to that
  Push $R1
  Push $R2
  StrCpy $R1 "$ENVS\_app_own_environment_open_gpias"
  
  FileOpen $0 "$R1\OpenGPIAS.bat" w
  IfErrors done
  FileWrite $0 "@echo off$\r$\n"
  FileWrite $0 '"$R1\Scripts\Open_GPIAS.exe" -srcpath=%1$\r$\n'
  FileWrite $0 "IF %ERRORLEVEL% NEQ 0 pause$\r$\n"
  FileClose $0
  done:
  
  SetOutPath "$PROFILE"  # Shortcut working dir
  CreateShortcut "$SMPROGRAMS\OpenGPIAS.lnk" "$R1\ASRSetup.bat" "$R2" "$R1\Lib\site-packages\open_gpias\icon.ico" 0 "" "" "Start Open GPIAS"

  Pop $R2
  Pop $R1
  
  ; this would be the useage of the CreateShortcut macro
  ;!insertmacro CreateShortcut "Open_GPIAS" \
  ;  "ASRSetup" "ASRSetup.bat" ""\
  ;  "..\..\ASRSetup\icons\ASRSetup.ico"
  ;  ;Lib\site-packages\Open_GPIAS
SectionEnd

Section "File Assiciations";
  Call SetRootEnv

  DetailPrint "Linking file extensions ..."

  ExecDos::exec /DETAILED '$ENVS\_app_own_environment_open_gpias\Scripts\open_gpias.exe register' "" ""
  !insertmacro _FinishMessage "File extensions linked"
SectionEnd

Section "un.OpenGPIAS";
  Call un.SetRootEnv
  !insertmacro DeleteApp "OpenGPIAS"
  !insertmacro DeleteShortcut "OpenGPIAS"
SectionEnd
