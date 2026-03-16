; EchoScribe Inno Setup Script
; Packages the PyInstaller one-folder output under dist\main.

[Setup]
AppName=EchoScribe
AppVersion=1.1
DefaultDirName={autopf}\EchoScribe
DefaultGroupName=EchoScribe
UninstallDisplayIcon={app}\main.exe
OutputBaseFilename=EchoScribe-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "dist\main\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\EchoScribe"; Filename: "{app}\main.exe"
Name: "{commondesktop}\EchoScribe"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\main.exe"; Description: "Launch EchoScribe"; Flags: nowait postinstall skipifsilent
