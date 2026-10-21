; Windows installer for Facet (Inno Setup 6). Built by `python scripts/build.py --installer`,
; which passes AppVersion, Publisher, Homepage, SourceDir (the PyInstaller folder build),
; IconFile, FileIconsDir (the .ico of each 3D file type) and OutputDir with /D.
;
; Installs for the current user by default (no admin prompt); the wizard offers
; "install for all users" too. Your settings live in AppData, so upgrading
; or uninstalling never touches them.

#define AppName "Facet"
#define AppExe "Facet.exe"

[Setup]
; Never change AppId: Windows uses it to recognise upgrades of the same app.
AppId={{8B4D2F61-1E7A-4C93-A5D0-6F3B9E21C8A7}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#Publisher}
AppPublisherURL={#Homepage}
AppSupportURL={#Homepage}/issues
AppUpdatesURL={#Homepage}/releases
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#Publisher}
VersionInfoDescription={#AppName} setup
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
WizardStyle=modern
ChangesAssociations=yes
Compression=lzma2/max
SolidCompression=yes
; Upgrading while Facet is open: offer to close it, then start it again afterwards.
CloseApplications=yes
RestartApplications=yes
OutputDir={#OutputDir}
OutputBaseFilename=Facet-{#AppVersion}-windows-x64-setup

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

Source: "{#FileIconsDir}\*.ico"; DestDir: "{app}\icons"; Flags: ignoreversion

[InstallDelete]
; Drop files from the previous version's folder build before copying the new one.
Type: filesandordirs; Name: "{app}\_internal"

[Registry]
; One file type per 3D format, each with its own icon. Facet is offered in "Open with" without
; taking the files over from a slicer; the icon shows for whoever makes Facet the default.
Root: HKA; Subkey: "Software\Classes\.stl\OpenWithProgids"; ValueType: string; ValueName: "Facet.Stl"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\Facet.Stl"; ValueType: string; ValueName: ""; ValueData: "STL 3D model"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Facet.Stl\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\icons\stl.ico"
Root: HKA; Subkey: "Software\Classes\Facet.Stl\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\.obj\OpenWithProgids"; ValueType: string; ValueName: "Facet.Obj"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\Facet.Obj"; ValueType: string; ValueName: ""; ValueData: "OBJ 3D model"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Facet.Obj\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\icons\obj.ico"
Root: HKA; Subkey: "Software\Classes\Facet.Obj\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\.ply\OpenWithProgids"; ValueType: string; ValueName: "Facet.Ply"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\Facet.Ply"; ValueType: string; ValueName: ""; ValueData: "PLY 3D model"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Facet.Ply\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\icons\ply.ico"
Root: HKA; Subkey: "Software\Classes\Facet.Ply\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\.3mf\OpenWithProgids"; ValueType: string; ValueName: "Facet.3mf"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\Facet.3mf"; ValueType: string; ValueName: ""; ValueData: "3MF 3D model"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Facet.3mf\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\icons\3mf.ico"
Root: HKA; Subkey: "Software\Classes\Facet.3mf\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#AppExe}"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExe}"; Flags: uninsdeletekey

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; An update from inside Facet runs this setup silently: start Facet again when it's done.
Filename: "{app}\{#AppExe}"; Flags: nowait skipifnotsilent
