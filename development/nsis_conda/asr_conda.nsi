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

Name "ASR Setup"
OutFile "ASR_Setup.exe"
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
  !insertmacro InstallOrUpdateApp "asr_setup" "-c rgerum -c conda-forge -c dlidstrom"
  ExecDos::exec /DETAILED '$ENVS\_app_own_environment_asr_setup\Scripts\pip.exe install pyqt5' "" ""
  !insertmacro WriteUninstaller "ASRSetup"
SectionEnd

Section "Start Menu shortcut"
  Call SetRootEnv
  ; Here we don't use the CreateShortcut macro of conda_macros because we want a console that does not close when an exception occurs
  ; therefore we create a bat file and link to that
  Push $R1
  Push $R2
  StrCpy $R1 "$ENVS\_app_own_environment_asr_setup"
  
  FileOpen $0 "$R1\ASRSetup.bat" w
  IfErrors done
  FileWrite $0 "@echo off$\r$\n"
  FileWrite $0 '"$R1\Scripts\asr_setup.exe" -srcpath=%1$\r$\n'
  FileWrite $0 "IF %ERRORLEVEL% NEQ 0 pause$\r$\n"
  FileClose $0
  done:
  
  SetOutPath "$PROFILE"  # Shortcut working dir
  CreateShortcut "$SMPROGRAMS\ASRSetup.lnk" "$R1\ASRSetup.bat" "$R2" "$R1\Lib\site-packages\asr_setup\icons\ASRSetup.ico" 0 "" "" "Open ASR Setup"

  Pop $R2
  Pop $R1
  
  ; this would be the useage of the CreateShortcut macro
  ;!insertmacro CreateShortcut "ASR_Setup" \
  ;  "ASRSetup" "ASRSetup.bat" ""\
  ;  "..\..\ASRSetup\icons\ASRSetup.ico"
  ;  ;Lib\site-packages\ASR_Setup
SectionEnd

Section "File Assiciations";
  Call SetRootEnv

  DetailPrint "Linking file extensions ..."

  ExecDos::exec /DETAILED '$ENVS\_app_own_environment_asr_setup\Scripts\asr_setup.exe register' "" ""
  !insertmacro _FinishMessage "File extensions linked"
SectionEnd

Section "un.ASRSetup";
  Call un.SetRootEnv
  !insertmacro DeleteApp "ASRSetup"
  !insertmacro DeleteShortcut "ASRSetup"
SectionEnd
