from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['AUDIO_FOLDER'] = 'static/audio/'
app.config['PUBLISH_FOLDER'] = 'publish/'  # 存放发布页面的目录
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传大小为16MB

# 确保所有必要目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['AUDIO_FOLDER'], 'prompts'), exist_ok=True)
os.makedirs(os.path.join(app.config['AUDIO_FOLDER'], 'tts'), exist_ok=True)
os.makedirs(app.config['PUBLISH_FOLDER'], exist_ok=True)

# 存储比较数据的文件
SPEAKERS_FILE = 'static/data/speakers.json'
os.makedirs(os.path.dirname(SPEAKERS_FILE), exist_ok=True)

# 初始化示例数据
if not os.path.exists(SPEAKERS_FILE):
    with open(SPEAKERS_FILE, 'w', encoding='utf-8') as f:
        json.dump([
            {
                "id": 1,
                "name": "Speaker-1",
                "promptType": "audio",  # audio 或 text
                "promptAudio": "/static/audio/prompts/speaker1.mp3",
                "promptText": "",  # 如果是文字描述,则这里有内容
                "text": "Old will is a fine fellow but poor and helpless since missus rogers had her accident.",
                "audioLength": "0:04",
                "indexTTS": "0:05",
                "indexTTSPath": "/static/audio/tts/speaker1.mp3"
            },
            {
                "id": 2,
                "name": "Speaker-2",
                "promptType": "text",  # 这个示例用文字描述
                "promptAudio": "",
                "promptText": "一个温柔的女声，语速中等，有轻微法国口音",
                "text": "Silvia was the adoration of france and her talent was the real support of all the comedies.",
                "audioLength": "",
                "indexTTS": "0:14",
                "indexTTSPath": "/static/audio/tts/speaker2.mp3"
            }
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


@app.route('/api/speakers/<int:speaker_id>', methods=['PUT'])
def update_speaker(speaker_id):
    data = request.get_json()
    with open(SPEAKERS_FILE, 'r', encoding='utf-8') as f:
        speakers = json.load(f)

    # 查找要编辑的speaker
    for i, speaker in enumerate(speakers):
        if speaker['id'] == speaker_id:
            # 保留ID，更新其他字段
            data['id'] = speaker_id
            speakers[i] = data
            break
    else:
        return jsonify({'error': 'Speaker not found'}), 404

    with open(SPEAKERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(speakers, f, ensure_ascii=False)

    return jsonify(data)


@app.route('/api/speakers/<int:speaker_id>', methods=['DELETE'])
def delete_speaker(speaker_id):
    with open(SPEAKERS_FILE, 'r', encoding='utf-8') as f:
        speakers = json.load(f)

    # 查找要删除的speaker
    for i, speaker in enumerate(speakers):
        if speaker['id'] == speaker_id:
            del speakers[i]
            break
    else:
        return jsonify({'error': 'Speaker not found'}), 404

    with open(SPEAKERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(speakers, f, ensure_ascii=False)

    return jsonify({'success': True})


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


@app.route('/api/publish', methods=['POST'])
def publish_page():
    """创建一个静态的展示页面"""
    try:
        # 获取当前所有speaker数据
        with open(SPEAKERS_FILE, 'r', encoding='utf-8') as f:
            speakers = json.load(f)

        # 生成一个唯一的文件名 (使用时间戳)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"tts_comparison_{timestamp}.html"
        filepath = os.path.join(app.config['PUBLISH_FOLDER'], filename)

        # 渲染静态页面
        page_content = render_template('publish_template.html',
                                       speakers=speakers,
                                       title="TTS Comparison",
                                       timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(page_content)

        # 返回页面的URL
        page_url = f"/publish/{filename}"

        return jsonify({
            'success': True,
            'url': page_url,
            'filename': filename
        })

    except Exception as e:
        print(f"Error publishing page: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/publish/<filename>')
def show_published(filename):
    """提供已发布的静态页面"""
    return send_from_directory(app.config['PUBLISH_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
