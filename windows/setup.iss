; Inno Setup Script for HelaKatha (Singlish to Sinhala Input Tool)
; Compile using Inno Setup Compiler (ISCC.exe)

[Setup]
AppName=HelaKatha
AppVersion=1.0.0
AppPublisher=HelaKatha
DefaultDirName={autopf}\HelaKatha
DefaultGroupName=HelaKatha
UninstallDisplayIcon={app}\HelaKatha.exe
SetupIconFile=icon.ico
OutputDir=.
OutputBaseFilename=HelaKathaSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Support both per-user and administrative installations
PrivilegesRequiredOverridesAllowed=dialog

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Run HelaKatha automatically when Windows starts"; GroupDescription: "Additional options:"; Flags: checked

[Files]
Source: "dist\HelaKatha.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\HelaKatha"; Filename: "{app}\HelaKatha.exe"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\HelaKatha"; Filename: "{app}\HelaKatha.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{userstartup}\HelaKatha"; Filename: "{app}\HelaKatha.exe"; IconFilename: "{app}\icon.ico"; Tasks: startupicon

[Run]
Filename: "{app}\HelaKatha.exe"; Description: "{cm:LaunchProgram,HelaKatha}"; Flags: nowait postinstall skipifsilent
