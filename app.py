from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
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

# 存储表格数据的文件
TABLES_FILE = 'static/data/tables.json'
os.makedirs(os.path.dirname(TABLES_FILE), exist_ok=True)

# 初始化表格数据
if not os.path.exists(TABLES_FILE):
    with open(TABLES_FILE, 'w', encoding='utf-8') as f:
        json.dump([
            {
                "id": 1,
                "name": "标准语音",
                "description": "这是默认的TTS比较表格",
                "created_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ], f, ensure_ascii=False)


# 获取存储speakers的文件路径
def get_speakers_file(table_id):
    return f'static/data/speakers_{table_id}.json'


# 初始化示例数据
def init_speakers_data(table_id):
    speakers_file = get_speakers_file(table_id)
    if not os.path.exists(speakers_file):
        with open(speakers_file, 'w', encoding='utf-8') as f:
            json.dump([
                {
                    "id": 1,
                    "name": "Speaker-1",
                    "promptType": "audio",
                    "promptAudio": "/static/audio/prompts/speaker1.mp3",
                    "promptText": "",
                    "text": "Old will is a fine fellow but poor and helpless since missus rogers had her accident.",
                    "indexTTSPath": "/static/audio/tts/speaker1.mp3"
                }
            ], f, ensure_ascii=False)


# 初始化第一个表格的数据
init_speakers_data(1)


@app.route('/')
def index():
    return redirect(url_for('table_view', table_id=1))


@app.route('/table/<int:table_id>')
def table_view(table_id):
    # 确保表格存在
    with open(TABLES_FILE, 'r', encoding='utf-8') as f:
        tables = json.load(f)

    table = next((t for t in tables if t['id'] == table_id), None)
    if not table:
        # 如果表格不存在，重定向到第一个表格
        return redirect(url_for('index'))

    # 初始化表格数据（如果不存在）
    init_speakers_data(table_id)

    return render_template('index.html', current_table_id=table_id, tables=tables)


@app.route('/api/tables', methods=['GET'])
def get_tables():
    with open(TABLES_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/tables', methods=['POST'])
def create_table():
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Table name is required'}), 400

    with open(TABLES_FILE, 'r', encoding='utf-8') as f:
        tables = json.load(f)

    # 创建新表格
    new_id = max([t['id'] for t in tables], default=0) + 1
    new_table = {
        "id": new_id,
        "name": data['name'],
        "description": data.get('description', ''),
        "created_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    tables.append(new_table)

    with open(TABLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(tables, f, ensure_ascii=False)

    # 初始化新表格的speakers数据
    init_speakers_data(new_id)

    return jsonify(new_table), 201


@app.route('/api/tables/<int:table_id>', methods=['DELETE'])
def delete_table(table_id):
    # 不允许删除ID为1的默认表格
    if table_id == 1:
        return jsonify({'error': 'Cannot delete the default table'}), 403

    with open(TABLES_FILE, 'r', encoding='utf-8') as f:
        tables = json.load(f)

    # 查找要删除的表格
    for i, table in enumerate(tables):
        if table['id'] == table_id:
            del tables[i]
            break
    else:
        return jsonify({'error': 'Table not found'}), 404

    with open(TABLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(tables, f, ensure_ascii=False)

    # 删除相关的speakers数据文件
    speakers_file = get_speakers_file(table_id)
    if os.path.exists(speakers_file):
        os.remove(speakers_file)

    return jsonify({'success': True})


@app.route('/api/tables/<int:table_id>/speakers', methods=['GET'])
def get_table_speakers(table_id):
    speakers_file = get_speakers_file(table_id)

    # 确保数据文件存在
    init_speakers_data(table_id)

    with open(speakers_file, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/tables/<int:table_id>/speakers', methods=['POST'])
def add_table_speaker(table_id):
    speakers_file = get_speakers_file(table_id)

    # 确保数据文件存在
    init_speakers_data(table_id)

    data = request.get_json()
    with open(speakers_file, 'r', encoding='utf-8') as f:
        speakers = json.load(f)

    # 给新speaker分配ID
    new_id = max([s['id'] for s in speakers], default=0) + 1
    data['id'] = new_id

    speakers.append(data)

    with open(speakers_file, 'w', encoding='utf-8') as f:
        json.dump(speakers, f, ensure_ascii=False)

    return jsonify(data), 201


@app.route('/api/tables/<int:table_id>/speakers/<int:speaker_id>', methods=['PUT'])
def update_table_speaker(table_id, speaker_id):
    speakers_file = get_speakers_file(table_id)

    # 确保数据文件存在
    init_speakers_data(table_id)

    data = request.get_json()
    with open(speakers_file, 'r', encoding='utf-8') as f:
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

    with open(speakers_file, 'w', encoding='utf-8') as f:
        json.dump(speakers, f, ensure_ascii=False)

    return jsonify(data)


@app.route('/api/tables/<int:table_id>/speakers/<int:speaker_id>', methods=['DELETE'])
def delete_table_speaker(table_id, speaker_id):
    speakers_file = get_speakers_file(table_id)

    # 确保数据文件存在
    init_speakers_data(table_id)

    with open(speakers_file, 'r', encoding='utf-8') as f:
        speakers = json.load(f)

    # 查找要删除的speaker
    for i, speaker in enumerate(speakers):
        if speaker['id'] == speaker_id:
            del speakers[i]
            break
    else:
        return jsonify({'error': 'Speaker not found'}), 404

    with open(speakers_file, 'w', encoding='utf-8') as f:
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

    # 为文件名添加时间戳前缀以确保唯一性
    filename = secure_filename(file.filename)
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    unique_filename = f"{timestamp}_{filename}"

    save_path = os.path.join(app.config['AUDIO_FOLDER'], audio_type, unique_filename)
    file.save(save_path)

    # 返回可访问的URL路径
    url_path = f"/static/audio/{audio_type}/{unique_filename}"

    return jsonify({
        'success': True,
        'path': url_path,
        'filename': unique_filename
    })


@app.route('/api/tables/<int:table_id>/publish', methods=['POST'])
def publish_table(table_id):
    """创建一个静态的展示页面"""
    try:
        # 获取表格信息
        with open(TABLES_FILE, 'r', encoding='utf-8') as f:
            tables = json.load(f)

        table = next((t for t in tables if t['id'] == table_id), None)
        if not table:
            return jsonify({'error': 'Table not found'}), 404

        # 获取当前表格的speakers数据
        speakers_file = get_speakers_file(table_id)
        with open(speakers_file, 'r', encoding='utf-8') as f:
            speakers = json.load(f)

        # 生成一个唯一的文件名 (使用时间戳)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"tts_comparison_{table_id}.html"
        filepath = os.path.join(app.config['PUBLISH_FOLDER'], filename)

        # 渲染静态页面
        page_content = render_template('publish_template.html',
                                       speakers=speakers,
                                       title=f"TTS Comparison - {table['name']}",
                                       table=table,
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