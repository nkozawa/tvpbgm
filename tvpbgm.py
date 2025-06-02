import pygame
import os
import time
import random
from pythonosc import dispatcher
from pythonosc import osc_server
import socket
from flask import Flask, render_template, request, jsonify
import threading
import argparse
import sys
import json
import re

# バージョン情報
__version__ = '1.1'
__author__ = 'KozakFPV'

# コマンドライン引数の解析
def parse_args():
    parser = argparse.ArgumentParser(description='TVP BGM Controller')
    parser.add_argument('--web-port', type=int, default=5740,
                      help='Webサーバーのポート番号 (デフォルト: 5740)')
    return parser.parse_args()

# Flaskアプリケーションの初期化
app = Flask(__name__)

# グローバル変数
is_playing = False
current_file = None
current_set = 1  # 現在選択されているセット（1-4）
volume_lower_timer = None  # 音量低下タイマー
volume_reduction_percent = 50  # 音量低下のパーセンテージ（デフォルト50%）

# 各セットとタイプ（race/interval）の音量設定を保存する辞書
volume_settings = {
    'race': {
        1: 0.5,
        2: 0.5,
        3: 0.5,
        4: 0.5
    },
    'interval': {
        1: 0.5,
        2: 0.5,
        3: 0.5,
        4: 0.5
    }
}

# 現在の再生タイプ（race/interval）を追跡
current_type = 'race'

# スクリプトの場所を取得
def get_script_dir():
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた場合
        return os.path.dirname(sys.executable)
    else:
        # 通常のPythonスクリプトとして実行される場合
        return os.path.dirname(os.path.abspath(__file__))

SCRIPT_DIR = get_script_dir()
print(f"Script directory: {SCRIPT_DIR}")

# 設定ファイルのパス
SETTINGS_FILE = os.path.join(SCRIPT_DIR, 'volume_settings.json')

def load_volume_settings():
    """音量設定をJSONファイルから読み込む"""
    global volume_settings, volume_reduction_percent
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                loaded_settings = json.load(f)
                # 読み込んだ設定を現在の設定に反映
                for type_key in ['race', 'interval']:
                    for set_num in range(1, 5):
                        if type_key in loaded_settings and str(set_num) in loaded_settings[type_key]:
                            volume_settings[type_key][set_num] = float(loaded_settings[type_key][str(set_num)])
                
                # 音量低下パーセンテージを読み込む
                if 'volume_reduction_percent' in loaded_settings:
                    volume_reduction_percent = int(loaded_settings['volume_reduction_percent'])
            print("Volume settings loaded successfully")
    except Exception as e:
        print(f"Error loading volume settings: {e}")

def save_volume_settings():
    """音量設定をJSONファイルに保存"""
    try:
        # 数値を文字列に変換して保存（JSONの互換性のため）
        settings_to_save = {
            'race': {str(k): v for k, v in volume_settings['race'].items()},
            'interval': {str(k): v for k, v in volume_settings['interval'].items()},
            'volume_reduction_percent': volume_reduction_percent
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_to_save, f, indent=4)
        print("Volume settings saved successfully")
    except Exception as e:
        print(f"Error saving volume settings: {e}")

# ディレクトリ設定
RACE_DIRS = {
    1: os.path.join(SCRIPT_DIR, 'race1'),
    2: os.path.join(SCRIPT_DIR, 'race2'),
    3: os.path.join(SCRIPT_DIR, 'race3'),
    4: os.path.join(SCRIPT_DIR, 'race4')
}
INTERVAL_DIRS = {
    1: os.path.join(SCRIPT_DIR, 'interval1'),
    2: os.path.join(SCRIPT_DIR, 'interval2'),
    3: os.path.join(SCRIPT_DIR, 'interval3'),
    4: os.path.join(SCRIPT_DIR, 'interval4')
}

# pygame初期化
pygame.mixer.init()

def play_random_mp3(directory, wait):
    """指定されたディレクトリからランダムにMP3ファイルを選択して再生"""
    global is_playing, current_file, current_type
    
    try:
        # 再生タイプを設定
        if 'race' in directory:
            current_type = 'race'
        else:
            current_type = 'interval'

        # ディレクトリ内のMP3ファイルを取得
        mp3_files = [f for f in os.listdir(directory) if f.endswith('.mp3')]
        if not mp3_files:
            print(f"No MP3 files found in {directory}")
            # 再生を停止し、状態を更新
            pygame.mixer.music.stop()
            is_playing = False
            current_file = None
            return

        # ランダムにファイルを選択
        random_file = random.choice(mp3_files)
        full_path = os.path.join(directory, random_file)
        
        # 現在再生中の音声を停止
        pygame.mixer.music.stop()
        time.sleep(wait)  # 少し待機
        
        # 新しい音声を再生
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.set_volume(volume_settings[current_type][current_set])  # 現在のタイプとセットの音量を使用
        pygame.mixer.music.play(-1)  # -1を指定して無限ループ再生
        
        is_playing = True
        current_file = random_file
        print(f"Playing: {random_file}")
        
    except Exception as e:
        print(f"Error playing audio: {e}")
        is_playing = False
        current_file = None

