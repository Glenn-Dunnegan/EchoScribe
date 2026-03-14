; EchoScribe Inno Setup Script
; This script will create an installer for EchoScribe with bundled models and recordings folders.

[Setup]
AppName=EchoScribe
AppVersion=1.0
DefaultDirName={pf}\EchoScribe
DefaultGroupName=EchoScribe
UninstallDisplayIcon={app}\main.exe
OutputBaseFilename=EchoScribe-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "models\*"; DestDir: "{app}\models"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "recordings\*"; DestDir: "{app}\recordings"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\EchoScribe"; Filename: "{app}\main.exe"
Name: "{commondesktop}\EchoScribe"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\main.exe"; Description: "Launch EchoScribe"; Flags: nowait postinstall skipifsilent
