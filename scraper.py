# scraper.py
import requests
import re
import os
import time
from datetime import datetime
import json
from url_manager import UrlManager

# --- HTTP client configuration ---
REQUEST_TIMEOUT = 30  # seconds: connection + read timeout
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Globalno set za sahranenie na istoriyata na sesiyata (izchistva se pri restart na servera)
SESSION_HISTORY = set()

# Globalen instans na UrlManager za inkrementirane
_url_manager = UrlManager('urls.json')


def download_images(url_list, iterations, output_folder, url_indices=None):
    """
    Priema spisak ot URL adresi i za vseki ot tyah svalya poreditsa ot izobrazheniya.
    Vrashta progresas chrez generator (yield).

    Args:
        url_list: Spisak ot URL adresi
        iterations: Broy iteratsii za vseki URL
        output_folder: Papka za zapis
        url_indices: (po izbor) Spisak ot indeksi na URL v spisaka za avtomatichno inkrementirane
    """
    if url_indices is None:
        url_indices = []

    # Sazdavane na papka, ako ne sashtestvuva
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    all_downloaded_files = []
    total_urls = len(url_list)
    has_downloaded_any = False  # Dali e svaleno pone edno izobrazhenie

    for index, start_url in enumerate(url_list):
        start_url = start_url.strip()
        if not start_url:
            continue

        # Proverka za istoriyata na sesiyata
        if start_url in SESSION_HISTORY:
            message = f"--- PROPUSKANE: URL adresat veche e obraboten v tazi sesiya: {start_url} ---"
            yield f"data: {json.dumps({'type': 'info', 'message': message})}\n\n"
            continue

        yield f"data: {json.dumps({'type': 'info', 'message': f'--- Obrabotka na URL {index + 1} ot {total_urls}: {start_url} ---'})}\n\n"

        # Izvikvane na logikata za edinichen URL
        for message in process_single_url(start_url, iterations, output_folder, all_downloaded_files):
            data = json.loads(message.replace('data: ', '').strip())
            if data.get('type') == 'progress':
                has_downloaded_any = True
            yield message

        # Dobavyame uspeshno obraboteniya URL v istoriyata
        SESSION_HISTORY.add(start_url)

    # Signal completion at the very end
    completion_message = f"Gotovo. Obshto svaleni failove ot vsichki adresi: {len(all_downloaded_files)}."
    print(completion_message)

    # Avtomatichno inkrementirane za vsichki indeksi ot spisaka (s broi napovtoreniya)
    if url_indices and has_downloaded_any:
        # Pribroqvame kolko pati se sreshta vseki indeks
        from collections import Counter
        index_counts = Counter(url_indices)

        for idx, count in index_counts.items():
            success, old_url, new_url = _url_manager.increment_url_by_count(idx, count)
            if success and new_url:
                increment_message = (
                    f"URL ot spisaka e inkrementiran s {count} stypki (index {idx}): {old_url} -> {new_url}"
                )
                print(increment_message)
                yield f"data: {json.dumps({'type': 'increment_info', 'url_index': idx, 'old_url': old_url, 'new_url': new_url, 'count': count, 'message': increment_message})}\n\n"
            elif old_url and not new_url:
                no_increment_message = (
                    f"URL ot spisaka ne mozhe da se inkrementira (nyama chislo v direktoriyata): {old_url}"
                )
                print(no_increment_message)
                yield f"data: {json.dumps({'type': 'info', 'message': no_increment_message})}\n\n"
    elif url_indices and not has_downloaded_any:
        skip_increment_message = (
            f"URL ot spisaka nqma da bude inkrementiran, zashtoto ne e svaleno nito edno izobrazhenie."
        )
        print(skip_increment_message)
        yield f"data: {json.dumps({'type': 'info', 'message': skip_increment_message})}\n\n"

    yield f"data: {json.dumps({'type': 'complete', 'message': completion_message, 'files': all_downloaded_files})}\n\n"


