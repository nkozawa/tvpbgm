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

# バージョン情報
__version__ = '1.0'
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
current_volume = 0.5
is_playing = False
current_file = None
current_set = 1  # 現在選択されているセット（1-4）

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
    global is_playing, current_file
    
    try:
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
        pygame.mixer.music.set_volume(current_volume)
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
        'volume': current_volume,
        'current_set': current_set,
        'version': __version__,
        'author': __author__
    })

@app.route('/api/volume', methods=['POST'])
def set_volume():
    global current_volume
    try:
        volume = float(request.json.get('volume', 0.5))
        volume = max(0.0, min(1.0, volume))  # 0.0から1.0の範囲に制限
        current_volume = volume
        pygame.mixer.music.set_volume(volume)
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
            return jsonify({'success': True, 'set': current_set})
        else:
            return jsonify({'success': False, 'error': 'Set number must be between 1 and 4'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # コマンドライン引数の解析
    args = parse_args()
    
    # 必要なディレクトリが存在することを確認
    for i in range(1, 5):
        os.makedirs(RACE_DIRS[i], exist_ok=True)
        os.makedirs(INTERVAL_DIRS[i], exist_ok=True)
    # os.makedirs('templates', exist_ok=True)
    
    # OSCサーバーを別スレッドで開始
    osc_thread = threading.Thread(target=start_osc_server)
    osc_thread.daemon = True
    osc_thread.start()
    
    # Flaskサーバーを開始
    print(f"Starting web server on port {args.web_port}")
    app.run(host='0.0.0.0', port=args.web_port) 