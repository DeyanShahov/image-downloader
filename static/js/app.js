// static/js/app.js
// ─── Константи и DOM референции ─────────────────────────────────────
const form = document.getElementById('download-form');
const submitBtn = document.getElementById('submit-btn');
const progressBarContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress-bar');
const logDiv = document.getElementById('log');
const galleryDiv = document.getElementById('results-gallery');
const themeToggleBtn = document.getElementById('theme-toggle');
const clearUrlCheckbox = document.getElementById('clear-url');
const urlTextarea = document.getElementById('url');
const urlIndexHidden = document.getElementById('url-index');
const newUrlInput = document.getElementById('new-url-input');
const addUrlBtn = document.getElementById('add-url-btn');
const loadUrlBtn = document.getElementById('load-url-btn');
const refreshUrlBtn = document.getElementById('refresh-url-btn');
const urlListBody = document.getElementById('url-list-body');
const urlListWrapper = document.getElementById('url-list-wrapper');
const urlListEmpty = document.getElementById('url-list-empty');
const urlStatus = document.getElementById('url-status');
const urlCountSpan = document.getElementById('url-count');

let selectedUrlIndex = -1;  // Кой ред е маркиран

// ─── Тъмна тема ──────────────────────────────────────────────────────
themeToggleBtn.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
});
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}

// ─── API функции ─────────────────────────────────────────────────────
async function apiGetUrls() {
    const res = await fetch('/api/urls');
    return await res.json();
}

async function apiAddUrl(url) {
    const res = await fetch('/api/urls/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
    });
    return await res.json();
}

async function apiDeleteUrl(index) {
    const res = await fetch('/api/urls/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index })
    });
    return await res.json();
}

async function apiUpdateUrl(index, url) {
    const res = await fetch('/api/urls/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index, url })
    });
    return await res.json();
}

// ─── Помощни функции за url_index ──────────────────────────────────
function getUrlIndices() {
    const val = urlIndexHidden.value.trim();
    if (!val) return [];
    return val.split(',').map(Number).filter(n => !isNaN(n));
}

function setUrlIndices(indices) {
    urlIndexHidden.value = indices.join(',');
}

function addUrlIndex(index) {
    const current = getUrlIndices();
    current.push(index);
    setUrlIndices(current);
    console.log('addUrlIndex:', index, '-> url_index:', urlIndexHidden.value);
}

/**
 * Рекурсивно извлича числото от дадена част на URL (директория или файл).
 * Връща числото или null, ако няма.
 */
function extractNumberFromUrlPart(part) {
    const match = part.match(/(\d+)/);
    return match ? match[1] : null;
}

// ─── Показване на статус съобщение ──────────────────────────────────
let statusTimeout = null;
function showStatus(message, type) {
    urlStatus.textContent = message;
    urlStatus.className = 'status-msg ' + type;
    // Показване чрез премахване на скритието
    urlStatus.style.display = 'block';
    // Автоматично скриване след 5 секунди
    if (statusTimeout) clearTimeout(statusTimeout);
    statusTimeout = setTimeout(() => {
        urlStatus.style.display = 'none';
    }, 5000);
}

// ─── Зареждане и рендериране на списъка ─────────────────────────────
async function loadUrlList() {
    try {
        const data = await apiGetUrls();
        renderUrlList(data.urls);
        urlCountSpan.textContent = data.count;
    } catch (err) {
        console.error('Грешка при зареждане на URL списъка:', err);
        showStatus('Грешка при зареждане на списъка.', 'error');
    }
}

