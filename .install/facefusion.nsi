!include MUI2.nsh
!include nsDialogs.nsh
!include LogicLib.nsh

RequestExecutionLevel admin
ManifestDPIAware true

Name 'FaceFusion 2.6.1'
OutFile 'FaceFusion_2.6.1.exe'

!define MUI_ICON 'facefusion.ico'

!insertmacro MUI_PAGE_DIRECTORY
Page custom InstallPage PostInstallPage
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE English

Var UseDefault
Var UseCuda
Var UseDirectMl
Var UseOpenVino

Function .onInit
	StrCpy $INSTDIR 'C:\FaceFusion'
FunctionEnd

Function InstallPage
	nsDialogs::Create 1018
	!insertmacro MUI_HEADER_TEXT 'Choose Your Accelerator' 'Choose your accelerator based on the graphics card.'

	${NSD_CreateRadioButton} 0 40u 100% 10u 'Default'
	Pop $UseDefault

	${NSD_CreateRadioButton} 0 55u 100% 10u 'CUDA (NVIDIA)'
	Pop $UseCuda

	${NSD_CreateRadioButton} 0 70u 100% 10u 'DirectML (AMD, Intel, NVIDIA)'
	Pop $UseDirectMl

	${NSD_CreateRadioButton} 0 85u 100% 10u 'OpenVINO (Intel)'
	Pop $UseOpenVino

	${NSD_Check} $UseDefault

	nsDialogs::Show
FunctionEnd

Function PostInstallPage
	${NSD_GetState} $UseDefault $UseDefault
	${NSD_GetState} $UseCuda $UseCuda
	${NSD_GetState} $UseDirectMl $UseDirectMl
	${NSD_GetState} $UseOpenVino $UseOpenVino
FunctionEnd

Function Destroy
	${If} ${Silent}
		Quit
	${Else}
		Abort
	${EndIf}
FunctionEnd

Section 'Prepare Your Platform'
	DetailPrint 'Install GIT'
	inetc::get 'https://github.com/git-for-windows/git/releases/download/v2.45.2.windows.1/Git-2.45.2-64-bit.exe' '$TEMP\Git.exe'
	ExecWait '$TEMP\Git.exe /CURRENTUSER /VERYSILENT /DIR=$LOCALAPPDATA\Programs\Git' $0
	Delete '$TEMP\Git.exe'

	${If} $0 > 0
		DetailPrint 'Git installation aborted with error code $0'
		Call Destroy
	${EndIf}

	DetailPrint 'Uninstall Conda'
	ExecWait '$LOCALAPPDATA\Programs\Miniconda3\Uninstall-Miniconda3.exe /S _?=$LOCALAPPDATA\Programs\Miniconda3'
	RMDir /r '$LOCALAPPDATA\Programs\Miniconda3'

	DetailPrint 'Install Conda'
	inetc::get 'https://repo.anaconda.com/miniconda/Miniconda3-py310_24.3.0-0-Windows-x86_64.exe' '$TEMP\Miniconda3.exe'
	ExecWait '$TEMP\Miniconda3.exe /InstallationType=JustMe /AddToPath=1 /S /D=$LOCALAPPDATA\Programs\Miniconda3' $1
	Delete '$TEMP\Miniconda3.exe'

	${If} $1 > 0
		DetailPrint 'Conda installation aborted with error code $1'
		Call Destroy
	${EndIf}
SectionEnd

Section 'Download Your Copy'
	SetOutPath $INSTDIR

	DetailPrint 'Download Your Copy'
	RMDir /r $INSTDIR
	nsExec::Exec '$LOCALAPPDATA\Programs\Git\cmd\git.exe clone https://github.com/facefusion/facefusion --branch 2.6.1 .'
SectionEnd

Section 'Setup Your Environment'
	DetailPrint 'Setup Your Environment'
	nsExec::Exec '$LOCALAPPDATA\Programs\Miniconda3\Scripts\conda.exe init --all'
	nsExec::Exec '$LOCALAPPDATA\Programs\Miniconda3\Scripts\conda.exe create --name facefusion python=3.10 --yes'
