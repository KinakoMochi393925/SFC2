; このスクリプトは Inno Setup スクリプトウィザード によって生成されました。
; Inno Setup スクリプトファイルの作成方法の詳細については、ドキュメントを参照してください！
; 非商用利用のみ.

#define MyAppName "SFC2"
#define MyAppVersion "1.3.0"
#define MyAppPublisher "KinakomoChi"
#define MyAppURL "https://github.com/KinakoMochi393925/SFC2"
#define MyAppExeName "SFC2.exe"
#define DoubleAmp(Value) StringChange(Value, "&", "&&")
#define EscapeConstArgument(Value) StringChange(StringChange(StringChange(Value, "%", "%25"), ",", "%2c"), "}", "%7d")

[Setup]
; 注意: AppId の値はこのアプリケーションを一意に識別します。他のアプリケーションのインストーラーで同じ AppId の値を使用しないでください。
; (新しい GUID を生成するには、IDE 内で「ツール」|「GUID の生成」をクリックしてください。)
AppId={{487B6C77-559C-4FC6-9426-E7B0390EB4CB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={cm:NameAndVersion,{#EscapeConstArgument(MyAppName)},{#EscapeConstArgument(MyAppVersion)}}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
; "ArchitecturesAllowed=x64compatible" は、セットアップが x64 および Arm 版 Windows 11 以外では実行できないことを指定します。
ArchitecturesAllowed=x64compatible
; "ArchitecturesInstallIn64BitMode=x64compatible" は、x64 または Arm 版 Windows 11 で「64 ビットモード」でインストールを実行するように要求します。
; これは、ネイティブの 64 ビット Program Files フォルダーおよびレジストリの 64 ビットビューを使用することを意味します。
ArchitecturesInstallIn64BitMode=x64compatible
; 64 ビットインストーラーを使用するには、次の行のコメントを解除してください。
;SetupArchitecture=x64
ChangesAssociations=yes
DisableProgramGroupPage=yes
; 管理者インストールモード (すべてのユーザーにインストール) で実行するには、次の行を削除してください。
PrivilegesRequired=lowest
OutputBaseFilename=SFC2_Win_v1.3.0_Setup
SetupIconFile=..\resources\favicon.ico
SolidCompression=yes
WizardStyle=classic dynamic
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "contextmenu"; Description: "右クリックメニューに「SFC2で変換」を登録する"; GroupDescription: "追加設定:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 注意: 共有システムファイルには "Flags: ignoreversion" を使用しないでください。

; [Registry]
; Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
; Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--register-context-menu"; Tasks: contextmenu; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#DoubleAmp(MyAppName)}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; アンインストール実行時にサイレントで登録解除コマンドを実行する
Filename: "{app}\{#MyAppExeName}"; Parameters: "--unregister-context-menu"; Flags: runhidden