function renderUrlList(urls) {
    urlListBody.innerHTML = '';

    if (!urls || urls.length === 0) {
        urlListWrapper.style.display = 'none';
        urlListEmpty.style.display = 'block';
        loadUrlBtn.disabled = true;
        return;
    }

    urlListWrapper.style.display = 'block';
    urlListEmpty.style.display = 'none';
    loadUrlBtn.disabled = false;

    urls.forEach((url, index) => {
        const tr = document.createElement('tr');
        if (index === selectedUrlIndex) {
            tr.classList.add('selected');
        }
        tr.dataset.index = index;

        // Радио бутон за избор (визуален)
        const tdSelect = document.createElement('td');
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'url-select';
        radio.value = index;
        radio.checked = (index === selectedUrlIndex);
        radio.addEventListener('change', () => {
            selectUrl(index);
        });
        tdSelect.appendChild(radio);

        // URL текст
        const tdUrl = document.createElement('td');
        tdUrl.className = 'url-text-cell';
        tdUrl.textContent = url;

        // Бутони за действия
        const tdActions = document.createElement('td');
        tdActions.className = 'url-actions';

        const editBtn = document.createElement('button');
        editBtn.className = 'btn-icon';
        editBtn.title = 'Редактирай';
        editBtn.textContent = '✏️';
        editBtn.addEventListener('click', () => editUrl(index, url));

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn-icon';
        deleteBtn.title = 'Изтрий';
        deleteBtn.textContent = '🗑️';
        deleteBtn.addEventListener('click', () => deleteUrl(index));

        tdActions.appendChild(editBtn);
        tdActions.appendChild(deleteBtn);

        tr.appendChild(tdSelect);
        tr.appendChild(tdUrl);
        tr.appendChild(tdActions);

        // Клик върху целия ред за избор
        tr.addEventListener('click', (e) => {
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON') {
                radio.checked = true;
                selectUrl(index);
            }
        });

        urlListBody.appendChild(tr);
    });
}

// ─── Избор на URL от списъка ────────────────────────────────────────
function selectUrl(index) {
    selectedUrlIndex = index;
    // Обновяваме визуалния избор
    const rows = urlListBody.querySelectorAll('tr');
    rows.forEach((row, i) => {
        row.classList.toggle('selected', i === index);
        const radio = row.querySelector('input[type="radio"]');
        if (radio) radio.checked = (i === index);
    });
    loadUrlBtn.disabled = false;
}

// ─── Зареждане на избрания URL в полето ─────────────────────────────
function loadSelectedUrl() {
    if (selectedUrlIndex < 0) {
        showStatus('Моля, изберете URL адрес от списъка.', 'error');
        return;
    }

    const rows = urlListBody.querySelectorAll('tr');
    if (selectedUrlIndex >= rows.length) {
        showStatus('Невалиден избор.', 'error');
        return;
    }

    const urlCell = rows[selectedUrlIndex].querySelector('.url-text-cell');
    if (!urlCell) return;

    let url = urlCell.textContent.trim();

    // Разделяме URL на части за проверка на дублиране
    const urlParts = url.split('/');
    const urlFilename = urlParts[urlParts.length - 1];
    const urlDirNumber = extractNumberFromUrlPart(urlParts[urlParts.length - 2]);

    // Вземаме всички вече заредени URL-и и проверяваме за съвпадение
    const currentLines = urlTextarea.value.split('\n').map(l => l.trim()).filter(l => l);
    let maxNumber = null;

    for (const line of currentLines) {
        const parts = line.split('/');
        if (parts.length < 2) continue;

        const dirNumber = extractNumberFromUrlPart(parts[parts.length - 2]);
        const filename = parts[parts.length - 1];

        // Ако съвпадат базовата директория и името на файла - това е дубликат
        if (dirNumber && urlDirNumber) {
            const baseMatch = line.indexOf(urlParts.slice(0, -2).join('/'));
            if (baseMatch !== -1 && filename === urlFilename) {
                const num = parseInt(dirNumber, 10);
                if (isNaN(num)) continue;
                if (maxNumber === null || num > maxNumber) {
                    maxNumber = num;
                }
            }
        }
    }

    // Ако има вече зареден URL с тази база, инкрементираме
    if (maxNumber !== null) {
        const newNumber = maxNumber + 1;
        const padding = urlDirNumber ? urlDirNumber.length : 1;
        const newNumberStr = String(newNumber).padStart(padding, '0');
        urlParts[urlParts.length - 2] = urlParts[urlParts.length - 2].replace(
            new RegExp('(\\d+)'),
            newNumberStr
        );
        url = urlParts.join('/');
    }

    // Добавяме URL-а като нов ред в textarea
    const currentValue = urlTextarea.value.trim();
    if (currentValue) {
        urlTextarea.value = currentValue + '\n' + url;
    } else {
        urlTextarea.value = url;
    }

    // Добавяме индекса към списъка с индекси за инкрементиране
    addUrlIndex(selectedUrlIndex);

    showStatus(`URL адресът е зареден в полето: ${url}`, 'success');
}