def stop_playback():
    """現在再生中の音声を停止"""
    global is_playing, current_file
    try:
        pygame.mixer.music.stop()
        is_playing = False
        current_file = None
        return True
    except Exception as e:
        print(f"Error stopping playback: {e}")
        return False

def handle_race_event(address, *args):
    """OSCイベントのハンドラー"""
    if not args or len(args) == 0:
        return
    
    print(f"OSC message received - Address: {address}")
    print(f"OSC message args: {args}")
    
    event = args[0]
    if event == "started":
        print(f"Race started - playing random race music from set {current_set}")
        play_random_mp3(RACE_DIRS[current_set], 6)
    elif event == "finished":
        print(f"Race finished - playing random interval music from set {current_set}")
        play_random_mp3(INTERVAL_DIRS[current_set], 2)

def handle_lap_event(address, *args):
    """ラップイベントのハンドラー"""
    global volume_lower_timer
    
    # アドレスからカメラIDを抽出
    match = re.match(r'/v1/camera/(\d+)/lap', address)
    if not match:
        return
    
    camera_id = int(match.group(1))
    if not 1 <= camera_id <= 4:
        return
    
    print(f"Lap event received for camera {camera_id}")
    
    # 現在の音量を保存
    current_volume = volume_settings[current_type][current_set]
    
    # 設定されたパーセンテージで音量を下げる
    reduction_factor = 1.0 - (volume_reduction_percent / 100.0)
    new_volume = max(0.0, current_volume * reduction_factor)
    if is_playing:
        pygame.mixer.music.set_volume(new_volume)
    
    # 既存のタイマーをキャンセル
    if volume_lower_timer is not None:
        volume_lower_timer.cancel()
    
    # 3秒後に元の音量に戻す
    def restore_volume():
        global volume_lower_timer
        if is_playing:
            pygame.mixer.music.set_volume(current_volume)
        volume_lower_timer = None
    
    volume_lower_timer = threading.Timer(3.0, restore_volume)
    volume_lower_timer.start()

def is_port_in_use(port, host='127.0.0.1'):
    """ポートが使用中かどうかを確認"""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True

def start_osc_server():
    """OSCサーバーを開始"""
    osc_dispatcher = dispatcher.Dispatcher()
    osc_dispatcher.map("/v1/race/event", handle_race_event)
    
    # ラップイベントのハンドラーを追加
    for i in range(1, 5):
        osc_dispatcher.map(f"/v1/camera/{i}/lap", handle_lap_event)
    
    port = 4001
    host = '0.0.0.0'
    
    try:
        server = osc_server.ThreadingOSCUDPServer((host, port), osc_dispatcher)
        print(f"OSC Server started on {host}:{port}")
        server.serve_forever()
    except Exception as e:
        print(f"Error starting OSC server: {e}")

# Flaskルート
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify({
        'is_playing': is_playing,
        'current_file': current_file,
        'volume': volume_settings[current_type][current_set],
        'current_set': current_set,
        'current_type': current_type,
        'volume_reduction_percent': volume_reduction_percent,
        'version': __version__,
        'author': __author__
    })

@app.route('/api/volume', methods=['POST'])
def set_volume():
    try:
        volume = float(request.json.get('volume', 0.5))
        volume = max(0.0, min(1.0, volume))  # 0.0から1.0の範囲に制限
        volume_settings[current_type][current_set] = volume  # 現在のタイプとセットの音量を更新
        if is_playing:
            pygame.mixer.music.set_volume(volume)
        # 音量設定を保存
        save_volume_settings()
        return jsonify({'success': True, 'volume': volume})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stop', methods=['POST'])
def stop_music():
    success = stop_playback()
    return jsonify({'success': success})

@app.route('/api/set', methods=['POST'])
def set_current_set():
    global current_set
    try:
        set_number = int(request.json.get('set', 1))
        if 1 <= set_number <= 4:
            current_set = set_number
            # セット切り替え時に音量を更新
            if is_playing:
                pygame.mixer.music.set_volume(volume_settings[current_type][current_set])
            return jsonify({'success': True, 'set': current_set})
        else:
            return jsonify({'success': False, 'error': 'Set number must be between 1 and 4'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/volume-reduction', methods=['POST'])
def set_volume_reduction():
    global volume_reduction_percent
    try:
        percent = int(request.json.get('percent', 50))
        percent = max(0, min(100, percent))  # 0から100の範囲に制限
        volume_reduction_percent = percent
        save_volume_settings()
        return jsonify({'success': True, 'percent': percent})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # コマンドライン引数の解析
    args = parse_args()
    
    # 必要なディレクトリが存在することを確認
    for i in range(1, 5):
        os.makedirs(RACE_DIRS[i], exist_ok=True)
        os.makedirs(INTERVAL_DIRS[i], exist_ok=True)
    #os.makedirs('templates', exist_ok=True)
    
    # 音量設定を読み込む
    load_volume_settings()
    
    # OSCサーバーを別スレッドで開始
    osc_thread = threading.Thread(target=start_osc_server)
    osc_thread.daemon = True
    osc_thread.start()
    
    # Flaskサーバーを開始
    print(f"Starting web server on port {args.web_port}")
    app.run(host='0.0.0.0', port=args.web_port) 