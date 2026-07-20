#ifndef ProjectRoot
  #define ProjectRoot "..\.."
#endif

#define VersionFile AddBackslash(ProjectRoot) + "VERSION"

#if !FileExists(VersionFile)
  #error "File VERSION non trovato nella root del progetto"
#endif

#define VerHandle FileOpen(VersionFile)
#define MyAppVersion Trim(FileRead(VerHandle))
#expr FileClose(VerHandle)
#define MyAppName "FinanceTracker"
#define MyAppPublisher "Carlo La Sala"
#define MyAppExeName "FinanceTracker.exe"
; VersionInfo* vuole 4 numeri (es. 1.1.0.0)
#define MyAppVersionInfo MyAppVersion + ".0"

[Setup]
AppId={{86EC67C4-9446-4AA9-B2DD-894C37EEA735}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

SourceDir={#ProjectRoot}
OutputDir={#ProjectRoot}\installer_output
OutputBaseFilename=FinanceTracker_Setup_v{#MyAppVersion}

SetupIconFile={#ProjectRoot}\assets\icons\ft_logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

CloseApplications=yes
RestartApplications=no

VersionInfoVersion={#MyAppVersionInfo}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=FinanceTracker Personal Finance Manager
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; \
    Description: "Crea un collegamento sul desktop"; \
    GroupDescription: "Collegamenti aggiuntivi:"; \
    Flags: unchecked

[Files]
Source: "dist\FinanceTracker.exe"; \
    DestDir: "{app}"; \
    Flags: ignoreversion

[Icons]
Name: "{autoprograms}\FinanceTracker"; \
    Filename: "{app}\FinanceTracker.exe"; \
    WorkingDir: "{app}"

Name: "{autodesktop}\FinanceTracker"; \
    Filename: "{app}\FinanceTracker.exe"; \
    WorkingDir: "{app}"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\FinanceTracker.exe"; \
    Description: "Avvia FinanceTracker"; \
    WorkingDir: "{app}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
