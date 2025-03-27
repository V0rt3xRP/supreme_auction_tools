#define MyAppName "ReNinja"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "V0rt3xRP"
#define MyAppURL "https://github.com/V0rt3xRP/supreme_auction_tools"
#define MyAppExeName "ReNinja.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId in installers for other applications.
AppId={{A1B2C3D4-E5F6-4321-8765-9ABCDEF01234}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=ReNinja_Setup
SetupIconFile=assets\reninja_logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application files
Source: "dist\ReNinja\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Check if application is running during uninstall
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // Try to close the application if it's running
  if CheckForMutexes('ReNinja_Instance') then
  begin
    if MsgBox('ReNinja is currently running. The application needs to be closed before uninstalling. Would you like to close it now?',
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Try to close gracefully first
      ShellExec('', ExpandConstant('{app}\{#MyAppExeName}'), '--quit', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Sleep(1000);
      
      // Force close if still running
      if CheckForMutexes('ReNinja_Instance') then
        ShellExec('', 'taskkill.exe', '/F /IM {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end
    else
      Result := False;
  end;
end;

// Check if application is running during install/upgrade
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  PrevPath: String;
begin
  Result := True;

  // Check if previous version exists and is running
  if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ReNinja_is1',
     'InstallLocation', PrevPath) then
  begin
    if CheckForMutexes('ReNinja_Instance') then
    begin
      if MsgBox('ReNinja is currently running. The application needs to be closed before updating. Would you like to close it now?',
        mbConfirmation, MB_YESNO) = IDYES then
      begin
        // Try to close gracefully first
        ShellExec('', ExpandConstant(PrevPath + '\{#MyAppExeName}'), '--quit', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        Sleep(1000);
        
        // Force close if still running
        if CheckForMutexes('ReNinja_Instance') then
          ShellExec('', 'taskkill.exe', '/F /IM {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      end
      else
        Result := False;
    end;
  end;
end; 