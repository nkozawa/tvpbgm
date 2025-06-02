# TVP BGM Controller

TVP BGM Controllerは、OSCメッセージをトリガーにしてMP3ファイルを再生するPythonアプリケーションです。レースイベントの開始時と終了時に異なる音楽を再生することができます。

このプログラムは無課金vibe programingにより100% AIによりコーティングしました。このREADMEも90%はAIによるものです。

このプログラムのアイデアはninjaMoonLight師匠(<https://x.com/
masaaki_oyama>)によるものです。

- 4セットのBGMディレクトリ（race/interval）を管理
- Web UIからセットの選択が可能
- 音量の調整が可能
- ラップ時の音量低下設定（5段階）
  - 音量低下なし
  - 弱 (25%)
  - 中 (50%)
  - 強 (75%)
  - 最大 (90%)
  音量低下は3秒間持続

## ディレクトリ構造

```
tvpbgm/
├── race1/      # セット1のレースBGM
├── interval1/  # セット1のインターバルBGM
├── race2/      # セット2のレースBGM
├── interval2/  # セット2のインターバルBGM
├── race3/      # セット3のレースBGM
├── interval3/  # セット3のインターバルBGM
├── race4/      # セット4のレースBGM
└── interval4/  # セット4のインターバルBGM
```

## 使用方法

1. アプリケーションを起動
```bash
python tvpbgm.py
```

2. ブラウザで `http://localhost:5740` にアクセス、同一ネット内の他のPCからのアクセスも可能

3. Web UIから以下の操作が可能:
   - セットの選択（1-4）
   - 音量の調整（0-100%）
   - ラップ時の音量低下レベルの設定
   - 再生の停止

## 依存パッケージ

- Flask
- python-osc
- pygame

## インストール方法

```bash
pip install -r requirements.txt
```

## 注意事項

- 各ディレクトリにはMP3ファイルを配置してください
- ディリクトリーに複数のMP3ファイルがある場合はランダムに選択し再生されます
- インターバルBGMは自動的にループ再生されます

## 必要条件

- Python 3.6以上
- 必要なPythonパッケージ（requirements.txtに記載）
  - python-osc
  - pygame
  - flask

## インストール

releaseページにWindowsとMacOS用のバイナリーも用意しました。こちらは特別なインストール作業は必要ありません、そのまま実行出来ます。

1. リポジトリをクローン
```bash
git clone https://github.com/KozakFPV/tvpbgm.git
cd tvpbgm
```

2. 仮想環境を作成して有効化（推奨）
```bash
python -m venv .venv
source .venv/bin/activate  # Linuxの場合
# または
.venv\Scripts\activate  # Windowsの場合
```

3. 必要なパッケージをインストール
```bash
pip install -r requirements.txt
```

## 設定

- OSCサーバー: `0.0.0.0:4001`
- Web UI: `0.0.0.0:5740`（デフォルト、--web-portオプションで変更可能）
- 音量設定: `volume_settings.json`に保存（自動生成）

## コマンドラインオプション

- `--web-port`: Webサーバーのポート番号を指定（デフォルト: 5740）
  ```bash
  python tvpbgm.py --web-port 8080
  ```

## ライセンス

MIT License

## 作者

KozakFPV

## バージョン

1.1 