def process_single_url(start_url, iterations, output_folder, downloaded_files_list):
    downloaded_files = []

    # Razbivane na URL adresa
    # Primer: https://cdn.elitebabes.com/content/260332/0007-01_1200.jpg
    filename_with_ext = start_url.split('/')[-1]  # 0007-01_1200.jpg
    base_url_path = start_url.rsplit('/', 1)[0]   # https://cdn.elitebabes.com/content/260332

    filename, extension = os.path.splitext(filename_with_ext)  # 0007-01_1200, .jpg

    # Opit za namirane na modela za iteratsiya chrez Regex
    # Tarsim shablon: (Prefiks)-(Nomer)(Sufiks/Rezolyutsiya)
    # Za 0007-01_1200 tova e:
    # Group 1: 0007-
    # Group 2: 01
    # Group 3: _1200
    match = re.search(r'^(.*?-)(\d+)(_.*)$', filename)

    # Rezerven variant: Ako nyama dolna cherta (napr. image01.jpg)
    if not match:
        match = re.search(r'^(.*?)(\d+)$', filename)

    if not match:
        error_message = f"GRESHKA: Ne moga da razpoyana poreden nomer v URL: {start_url}"
        print(error_message)
        yield f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"
        return

    prefix = match.group(1)
    start_num_str = match.group(2)
    suffix = match.group(3) if len(match.groups()) > 2 else ""

    start_num = int(start_num_str)
    padding = len(start_num_str)  # Zapazvame dalzhinata za vodeshtite nuli (01 vs 1)

    initial_message = f"Zasichan shablon: {prefix}[{start_num_str}]{suffix}{extension}. Startirane na svalyane za {iterations} izobrazheniya..."
    print(f"-> {initial_message}")
    yield f"data: {json.dumps({'type': 'info', 'message': initial_message})}\n\n"

    for i in range(iterations):
        # Izchislyavane na tekushtiya nomer
        current_num = start_num + i
        current_num_str = str(current_num).zfill(padding)

        # Formirane na novoto ime i URL
        new_filename_base = f"{prefix}{current_num_str}{suffix}"
        new_full_filename = f"{new_filename_base}{extension}"
        current_url = f"{base_url_path}/{new_full_filename}"

        # Pauza za shtadene na servera
        time.sleep(0.5)

        try:
            response = requests.get(current_url, stream=True, timeout=REQUEST_TIMEOUT, headers=REQUEST_HEADERS)

            if response.status_code == 200:
                # Generirane na unikalna signatura za zapis
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                save_name = f"{new_filename_base}_{timestamp}{extension}"
                save_path = os.path.join(output_folder, save_name)

                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                message = f"[OK] Svalen: {save_name}"
                print(message)
                downloaded_files_list.append(save_name)
                # Yield progress
                yield f"data: {json.dumps({'type': 'progress', 'message': message, 'current': i + 1, 'total': iterations, 'file': save_name})}\n\n"

            elif response.status_code == 404:
                message = f"[404] Nyama izobrazhenie na adres: {current_url}. Spirane na tsikula."
                print(message)
                yield f"data: {json.dumps({'type': 'info', 'message': message})}\n\n"
                break  # Spirame, ako stignem kraya na galeriyata
            else:
                message = f"[Skip] Greshka {response.status_code} za {current_url}"
                print(message)
                yield f"data: {json.dumps({'type': 'info', 'message': message})}\n\n"

        except requests.exceptions.Timeout:
            message = f"[Timeout] Serverat ne otgovori v ramkite na {REQUEST_TIMEOUT} sekundi: {current_url}"
            print(message)
            yield f"data: {json.dumps({'type': 'error', 'message': message})}\n\n"

        except requests.exceptions.ConnectionError:
            message = f"[ConnectionError] Neuspeshna vrazka sus servera (proverete URL ili mrezhata): {current_url}"
            print(message)
            yield f"data: {json.dumps({'type': 'error', 'message': message})}\n\n"

        except requests.exceptions.RequestException as e:
            message = f"[Error] Mrezhova greshka pri {current_url}: {e}"
            print(message)
            yield f"data: {json.dumps({'type': 'error', 'message': message})}\n\n"