// ─── Добавяне на нов URL ────────────────────────────────────────────
async function addUrl() {
    const url = newUrlInput.value.trim();
    if (!url) {
        showStatus('Моля, въведете URL адрес.', 'error');
        return;
    }

    try {
        const result = await apiAddUrl(url);
        if (result.success) {
            showStatus(result.message, 'success');
            newUrlInput.value = '';
            renderUrlList(result.urls);
            urlCountSpan.textContent = result.urls.length;
        } else {
            showStatus(result.message, 'error');
        }
    } catch (err) {
        showStatus('Грешка при добавяне на URL адрес.', 'error');
    }
}

// ─── Изтриване на URL ───────────────────────────────────────────────
async function deleteUrl(index) {
    if (!confirm('Сигурни ли сте, че искате да изтриете този URL адрес?')) {
        return;
    }

    try {
        const result = await apiDeleteUrl(index);
        if (result.success) {
            showStatus(result.message, 'success');
            if (selectedUrlIndex === index) {
                selectedUrlIndex = -1;
            } else if (selectedUrlIndex > index) {
                selectedUrlIndex--;
            }
            renderUrlList(result.urls);
            urlCountSpan.textContent = result.urls.length;
        } else {
            showStatus(result.message, 'error');
        }
    } catch (err) {
        showStatus('Грешка при изтриване на URL адрес.', 'error');
    }
}

// ─── Редактиране на URL ─────────────────────────────────────────────
function editUrl(index, currentUrl) {
    const newUrl = prompt('Редактирайте URL адреса:', currentUrl);
    if (!newUrl || newUrl === currentUrl) return;

    fetch('/api/urls/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index, url: newUrl })
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            showStatus(result.message, 'success');
            renderUrlList(result.urls);
            urlCountSpan.textContent = result.urls.length;
        } else {
            showStatus(result.message, 'error');
        }
    })
    .catch(() => showStatus('Грешка при редактиране на URL адрес.', 'error'));
}

// ─── Събитие за добавяне чрез Enter ─────────────────────────────────
newUrlInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        addUrl();
    }
});

// ─── Събитие за бутоните ────────────────────────────────────────────
addUrlBtn.addEventListener('click', addUrl);
loadUrlBtn.addEventListener('click', loadSelectedUrl);
refreshUrlBtn.addEventListener('click', loadUrlList);

