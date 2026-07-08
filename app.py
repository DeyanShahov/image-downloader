# app.py
from flask import Flask, render_template, request, Response, send_from_directory, jsonify
import os, json, re
from scraper import download_images
from url_manager import UrlManager
from version_checker import start_background_update_check, perform_update

app = Flask(__name__)

# Конфигурация
STATIC_FOLDER = 'static'

# Проверка дали urls.json съществува
if not os.path.exists('urls.json'):
    print("[INFO] urls.json not found. Creating empty database...")
    with open('urls.json', 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2, ensure_ascii=False)
    print("[OK] Empty urls.json created.")

# Инициализация на мениджъра за URL адреси
url_manager = UrlManager('urls.json')
urls_count = len(url_manager.load_urls())

if urls_count == 0 and not os.path.exists('urls.json'):
    print(f"[OK] urls.json initialized (empty database).")
else:
    print(f"[OK] urls.json loaded with {urls_count} URL(s).")


# ─── API endpoints за управление на URL списъка ────────────────────────────


@app.route('/api/urls', methods=['GET'])
def api_get_urls():
    """Връща списъка с всички URL адреси."""
    urls = url_manager.load_urls()
    return jsonify({'urls': urls, 'count': len(urls)})


@app.route('/api/urls/add', methods=['POST'])
def api_add_url():
    """Добавя нов URL адрес в списъка."""
    data = request.get_json(silent=True)
    if not data or 'url' not in data:
        return jsonify({'success': False, 'message': 'Липсва URL адрес.'})

    success, message = url_manager.add_url(data['url'])
    urls = url_manager.load_urls()
    return jsonify({'success': success, 'message': message, 'urls': urls})


@app.route('/api/urls/delete', methods=['POST'])
def api_delete_url():
    """Изтрива URL адрес на посочената позиция."""
    data = request.get_json(silent=True)
    if not data or 'index' not in data:
        return jsonify({'success': False, 'message': 'Липсва индекс.'})

    success, message = url_manager.delete_url(int(data['index']))
    urls = url_manager.load_urls()
    return jsonify({'success': success, 'message': message, 'urls': urls})


@app.route('/api/urls/update', methods=['POST'])
def api_update_url():
    """Променя URL адрес на посочената позиция."""
    data = request.get_json(silent=True)
    if not data or 'index' not in data or 'url' not in data:
        return jsonify({'success': False, 'message': 'Липсват индекс и URL адрес.'})

    success, message = url_manager.update_url(int(data['index']), data['url'])
    urls = url_manager.load_urls()
    return jsonify({'success': success, 'message': message, 'urls': urls})


# ─── API endpoints за версия и обновления ──────────────────────────────────


@app.route('/api/version/check')
def api_check_version():
    """Проверява дали има налична обновена версия."""
    from version_checker import check_for_updates
    has_update, github_commit, message = check_for_updates()
    return jsonify({
        'has_update': has_update,
        'commit': github_commit,
        'message': message
    })


@app.route('/api/version/update', methods=['POST'])
def api_update():
    """Стартира процеса на обновяване."""
    success, message = perform_update()
    return jsonify({'success': success, 'message': message})


# ─── Основен маршрут и download ────────────────────────────────────────────


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/download', methods=['GET'])
def download():
    raw_urls = request.args.get('url')
    iterations = request.args.get('iterations')
    folder_name = request.args.get('output_folder')
    url_index = request.args.get('url_index')  # По избор, от списъка

    if not raw_urls or not iterations or not folder_name:
        def error_generator():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Липсват параметри (URL, итерации или папка).'})}\n\n"
        return Response(error_generator(), mimetype='text/event-stream')

    # Разделяне на входния низ на списък от URL адреси
    url_list = [u for u in re.split(r'[,\s\n;]+', raw_urls) if u]

    # Проверка дали потребителят е въвел абсолютен път или релативен
    if os.path.isabs(folder_name):
        full_output_path = folder_name
    else:
        full_output_path = os.path.join(STATIC_FOLDER, folder_name)

    # Конвертиране на url_index към списък от индекси
    # Вземаме ВСИЧКИ стойности (вкл. дублиращи се) от form-data
    url_indices = []
    if url_index:
        # Ако е подадено като запетаи разделен низ
        url_indices = [int(i) for i in url_index.split(',') if i.strip().isdigit()]
    else:
        # Опит да вземем всички стойности от query параметри (за duplicate индекси)
        all_indices = request.args.getlist('url_index')
        if all_indices:
            url_indices = [int(i) for i in all_indices if i.strip().isdigit()]

    # Връщаме Response, който стриймва резултатите от генератора
    return Response(
        download_images(url_list, int(iterations), full_output_path, url_indices=url_indices),
        mimetype='text/event-stream'
    )


@app.route('/api/urls/increment', methods=['POST'])
def api_increment_url():
    """JSON endpoint за инкрементиране на URL с брой повторения."""
    data = request.get_json(force=True)
    index = data.get('index')
    count = data.get('count', 1)

    if index is None or not isinstance(index, int):
        return jsonify({'success': False, 'message': 'Невалиден индекс.'})

    success, old_url, new_url = url_manager.increment_url_by_count(index, count)

    if success:
        return jsonify({
            'success': True,
            'message': f'URL инкрементиран с {count} стъпки: {old_url} → {new_url}',
            'old_url': old_url,
            'new_url': new_url
        })
    else:
        return jsonify({
            'success': False,
            'message': f'Неуспешно инкрементиране за индекс {index}.',
            'old_url': old_url,
            'new_url': new_url
        })


@app.route('/view_image')
def view_image():
    """Помощен маршрут за показване на изображения от произволни папки"""
    folder = request.args.get('folder')
    filename = request.args.get('file')

    if not folder or not filename:
        return "Missing arguments", 400

    directory = folder
    if not os.path.isabs(folder):
        directory = os.path.join(app.root_path, STATIC_FOLDER, folder)

    return send_from_directory(directory, filename)


if __name__ == '__main__':
    # Стартирай проверка за обновления в background прилагане
    # Не блокира старта на приложението
    def on_update_available(github_commit, message):
        # Тук може да се добави логика за показване на известие в UI
        # За момента само логваме
        print(f"\n{'='*60}")
        print(f"[UPDATE] НАЛИЧНО ОБНОВЛЕНИЕ")
        print(f"[UPDATE] {message}")
        print(f"[UPDATE] Отворете / за да видите повече информация")
        print(f"{'='*60}\n")
    
    def on_check_complete(has_update, message):
        pass  # Може да се използва за логика след проверка
    
    # Стартирай проверка в background thread
    start_background_update_check(on_update_available, on_check_complete)
    
    print("[INFO] Стартиране на Flask приложението...")
    app.run(debug=True, use_reloader=False)
