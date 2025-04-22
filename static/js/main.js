// 全局变量，用于存储当前正在编辑的speaker数据
let currentEditId = null;
let speakersData = [];
let deleteId = null;

document.addEventListener('DOMContentLoaded', function() {
    // 加载所有speaker数据
    loadSpeakers();

    // 添加表单提交事件处理
    document.getElementById('speaker-form').addEventListener('submit', handleSpeakerFormSubmit);

    // 添加发布按钮事件处理
    document.getElementById('publish-btn').addEventListener('click', handlePublish);

    // 添加关闭提示框事件处理
    const closeBtn = document.getElementById('close-alert');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            document.getElementById('publish-success').classList.add('hidden');
        });
    }

    // 添加取消编辑按钮事件处理
    document.getElementById('cancel-btn').addEventListener('click', resetForm);

    // 设置删除模态框事件
    document.getElementById('cancel-delete').addEventListener('click', hideDeleteModal);
    document.getElementById('confirm-delete').addEventListener('click', confirmDeleteSpeaker);
});

// 切换提示输入方式
function togglePromptInputs(type) {
    const audioDiv = document.getElementById('promptAudioDiv');
    const textDiv = document.getElementById('promptTextDiv');

    if (type === 'audio') {
        audioDiv.style.display = 'block';
        textDiv.style.display = 'none';
    } else {
        audioDiv.style.display = 'none';
        textDiv.style.display = 'block';
    }
}

