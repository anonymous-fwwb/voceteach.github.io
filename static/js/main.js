document.addEventListener('DOMContentLoaded', function() {
    // 加载所有speaker数据
    loadSpeakers();

    // 添加表单提交事件处理
    document.getElementById('add-speaker-form').addEventListener('submit', handleAddSpeaker);
});

// 加载所有speaker数据
async function loadSpeakers() {
    try {
        const response = await fetch('/api/speakers');
        const speakers = await response.json();

        renderSpeakers(speakers);
    } catch (err) {
        console.error('Error loading speakers:', err);
        document.getElementById('speakers-container').innerHTML =
            '<div class="text-center p-4 text-red-500">Failed to load data</div>';
    }
}

// 渲染speaker列表
function renderSpeakers(speakers) {
    const container = document.getElementById('speakers-container');

    if (speakers.length === 0) {
        container.innerHTML = '<div class="text-center p-4">No speakers found. Add your first one!</div>';
        return;
    }

    let html = '';
    speakers.forEach(speaker => {
        html += `
        <div class="grid grid-cols-4 border-b p-4 items-center">
            <div>${speaker.name}</div>
            <div class="flex justify-center">
                ${speaker.prompt ? renderAudioPlayer(speaker.prompt, speaker.audioLength) : 'No prompt audio'}
            </div>
            <div class="text-center px-4 text-sm">
                ${speaker.text}
            </div>
            <div class="flex justify-center">
                ${speaker.indexTTSPath ? renderAudioPlayer(speaker.indexTTSPath, speaker.indexTTS) : 'No TTS audio'}
            </div>
        </div>
        `;
    });

    container.innerHTML = html;
}

// 渲染音频播放器
function renderAudioPlayer(audioSrc, length) {
    return `
    <div class="audio-player">
        <audio controls src="${audioSrc}"></audio>
        <span class="text-xs text-gray-700 ml-2">${length || '0:00'}</span>
    </div>
    `;
}

// 处理添加新speaker
async function handleAddSpeaker(e) {
    e.preventDefault();

    const form = e.target;
    const speakerName = form.speakerName.value;
    const textContent = form.textContent.value;

    // 上传提示音频（如果有）
    let promptPath = '';
    let promptLength = '0:00';
    if (form.promptAudio.files.length > 0) {
        const promptUploadResult = await uploadAudio(form.promptAudio.files[0], 'prompts');
        if (promptUploadResult) {
            promptPath = promptUploadResult.path;
            // 这里可以添加获取音频长度的逻辑
        }
    }

    // 上传TTS音频（如果有）
    let ttsPath = '';
    let ttsLength = '0:00';
    if (form.ttsAudio.files.length > 0) {
        const ttsUploadResult = await uploadAudio(form.ttsAudio.files[0], 'tts');
        if (ttsUploadResult) {
            ttsPath = ttsUploadResult.path;
            // 这里可以添加获取音频长度的逻辑
        }
    }

    // 创建新speaker数据
    const newSpeaker = {
        name: speakerName,
        prompt: promptPath,
        text: textContent,
        audioLength: promptLength,
        indexTTS: ttsLength,
        indexTTSPath: ttsPath
    };

    // 发送到服务器
    try {
        const response = await fetch('/api/speakers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newSpeaker)
        });

        if (response.ok) {
            // 重新加载speaker列表
            loadSpeakers();
            // 重置表单
            form.reset();
        } else {
            alert('Failed to add speaker');
        }
    } catch (err) {
        console.error('Error adding speaker:', err);
        alert('Error adding speaker');
    }
}

// 上传音频文件
async function uploadAudio(file, type) {
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('type', type);

    try {
        const response = await fetch('/api/upload/audio', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            return await response.json();
        } else {
            console.error('Upload failed');
            return null;
        }
    } catch (err) {
        console.error('Error uploading file:', err);
        return null;
    }
}