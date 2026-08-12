# SFC2 - メディア変換アプリ

動画・音声・画像ファイルのフォーマット変換とアプリ内プレビューができる
Windows 11 向けGUIデスクトップアプリです。

SFC2 is a GUI desktop application for Windows 11 that allows you to convert video, audio, and image formats, as well as preview files directly within the app.
<img width="1920" height="1080" alt="GUI_cnv" src="https://github.com/user-attachments/assets/40491963-6839-4dfd-b677-318c6a9288aa" />
↑実際の画面（左：English、右：日本語用）↑

## 特徴

- シンプルなGUI
- FFmpegをGUIから簡単に操作
- 日本語・英語対応
- ドラッグ＆ドロップ操作
- 指定サイズへの圧縮
- プレビュー機能

## セットアップ

```bash
pip install -r requirements.txt
```

FFmpeg は同梱していません。以下のいずれかの方法で用意してください。

1. FFmpeg をインストールし、PATH に追加する（推奨）
2. アプリのメニュー「設定 > FFmpegの保存場所を設定...」から
   ffmpeg.exe の場所を指定する

## 起動

```bash
python main.py
```

## 使い方

1. ファイルをドラッグ＆ドロップ、または枠内をクリックして選択する
2. 変換先フォーマット・解像度（動画/画像のみ）を選択する
   - カスタム解像度ではボタンで元ファイルのアスペクト比を固定できる
3. 必要であれば「目標ファイルサイズ」と「優先度（画質優先/音声優先）」を指定する
   （動画・音声のみ。GIF出力時は対象外）
   - 極端に小さいサイズを指定すると警告が表示され、続行するか設定変更するか選べる
4. 保存先フォルダ・出力ファイル名を確認/変更する（デフォルトは
   入力ファイルと同じフォルダ、`元ファイル名_cnv`）
5. 「変換開始」を押すとバックグラウンドで変換が実行され、
   進捗バーに変換の進み具合が表示される

メニューの「設定 > アプリの設定...」から FFmpeg の保存場所と UI言語（日本語/英語）
を変更できる。言語切替はその場で反映されます。

## 対応フォーマット

|種類|対応形式|
|---|---|
|動画|MP4, AVI, MOV, MKV, WMV, WEBM, AV1(WebM), GIF|
|音声|WAV, MP3, M4A, OGG, FLAC|
|画像|JPG, JPEG, PNG, BMP, WEBP|

## アイコン / exe化

タイトルバー・タスクバーには `resources/favicon.ico` が表示される

PyInstaller で1ファイルのexeにパッケージングする場合は同梱の `SFC2.spec` を使う。
`favicon.ico` はexe内部にも組み込まれるため、exe単体の配布で
タイトルバー・タスクバーのアイコン表示まで機能する。

```bash
pip install pyinstaller
pyinstaller SFC2.spec
```

`dist/SFC2.exe` が生成される。

## プロジェクト構成

```
SFC2/
│ main.py                 エントリポイント
│ requirements.txt
│
├─ ui/                    メインウィンドウ・スタイル
├─ widgets/                個別UI部品（プレビュー、設定フォームなど）
├─ services/               FFmpeg検索・コマンド生成・変換ワーカー(QThread)
├─ models/                 データクラス
├─ utils/                  ロガー・ファイル名処理・拡張子判定など
├─ settings/                FFmpegパスなどの永続設定 (QSettings)
├─ resources/
└─ logs/                    実行時ログ (app.log) の出力先
```