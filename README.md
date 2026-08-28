# SFC2 - メディア変換アプリ

動画・音声・画像ファイルのフォーマット変換とアプリ内プレビューができるパソコン向けGUIデスクトップアプリです。  
GUIによる直感的な操作に加え、CLI（コマンドライン）からのヘッドレス一括変換や、Windows Explorer / macOS Finder の右クリックメニュー連携にも対応しています。

SFC2 is a media converter and preview desktop application for Windows and macOS. It provides a simple GUI, a headless CLI mode, and OS-integrated context-menu actions for converting video, audio, and image files.

<img width="1920" height="1080" alt="GUI_cnv" src="https://github.com/user-attachments/assets/40491963-6839-4dfd-b677-318c6a9288aa" />
*実際の画面（左：English、右：日本語）*

---

## 主な特徴

- **直感的な操作 & 一括変換**
  - ファイルやフォルダのドラッグ＆ドロップ、リスト追加に対応
  - 複数ファイルの一括キュー変換処理
- **目標のファイルサイズに簡単に圧縮できる**
  - 品質をできるだけ落とさずに目標ファイルサイズへ圧縮できる
- **アプリ内プレビュー**
  - 動画・音声の再生確認および画像のプレビュー
- **高機能な変換設定**
  - 解像度変更（元ファイルのアスペクト比固定ボタン付き）
  - 目標ファイルサイズ（MB）を指定した自動ビットレート計算・圧縮（画質優先 / 音声優先の選択可能）
- **CLI（コマンドライン）モード**
  - GUIを起動せずバックグラウンドで高速一括変換
  - 進行状況（Progress %）のリアルタイム表示と終了コード対応
- **OS 右クリックメニュー連携 (Context Menu / Quick Action)**
  - Windows（エクスプローラー）や macOS（Finder クイックアクション）からファイルを右クリックして「SFC2で変換」から即座に変換可能
- **多言語対応 (i18n)**
  - 日本語 / 英語 に対応（設定画面から即時切り替え可能）
- **永続設定 & 変換後アクション**
  - カテゴリ別（動画/音声/画像）のデフォルト出力形式設定
  - フォルダ追加時のサブフォルダ再帰探索の切り替え
  - 変換完了後のファイル自動オープン / 保存先フォルダ表示

---

## 必要要件 & セットアップ

### 前提条件
- **OS**: Windows 10 / 11 (x64 / ARM64), macOS
- **Python**: 3.10 以上（ソースコードから実行する場合）
- **FFmpeg**: 変換・メディア情報取得に必要です（同梱していません）。

### FFmpegの準備
以下のいずれかの方法でご用意ください：
1. FFmpeg をインストールし、システム環境変数 `PATH` に追加する（推奨）
2. アプリのメニュー「設定 > アプリの設定...」または「設定 > FFmpegの保存場所を設定...」から `ffmpeg.exe` のパスを指定する

### インストール (開発環境)

```bash
git clone https://github.com/KinakoMochi393925/SFC2.git
cd SFC2
pip install -r requirements.txt
```

---

## 起動方法

### GUI 起動

```bash
python main.py
```
*(ビルド済み実行ファイルの場合は `SFC2.exe` を直接起動)*

---

## 使い方 (GUI)

1. **ファイル / フォルダの追加**
   - ファイルやフォルダをウィンドウ左側のリストにドラッグ＆ドロップ、または下部のボタン（ファイル追加 / フォルダ追加）から選択します。
2. **変換設定**
   - リストからファイルを選択し、右側のパネルでプレビューを確認しながら変換設定を行います。
   - **出力形式**: 変換先の拡張子を選択
   - **解像度**（動画/画像）: プリセット選択、またはカスタムサイズ（アスペクト比固定可）
   - **目標サイズ**（動画/音声）: 希望のファイルサイズ（MB）と優先度（画質優先/音声優先）を指定可能
   - **保存先・ファイル名**: デフォルトは入力ファイルと同じフォルダ、`元ファイル名_cnv`
3. **変換実行**
   - 「変換開始」ボタンを押すとバックグラウンドでキュー順に変換が開始されます。進捗バーで進行状況を確認できます。
4. **アプリ設定**
   - メニューバーの「設定 > アプリの設定...」から以下を設定できます：
     - FFmpegの実行ファイルパス
     - UI言語（日本語 / English）
     - カテゴリ別（動画・音声・画像）のデフォルト変換形式
     - フォルダ追加時にサブフォルダを含めるかどうか
     - 変換完了後にファイルを開く / フォルダを開く

---

## CLI (コマンドライン) 変換

GUIを起動せずに、保存されたカテゴリ別デフォルト形式で素早く一括変換を行うことができます。  
複数ファイルおよびフォルダ（サブフォルダ設定も反映）の同時指定が可能です。

```bash
# 単一ファイルの変換
SFC2.exe --convert "D:\Videos\sample.mkv"

# 複数ファイル・フォルダの変換
SFC2.exe --convert "movie1.mkv" "music.flac" "D:\Photos"
```

> **Note**: 出力先は各入力ファイルと同じフォルダになり、ファイル名は `元ファイル名_cnv.拡張子` となります。進捗は標準エラー出力にパーセンテージで表示されます。

---

## OS 右クリックメニュー連携

### Windows Explorer

現在のユーザー環境（管理者権限不要）の右クリックメニューに「SFC2で変換」を登録できます。

```bash
# 右クリックメニューの登録
SFC2.exe --register-context-menu

# 右クリックメニューの登録解除
SFC2.exe --unregister-context-menu
```