// 加载所有speaker数据
async function loadSpeakers() {
    try {
        const response = await fetch('/api/speakers');
        speakersData = await response.json();

        renderSpeakers(speakersData);
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
        <div class="grid grid-cols-5 border-b p-4 items-center">
            <div>${speaker.name}</div>
            <div class="flex justify-center">
                ${renderPrompt(speaker)}
            </div>
            <div class="text-center px-4 text-sm">
                ${speaker.text}
            </div>
            <div class="flex justify-center">
                ${speaker.indexTTSPath ? renderAudioPlayer(speaker.indexTTSPath, speaker.indexTTS) : 'No TTS audio'}
            </div>
            <div class="flex justify-center space-x-2">
                <button
                    onclick="editSpeaker(${speaker.id})"
                    class="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded-md text-sm"
                >
                    编辑
                </button>
                <button
                    onclick="deleteSpeaker(${speaker.id})"
                    class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-md text-sm"
                >
                    删除
                </button>
            </div>
        </div>
        `;
    });

    container.innerHTML = html;
}

// 渲染提示（可以是音频或文字）
function renderPrompt(speaker) {
    if (speaker.promptType === 'audio' && speaker.promptAudio) {
        return renderAudioPlayer(speaker.promptAudio, speaker.audioLength);
    } else if (speaker.promptType === 'text' && speaker.promptText) {
        return `<div class="text-center italic">"${speaker.promptText}"</div>`;
    } else {
        return 'No prompt';
    }
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

// 处理表单提交（添加或编辑）
async function handleSpeakerFormSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const speakerId = form.speakerId.value;
    const speakerName = form.speakerName.value;
    const textContent = form.textContent.value;
    const promptType = form.promptType.value;

    // 判断是添加还是编辑
    const isEditing = speakerId !== '';

    // 初始化speaker数据
    let speakerData = {
        name: speakerName,
        promptType: promptType,
        text: textContent
    };

    // 如果是编辑模式，需要保留原有数据
    if (isEditing) {
        const originalSpeaker = speakersData.find(s => s.id == speakerId);
        if (originalSpeaker) {
            speakerData = {
                ...originalSpeaker,
                name: speakerName,
                promptType: promptType,
                text: textContent
            };

            // 根据提示类型处理不同的输入
            if (promptType === 'audio') {
                if (form.promptAudio.files.length > 0) {
                    const promptUploadResult = await uploadAudio(form.promptAudio.files[0], 'prompts');
                    if (promptUploadResult) {
                        speakerData.promptAudio = promptUploadResult.path;
                        // 这里可以添加获取音频长度的逻辑
                        speakerData.audioLength = '0:05'; // 示例长度，实际应测量
                    }
                    speakerData.promptText = ''; // 清除文字描述
                }
                // 如果没有上传新文件，保留原来的音频
            } else {
                speakerData.promptText = form.promptText.value;
                // 如果切换了类型，需要清除音频
                if (originalSpeaker.promptType !== promptType) {
                    speakerData.promptAudio = '';
                    speakerData.audioLength = '0:00';
                }
            }

            // 上传TTS音频（如果有）
            if (form.ttsAudio.files.length > 0) {
                const ttsUploadResult = await uploadAudio(form.ttsAudio.files[0], 'tts');
                if (ttsUploadResult) {
                    speakerData.indexTTSPath = ttsUploadResult.path;
                    // 这里可以添加获取音频长度的逻辑
                    speakerData.indexTTS = '0:05'; // 示例长度，实际应测量
                }
            }
            // 如果没有上传新TTS文件，保留原来的TTS音频
        }
    } else {
        // 添加模式
        speakerData.promptAudio = '';
        speakerData.promptText = '';
        speakerData.audioLength = '0:00';
        speakerData.indexTTS = '0:00';
        speakerData.indexTTSPath = '';

        // 根据提示类型处理不同的输入
        if (promptType === 'audio') {
            if (form.promptAudio.files.length > 0) {
                const promptUploadResult = await uploadAudio(form.promptAudio.files[0], 'prompts');
                if (promptUploadResult) {
                    speakerData.promptAudio = promptUploadResult.path;
                    // 这里可以添加获取音频长度的逻辑
                    speakerData.audioLength = '0:05'; // 示例长度，实际应测量
                }
            }
        } else {
            speakerData.promptText = form.promptText.value;
        }

        // 上传TTS音频（如果有）
        if (form.ttsAudio.files.length > 0) {
            const ttsUploadResult = await uploadAudio(form.ttsAudio.files[0], 'tts');
            if (ttsUploadResult) {
                speakerData.indexTTSPath = ttsUploadResult.path;
                // 这里可以添加获取音频长度的逻辑
                speakerData.indexTTS = '0:05'; // 示例长度，实际应测量
            }
        }
    }

    // 发送到服务器
    try {
        let url = '/api/speakers';
        let method = 'POST';

        if (isEditing) {
            url = `/api/speakers/${speakerId}`;
            method = 'PUT';
        }

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(speakerData)
        });

        if (response.ok) {
            // 重新加载speaker列表
            loadSpeakers();
            // 重置表单
            resetForm();
        } else {
            alert('操作失败');
        }
    } catch (err) {
        console.error('Error saving speaker:', err);
        alert('保存失败：' + err.message);
    }
}

// 编辑speaker
function editSpeaker(id) {
    const speaker = speakersData.find(s => s.id === id);
    if (!speaker) return;

    currentEditId = id;

    // 更新表单标题
    document.getElementById('form-title').textContent = '编辑语音比较';
    document.getElementById('submit-btn').textContent = '保存修改';

    // 显示取消按钮
    document.getElementById('cancel-btn').classList.remove('hidden');

    // 填充表单数据
    const form = document.getElementById('speaker-form');
    form.speakerId.value = speaker.id;
    form.speakerName.value = speaker.name;
    form.promptType.value = speaker.promptType;
    form.textContent.value = speaker.text;

    // 根据提示类型显示相应的输入
    togglePromptInputs(speaker.promptType);

    if (speaker.promptType === 'text') {
        form.promptText.value = speaker.promptText;
    } else if (speaker.promptAudio) {
        // 显示当前的音频文件名
        document.getElementById('current-prompt-audio').classList.remove('hidden');
        document.getElementById('prompt-audio-name').textContent = speaker.promptAudio.split('/').pop();
    }

    if (speaker.indexTTSPath) {
        // 显示当前的TTS音频文件名
        document.getElementById('current-tts-audio').classList.remove('hidden');
        document.getElementById('tts-audio-name').textContent = speaker.indexTTSPath.split('/').pop();
    }

    // 滚动到表单位置
    document.getElementById('form-title').scrollIntoView({ behavior: 'smooth' });
}

// 重置表单到添加模式
function resetForm() {
    currentEditId = null;

    // 更新表单标题
    document.getElementById('form-title').textContent = '添加新语音比较';
    document.getElementById('submit-btn').textContent = '添加语音比较';

    // 隐藏取消按钮
    document.getElementById('cancel-btn').classList.add('hidden');

    // 清空表单
    const form = document.getElementById('speaker-form');
    form.reset();
    form.speakerId.value = '';

    // 隐藏当前文件信息
    document.getElementById('current-prompt-audio').classList.add('hidden');
    document.getElementById('current-tts-audio').classList.add('hidden');

    // 重置为音频提示类型
    togglePromptInputs('audio');
}

// 显示删除确认模态框
function deleteSpeaker(id) {
    deleteId = id;
    document.getElementById('delete-modal').classList.remove('hidden');
}

// 隐藏删除模态框
function hideDeleteModal() {
    document.getElementById('delete-modal').classList.add('hidden');
    deleteId = null;
}

// 确认删除speaker
async function confirmDeleteSpeaker() {
    if (deleteId === null) return;

    try {
        const response = await fetch(`/api/speakers/${deleteId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            // 重新加载speaker列表
            loadSpeakers();
            // 如果正在编辑被删除的项，重置表单
            if (currentEditId === deleteId) {
                resetForm();
            }
        } else {
            alert('删除失败');
        }
    } catch (err) {
        console.error('Error deleting speaker:', err);
        alert('删除失败：' + err.message);
    }

    // 隐藏模态框
    hideDeleteModal();
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

// 处理发布按钮点击
async function handlePublish() {
    try {
        // 禁用按钮，防止重复点击
        const publishBtn = document.getElementById('publish-btn');
        publishBtn.disabled = true;
        publishBtn.textContent = '正在发布...';

        // 调用发布API
        const response = await fetch('/api/publish', {
            method: 'POST'
        });

        // 重新启用按钮
        publishBtn.disabled = false;
        publishBtn.textContent = '发布展示页面';

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                // 显示成功消息和链接
                const publishSuccess = document.getElementById('publish-success');
                const publishLink = document.getElementById('publish-link');

                publishLink.href = result.url;
                publishLink.textContent = window.location.origin + result.url;

                publishSuccess.classList.remove('hidden');

                // 5秒后自动关闭提示
                setTimeout(() => {
                    publishSuccess.classList.add('hidden');
                }, 5000);
            } else {
                alert('发布失败: ' + (result.error || '未知错误'));
            }
        } else {
            alert('发布请求失败');
        }
    } catch (err) {
        console.error('Error publishing page:', err);
        alert('发布出错: ' + err.message);

        // 确保按钮重新启用
        const publishBtn = document.getElementById('publish-btn');
        publishBtn.disabled = false;
        publishBtn.textContent = '发布展示页面';
    }
}