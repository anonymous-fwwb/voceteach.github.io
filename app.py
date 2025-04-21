from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['AUDIO_FOLDER'] = 'static/audio/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传大小为16MB

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['AUDIO_FOLDER'], 'prompts'), exist_ok=True)
os.makedirs(os.path.join(app.config['AUDIO_FOLDER'], 'tts'), exist_ok=True)

# 存储比较数据的文件
SPEAKERS_FILE = 'static/data/speakers.json'
os.makedirs(os.path.dirname(SPEAKERS_FILE), exist_ok=True)

# 初始化示例数据
if not os.path.exists(SPEAKERS_FILE):
    with open(SPEAKERS_FILE, 'w', encoding='utf-8') as f:
        json.dump([
            # 可以添加更多示例数据
        ], f, ensure_ascii=False)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/speakers', methods=['GET'])
def get_speakers():
    with open(SPEAKERS_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/speakers', methods=['POST'])
def add_speaker():
    data = request.get_json()
    with open(SPEAKERS_FILE, 'r', encoding='utf-8') as f:
        speakers = json.load(f)

    # 给新speaker分配ID
    new_id = max([s['id'] for s in speakers], default=0) + 1
    data['id'] = new_id

    speakers.append(data)

    with open(SPEAKERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(speakers, f, ensure_ascii=False)

    return jsonify(data), 201


@app.route('/api/upload/audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 处理音频类型 (prompt or tts)
    audio_type = request.form.get('type', 'prompts')
    if audio_type not in ['prompts', 'tts']:
        audio_type = 'prompts'

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['AUDIO_FOLDER'], audio_type, filename)
    file.save(save_path)

    # 返回可访问的URL路径
    url_path = f"/static/audio/{audio_type}/{filename}"

    return jsonify({
        'success': True,
        'path': url_path,
        'filename': filename
    })


if __name__ == '__main__':
    app.run(debug=True)