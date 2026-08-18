; Creoveya Windows Installer
; Compiled by Inno Setup (ISCC.exe) — produces CreoveyaSetup.exe, which
; installs the app properly with Start Menu + Desktop shortcuts, an
; uninstaller, and no admin rights required.

[Setup]
AppName=Creoveya
AppVersion=1.0
AppPublisher=Creoveya
DefaultDirName={autopf}\Creoveya
DefaultGroupName=Creoveya
OutputDir=Output
OutputBaseFilename=CreoveyaSetup
SetupIconFile=assets\icon.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\Creoveya.exe

[Files]
; Everything PyInstaller's --onedir build produces, bundled into the install folder
Source: "dist\Creoveya\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Creoveya"; Filename: "{app}\Creoveya.exe"; IconFilename: "{app}\assets\icon.ico"
Name: "{autodesktop}\Creoveya"; Filename: "{app}\Creoveya.exe"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Uninstall Creoveya"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\Creoveya.exe"; Description: "Launch Creoveya"; Flags: nowait postinstall skipifsilent
