# TVP BGM Controller

TVP BGM Controllerは、TinyView PlusからのOSCメッセージをトリガーにしてMP3ファイルを再生するPythonアプリケーションです。レースイベントの開始時と終了時に異なる音楽を再生することができます。

このプログラムはvibe programingにより100% AIによりコーティングしました。このREADMEも90%はAIによるものです。

## 機能

- OSCメッセージによる自動再生
  - `/v1/race/event "started"`: レース開始時に選択されたセットの`race`ディレクトリからランダムにMP3を再生
  - `/v1/race/event "finished"`: レース終了時に選択されたセットの`interval`ディレクトリからランダムにMP3を再生
- Web UIによる制御
  - 現在の再生状態の表示
  - 音量調整
  - 再生停止
  - 現在再生中のファイル名表示
  - 4セットの音楽セット切り替え
- ループ再生機能
  - 選択されたMP3ファイルは自動的にループ再生されます

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

## 使用方法

1. MP3ファイルの配置
   - セット1: `race1`と`interval1`ディレクトリ
   - セット2: `race2`と`interval2`ディレクトリ
   - セット3: `race3`と`interval3`ディレクトリ
   - セット4: `race4`と`interval4`ディレクトリ
   - 各ディレクトリにMP3ファイルを配置してください

2. アプリケーションの起動
```bash
# デフォルトポート(5740)で起動
python tvpbgm.py

# カスタムポートで起動
python tvpbgm.py --web-port 8080
```

3. Web UIへのアクセス
   - ブラウザで http://localhost:5740 にアクセス（デフォルトポートの場合）
   - カスタムポートを指定した場合は、指定したポート番号でアクセス
   - Web UIから4つのセットを切り替えることができます
   - 現在選択されているセットが表示されます

4. OSCメッセージの送信
```bash
# レース開始時の音声を再生（現在選択されているセットから）
oscsend 0.0.0.0 4001 /v1/race/event s "started"

# レース終了時の音声を再生（現在選択されているセットから）
oscsend 0.0.0.0 4001 /v1/race/event s "finished"
```

## 設定

- OSCサーバー: `0.0.0.0:4001`
- Web UI: `0.0.0.0:5740`（デフォルト、--web-portオプションで変更可能）

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

1.0 