SectionEnd

Section 'Create Install Batch'
	SetOutPath $INSTDIR

	FileOpen $0 install-ffmpeg.bat w
	FileOpen $1 install-accelerator.bat w
	FileOpen $2 install-application.bat w

	FileWrite $0 '@echo off && conda activate facefusion && conda install conda-forge::ffmpeg=7.0.1 --yes'
	${If} $UseCuda == 1
		FileWrite $1 '@echo off && conda activate facefusion && conda install cudatoolkit=11.8 cudnn=8.9.2.26 conda-forge::gputil=1.4.0 conda-forge::zlib-wapi --yes'
		FileWrite $2 '@echo off && conda activate facefusion && python install.py --onnxruntime cuda-11.8'
	${ElseIf} $UseDirectMl == 1
		FileWrite $2 '@echo off && conda activate facefusion && python install.py --onnxruntime directml'
	${ElseIf} $UseOpenVino == 1
		FileWrite $1 '@echo off && conda activate facefusion && conda install conda-forge::openvino=2023.1.0 --yes'
		FileWrite $2 '@echo off && conda activate facefusion && python install.py --onnxruntime openvino'
	${Else}
		FileWrite $2 '@echo off && conda activate facefusion && python install.py --onnxruntime default'
	${EndIf}

	FileClose $0
	FileClose $1
	FileClose $2
SectionEnd

Section 'Install Your FFmpeg'
	SetOutPath $INSTDIR

	DetailPrint 'Install Your FFmpeg'
	nsExec::ExecToLog 'install-ffmpeg.bat'
SectionEnd

Section 'Install Your Accelerator'
	SetOutPath $INSTDIR

	DetailPrint 'Install Your Accelerator'
	nsExec::ExecToLog 'install-accelerator.bat'
SectionEnd

Section 'Install The Application'
	SetOutPath $INSTDIR

	DetailPrint 'Install The Application'
	nsExec::ExecToLog 'install-application.bat'
SectionEnd

Section 'Create Run Batch'
	SetOutPath $INSTDIR
	FileOpen $0 run.bat w
	FileWrite $0 '@echo off && conda activate facefusion && python run.py %*'
	FileClose $0
SectionEnd

Section 'Register The Application'
	DetailPrint 'Register The Application'

	CreateDirectory $SMPROGRAMS\FaceFusion
	CreateShortcut '$SMPROGRAMS\FaceFusion\FaceFusion.lnk' $INSTDIR\run.bat '--open-browser' $INSTDIR\.install\facefusion.ico
	CreateShortcut '$SMPROGRAMS\FaceFusion\FaceFusion Benchmark.lnk' $INSTDIR\run.bat '--ui-layouts benchmark --open-browser' $INSTDIR\.install\facefusion.ico
	CreateShortcut '$SMPROGRAMS\FaceFusion\FaceFusion Webcam.lnk' $INSTDIR\run.bat '--ui-layouts webcam --open-browser' $INSTDIR\.install\facefusion.ico

	CreateShortcut $DESKTOP\FaceFusion.lnk $INSTDIR\run.bat '--open-browser' $INSTDIR\.install\facefusion.ico

	WriteUninstaller $INSTDIR\Uninstall.exe

	WriteRegStr HKLM SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\FaceFusion DisplayName 'FaceFusion'
	WriteRegStr HKLM SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\FaceFusion DisplayVersion '2.6.0'
	WriteRegStr HKLM SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\FaceFusion Publisher 'Henry Ruhs'
	WriteRegStr HKLM SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\FaceFusion InstallLocation $INSTDIR
	WriteRegStr HKLM SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\FaceFusion UninstallString $INSTDIR\uninstall.exe
SectionEnd

Section 'Uninstall'
	nsExec::Exec '$LOCALAPPDATA\Programs\Miniconda3\Scripts\conda.exe env remove --name facefusion --yes'

	Delete $DESKTOP\FaceFusion.lnk
	RMDir /r $SMPROGRAMS\FaceFusion
	RMDir /r $INSTDIR

	DeleteRegKey HKLM SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\FaceFusion
SectionEnd