- **レジストリ登録先**: `HKCU\Software\Classes\*\shell\SFC2.Convert`
- **実行コマンド**: `"<SFC2.exeの絶対パス>" --convert "%1"`

### macOS Finder クイックアクション

設定画面の「右クリックメニュー連携」から「右クリックメニューに登録」を押すと、
ユーザー専用の Finder サービスとして「SFC2で変換」が登録されます。管理者権限は不要です。
登録後は Finder で対応ファイルを右クリックし、「クイックアクション」または「サービス」から
「SFC2で変換」を実行できます。

登録解除は同じ設定画面の「右クリックメニューから解除」から行えます。
ワークフローは `~/Library/Services/SFC2で変換.workflow` に作成されます。

---

## 対応フォーマット

|種類|対応形式|
|---|---|
|動画|MP4, AVI, MOV, MKV, WMV, WEBM, AV1(WebM), GIF|
|音声|WAV, MP3, M4A, OGG, FLAC|
|画像|JPG, JPEG, PNG, BMP, WEBP|

---

## ビルド & インストーラー作成

### 1. PyInstaller によるビルド

`SFC2.spec` を使用して、アイコン (`resources/favicon.ico`) が組み込まれた単一の `SFC2.exe` を生成します。

```bash
pip install pyinstaller
pyinstaller SFC2_win.spec
```
生成された実行ファイルは `dist/SFC2.exe` に配置されます。

macOSでは `SFC2_mac.spec` を使用して `.app` バンドルを生成します。

```bash
pyinstaller SFC2_mac.spec
```

生成されたアプリケーションは `dist/SFC2.app` に配置されます。

### 2. Inno Setup によるインストーラー作成 (Windows)

Inno Setupを使用して、セットアップウィザード形式のインストーラー（`SFC2_v1.2.0_Setup.exe`）を作成できます。

- 設定ファイル: `installer/SFC2.iss`
- 64bit OS (x64 / ARM64 Windows 11/10) 対応
- 一般ユーザー権限（UAC昇格不要）でインストール可能
- デスクトップショートカット作成、日英言語選択対応

---

## プロジェクト構成

```
SFC2/
├── main.py                     # アプリケーションエントリポイント (GUI / CLI判定)
├── requirements.txt            # Python依存パッケージ定義
├── SFC2.spec                   # PyInstaller ビルド設定ファイル
│
├── installer/
│   └── SFC2.iss                # Inno Setup インストーラースクリプト
│
├── ui/                         # メインウィンドウ & グローバルスタイル
│   ├── main_window.py
│   └── style.py
│
├── widgets/                    # 個別UIコンポーネント
│   ├── file_list_widget.py     # ファイルリスト・D&D受付
│   ├── preview_area.py         # プレビュー表示統合エリア
│   ├── video_preview.py        # 動画プレビュー
│   ├── audio_preview.py        # 音声プレビュー
│   ├── image_preview.py        # 画像プレビュー
│   ├── conversion_settings_widget.py # フォーマット・解像度・サイズ設定
│   ├── output_settings_widget.py     # 保存先・ファイル名設定
│   ├── progress_widget.py      # 進捗バー表示
│   ├── app_settings_dialog.py  # 全体設定ダイアログ
│   ├── ffmpeg_settings_dialog.py
│   └── ffmpeg_path_widget.py
│
├── services/                   # バックエンド・変換・外部連携
│   ├── cli_conversion.py       # CLI用同期変換コントローラー
│   ├── conversion_worker.py    # FFmpeg変換ワーカー (QThread)
│   ├── ffmpeg_command_builder.py # FFmpeg引数組み立て
│   ├── ffmpeg_locator.py       # FFmpeg実行ファイル探索
│   ├── media_probe.py          # メディアメタデータ取得 (ffprobe/QImage)
│   ├── bitrate_calculator.py   # 目標サイズからのビットレート計算
│   ├── windows_context_menu.py # Windowsレジストリ右クリック登録
│   └── mac_context_menu.py     # macOS Finderクイックアクション登録
│
├── models/                     # データ構造クラス
│   ├── conversion_settings.py  # 変換設定モデル
│   └── file_info.py            # メディアファイル情報モデル
│
├── settings/                   # 設定永続化 (QSettings)
│   └── app_settings.py
│
├── utils/                      # 共通ユーティリティ
│   ├── constants.py            # 定数・拡張子リスト
│   ├── file_type_detector.py   # ファイルカテゴリ判定
│   ├── filename_utils.py       # ファイル名整形・サニタイズ
│   ├── format_utils.py         # サイズ・時間フォーマット
│   ├── i18n.py                 # 多言語化管理 (日英)
│   ├── logger.py               # ログ設定 (app.log / CLI stderr)
│   └── resource_path.py        # リソースパス解決 (PyInstaller対応)
│
├── resources/                  # アイコン・アセット
│   ├── favicon.ico
│   └── SFC_cnv.png
│
├── tests/                      # テストコード
│   └── test_cli_conversion.py
│
└── logs/                       # 実行時ログ出力先
    └── app.log
```

---

## ログとトラブルシューティング

- アプリ起動中および変換中の動作ログや例外は、自動的に `logs/app.log` に記録されます（最大2MB × 3世代ローテーション）。
- CLI実行時は、`--convert` 実行時のログおよび進捗がコンソール（標準エラー出力）にも出力されます。
- FFmpegが見つからないエラーが発生した場合は、環境変数 `PATH` を確認するか、アプリ設定から直接パスを指定してください。