// ─── Изпращане на формата ───────────────────────────────────────────
form.addEventListener('submit', (event) => {
    event.preventDefault();

    // Нулиране на предишни резултати
    submitBtn.disabled = true;
    progressBar.style.width = '0%';
    progressBar.textContent = '0%';
    progressBarContainer.style.display = 'block';
    logDiv.innerHTML = '';
    logDiv.style.display = 'block';
    galleryDiv.innerHTML = '';
    progressBar.style.backgroundColor = '#4CAF50';

    const formData = new FormData(form);
    const params = new URLSearchParams(formData);

    // Създаваме EventSource връзка към нашия Flask endpoint
    const eventSource = new EventSource(`/download?${params.toString()}`);

    eventSource.onmessage = function(e) {
        try {
            const data = JSON.parse(e.data);

            // Обработка на съобщения от сървъра
            if (data.type === 'info' || data.type === 'error' || data.type === 'progress') {
                const logEntry = document.createElement('div');
                logEntry.textContent = data.message;
                logDiv.appendChild(logEntry);
                logDiv.scrollTop = logDiv.scrollHeight;
            }

            if (data.type === 'progress') {
                const percent = Math.round((data.current / data.total) * 100);
                progressBar.style.width = percent + '%';
                progressBar.textContent = percent + '%';
            }

            if (data.type === 'increment_info') {
                // Показваме информация за инкрементиране
                const logEntry = document.createElement('div');
                logEntry.className = 'increment-highlight';
                logEntry.textContent = '🔁 ' + data.message;
                logDiv.appendChild(logEntry);
                logDiv.scrollTop = logDiv.scrollHeight;

                // Автоматично обновяване на списъка
                loadUrlList();
            }

            if (data.type === 'complete') {
                eventSource.close();
                submitBtn.disabled = false;
                progressBar.textContent = 'Готово!';

                // Изчистване на скритото поле за url_index
                urlIndexHidden.value = '';

                // Проверка дали трябва да изчистим URL полето
                if (clearUrlCheckbox.checked) {
                    document.getElementById('url').value = '';
                }

                // Показваме галерията със свалените изображения
                const folder = formData.get('output_folder');
                data.files.forEach(file => {
                    const img = document.createElement('img');
                    img.src = `/view_image?folder=${encodeURIComponent(folder)}&file=${encodeURIComponent(file)}`;
                    galleryDiv.appendChild(img);
                });
            }

            if (data.type === 'error') {
                eventSource.close();
                submitBtn.disabled = false;
                progressBar.style.backgroundColor = '#dc3545';
                progressBar.textContent = 'Грешка!';
            }
        } catch (err) {
            console.error('Грешка при парсване на SSE данни:', err);
        }
    };

    eventSource.onerror = function(err) {
        console.error("EventSource failed:", err);
        logDiv.innerHTML += '<div>Грешка при връзката със сървъра.</div>';
        eventSource.close();
        submitBtn.disabled = false;
    };
});

// ─── Инициализация при зареждане ────────────────────────────────────
loadUrlList();

// ─── Проверка за обновления при старт ─────────────────────────────
checkForUpdatesOnLoad();

// ─── Update Notification Functions ─────────────────────────────────
let updateData = null;

async function checkForUpdatesOnLoad() {
    try {
        const response = await fetch('/api/version/check');
        const data = await response.json();

        if (data.has_update) {
            updateData = data.commit;
            showUpdateBanner(data.commit, data.message);
        }
    } catch (err) {
        console.error('Грешка при проверка за обновления:', err);
    }
}

function showUpdateBanner(commit, message) {
    const banner = document.getElementById('update-banner');
    const commitEl = document.getElementById('update-commit');
    const dateEl = document.getElementById('update-date');
    const messageEl = document.getElementById('update-message');

    // Показване на информация за commit-а
    if (commit) {
        commitEl.textContent = commit.sha ? commit.sha.substring(0, 8) : 'N/A';
        dateEl.textContent = commit.date ? new Date(commit.date).toLocaleString('bg-BG') : 'N/A';
        messageEl.textContent = commit.message || 'Няма информация';
    }

    // Показване на banner
    banner.style.display = 'block';
    document.body.classList.add('update-available');
}

function dismissUpdate() {
    const banner = document.getElementById('update-banner');
    banner.style.display = 'none';
    document.body.classList.remove('update-available');
    updateData = null;
}

async function performUpdate() {
    const banner = document.getElementById('update-banner');
    const statusEl = document.getElementById('update-status');
    const updateBtn = banner.querySelector('.btn-update');

    // Показвай loading състояние
    banner.classList.add('loading');
    updateBtn.disabled = true;
    statusEl.style.display = 'none';

    try {
        const response = await fetch('/api/version/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            statusEl.textContent = '✅ Обновяването е успешно! Страницата ще се презареди...';
            statusEl.className = 'update-message success';
            statusEl.style.display = 'block';

            // Забавяне преди презареждане
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } else {
            statusEl.textContent = '❌ Грешка при обновяване: ' + data.message;
            statusEl.className = 'update-message error';
            statusEl.style.display = 'block';

            // Възстанови бутона
            banner.classList.remove('loading');
            updateBtn.disabled = false;
        }
    } catch (err) {
        statusEl.textContent = '❌ Грешка при свързване със сървъра.';
        statusEl.className = 'update-message error';
        statusEl.style.display = 'block';

        banner.classList.remove('loading');
        updateBtn.disabled = false;
    }
}