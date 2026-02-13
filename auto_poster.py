#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║      AUTO POSTER GENERATOR  v5.0 – FINAL                    ║
║  Direct URL parsing + Cloudflare + automobile-catalog.com   ║
╚══════════════════════════════════════════════════════════════╝
"""

import argparse
import io
import json
import logging
import os
import pickle
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ═══════════════════════════════════════════════════════════════════════════
#  НАСТРОЙКА ЛОГИРОВАНИЯ
# ═══════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-7s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("poster")

# ═══════════════════════════════════════════════════════════════════════════
#  КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════
BASE_URL = "https://www.automobile-catalog.com"
COOKIES_FILE = Path("cookies_selenium.pkl")
REMOVEBG_API_KEY = os.getenv("REMOVEBG_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")

# Страны производителей
BRAND_COUNTRIES = {
    "audi": "GERMANY", "bmw": "GERMANY", "mercedes": "GERMANY", "mercedes-benz": "GERMANY",
    "porsche": "GERMANY", "volkswagen": "GERMANY", "vw": "GERMANY", "opel": "GERMANY",
    "toyota": "JAPAN", "honda": "JAPAN", "nissan": "JAPAN", "mazda": "JAPAN",
    "lexus": "JAPAN", "subaru": "JAPAN", "mitsubishi": "JAPAN",
    "ford": "USA", "chevrolet": "USA", "tesla": "USA", "dodge": "USA", "cadillac": "USA",
    "ferrari": "ITALY", "lamborghini": "ITALY", "alfa romeo": "ITALY", "maserati": "ITALY",
    "peugeot": "FRANCE", "renault": "FRANCE", "bugatti": "FRANCE", "citroen": "FRANCE",
    "jaguar": "UK", "aston martin": "UK", "bentley": "UK", "rolls-royce": "UK", "land rover": "UK",
    "hyundai": "SOUTH KOREA", "kia": "SOUTH KOREA", "genesis": "SOUTH KOREA",
    "volvo": "SWEDEN", "koenigsegg": "SWEDEN", "saab": "SWEDEN",
}

# Fallback база (только для дополнения недостающих данных!)
FALLBACK_DB = {
    "bmw m4": {
        "model": "BMW M4", "engine": "3.0L TwinTurbo", "power": "503 HP",
        "torque": "650 Nm", "acceleration": "3.5 s", "top_speed": "250 km/h",
        "weight": "1725 kg", "year": "2021-2024", "country": "GERMANY"
    },
    "bmw m3": {
        "model": "BMW M3", "engine": "3.0L TwinTurbo", "power": "510 HP",
        "torque": "650 Nm", "acceleration": "3.4 s", "top_speed": "250 km/h",
        "weight": "1730 kg", "year": "2021-2024", "country": "GERMANY"
    },
    "porsche 911": {
        "model": "Porsche 911", "engine": "3.0L Twin-Turbo", "power": "379 HP",
        "torque": "450 Nm", "acceleration": "4.2 s", "top_speed": "293 km/h",
        "weight": "1505 kg", "year": "2019-2024", "country": "GERMANY"
    },
    "audi tt rs": {
        "model": "Audi TT RS", "engine": "2.5L TFSI", "power": "394 HP",
        "torque": "480 Nm", "acceleration": "3.7 s", "top_speed": "250 km/h",
        "weight": "1450 kg", "year": "2016-2023", "country": "GERMANY"
    },
    "ferrari 488": {
        "model": "Ferrari 488 GTB", "engine": "3.9L TwinTurbo V8", "power": "661 HP",
        "torque": "760 Nm", "acceleration": "3.0 s", "top_speed": "330 km/h",
        "weight": "1475 kg", "year": "2015-2019", "country": "ITALY"
    },
}

# ═══════════════════════════════════════════════════════════════════════════
#  ASCII БАННЕР
# ═══════════════════════════════════════════════════════════════════════════
_BANNER = [
    r"    ██████  ▄████▄   ██▀███   ▄▄▄       ██▓███  ▓█████  ██▀███     ",
    r"▒██    ▒ ▒██▀ ▀█  ▓██ ▒ ██▒▒████▄    ▓██░  ██▒▓█   ▀ ▓██ ▒ ██▒   ",
    r"░ ▓██▄   ▒▓█    ▄ ▓██ ░▄█ ▒▒██  ▀█▄  ▓██░ ██▓▒▒███   ▓██ ░▄█ ▒   ",
    r"  ▒   ██▒▒▓▓▄ ▄██▒▒██▀▀█▄  ░██▄▄▄▄██ ▒██▄█▓▒ ▒▒▓█  ▄ ▒██▀▀█▄     ",
    r"▒██████▒▒▒ ▓███▀ ░░██▓ ▒██▒ ▓█   ▓██▒▒██▒ ░  ░░▒████▒░██▓ ▒██▒   ",
    r"▒ ▒▓▒ ▒ ░░ ░▒ ▒  ░░ ▒▓ ░▒▓░ ▒▒   ▓▒█░▒▓▒░ ░  ░░░ ▒░ ░░ ▒▓ ░▒▓░   ",
    r"░ ░▒  ░ ░  ░  ▒     ░▒ ░ ▒░  ▒   ▒▒ ░░▒ ░      ░ ░  ░  ░▒ ░ ▒░   ",
    r"░  ░  ░  ░          ░░   ░   ░   ▒   ░░          ░     ░░   ░    ",
    r"      ░  ░ ░         ░           ░  ░            ░  ░   ░        ",
    r"         ░                                                       ",
    r"                                                                 ",
    r"                  AUTO POSTER GENERATOR                           ",
]

def print_banner():
    """Вывод ASCII баннера с градиентом."""
    n = len(_BANNER)
    for i, line in enumerate(_BANNER):
        g = int(128 * i / (n - 1)) if n > 1 else 128
        color = f"\033[38;2;255;{g};0m"
        reset = "\033[0m"
        print(f"{color}{line}{reset}")
    print()


# ═══════════════════════════════════════════════════════════════════════════
#  WEB SCRAPER
# ═══════════════════════════════════════════════════════════════════════════
class AutoCatalogScraper:
    def __init__(self):
        self.driver = None
        self.cookies_file = COOKIES_FILE
        
    def init_driver(self):
        log.info("Initializing ChromeDriver...")
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        self.driver = uc.Chrome(options=options, version_main=None)
        self.driver.maximize_window()
        
        if self.cookies_file.exists():
            log.info(f"Loading saved cookies from {self.cookies_file}")
            try:
                self.driver.get(BASE_URL)
                time.sleep(2)
                
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        try:
                            self.driver.add_cookie(cookie)
                        except Exception as e:
                            log.debug(f"Could not add cookie: {e}")
                
                self.driver.refresh()
                log.info("Cookies loaded successfully")
            except Exception as e:
                log.warning(f"Could not load cookies: {e}")
        
        return self.driver
    
    def save_cookies(self):
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            log.info(f"Cookies saved to {self.cookies_file}")
        except Exception as e:
            log.error(f"Failed to save cookies: {e}")
    
    def wait_for_cloudflare(self, max_wait=300):
        log.info("Checking for Cloudflare challenge...")
        
        start_time = time.time()
        cloudflare_detected = False
        
        while time.time() - start_time < max_wait:
            try:
                page_source = self.driver.page_source.lower()
                title = self.driver.title.lower()
                
                if any(keyword in page_source or keyword in title for keyword in 
                       ['cloudflare', 'checking your browser', 'just a moment', 
                        'verify you are human', 'security check']):
                    
                    if not cloudflare_detected:
                        cloudflare_detected = True
                        log.warning("CLOUDFLARE DETECTED!")
                        log.warning("=" * 70)
                        log.warning("  Please complete the CAPTCHA in the browser window")
                        log.warning("  Waiting for you to pass the verification...")
                        log.warning("  This only needs to be done ONCE - cookies will be saved!")
                        log.warning("=" * 70)
                    
                    elapsed = int(time.time() - start_time)
                    remaining = max_wait - elapsed
                    print(f"\r  Waiting... {elapsed}s elapsed, {remaining}s remaining", end='', flush=True)
                    time.sleep(3)
                    continue
                
                if cloudflare_detected:
                    print()
                    log.info("Cloudflare challenge passed!")
                    self.save_cookies()
                    time.sleep(2)
                    return True
                else:
                    log.info("No Cloudflare challenge detected")
                    return True
                    
            except Exception as e:
                log.error(f"Error checking Cloudflare: {e}")
                time.sleep(2)
        
        if cloudflare_detected:
            print()
            log.error("Cloudflare timeout")
            return False
        
        return True
    
    def search_car(self, brand: str, model: str = "") -> List[Dict]:
        try:
            if not self.driver:
                self.init_driver()
            
            log.info(f"Searching for: {brand} {model}")
            
            brand_slug = brand.lower().replace(' ', '-')
            list_url = f"{BASE_URL}/list-{brand_slug}.html"
            
            log.info(f"Opening brand list: {list_url}")
            self.driver.get(list_url)
            
            if not self.wait_for_cloudflare():
                log.error("Failed to bypass Cloudflare")
                return []
            
            time.sleep(3)
            
            results = self._parse_model_list(model)
            
            if results:
                log.info(f"Found {len(results)} models")
                for i, r in enumerate(results[:5]):
                    log.info(f"  {i+1}. {r['name']}")
            else:
                log.warning("No models found on list page")
            
            return results
            
        except Exception as e:
            log.error(f"Search failed: {e}")
            return []
    
    def _parse_model_list(self, model_query: str = "") -> List[Dict]:
        results = []
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            model_links = []
            
            for a in soup.find_all('a', href=re.compile(r'/model/\w+/[\w\-_]+')):
                model_links.append(a)
            
            for a in soup.find_all('a', href=re.compile(r'/car/\d+/\w+/[\w\-_]+')):
                model_links.append(a)
            
            for a in soup.find_all('a', href=True):
                href = a.get('href', '')
                if '/car/' in href or '/model/' in href:
                    if a not in model_links:
                        model_links.append(a)
            
            seen_urls = set()
            for link in model_links:
                href = link.get('href', '')
                if not href or href in seen_urls:
                    continue
                
                if any(skip in href for skip in ['#', 'javascript:', 'mailto:', '.css', '.js']):
                    continue
                
                full_url = urljoin(BASE_URL, href)
                text = link.get_text(strip=True)
                
                if not text:
                    text = link.get('title', '') or link.get('alt', '')
                
                if text and len(text) > 2:
                    results.append({
                        'name': text,
                        'url': full_url
                    })
                    seen_urls.add(href)
            
            if model_query:
                model_lower = model_query.lower()
                exact_matches = [r for r in results if model_lower in r['name'].lower()]
                other_matches = [r for r in results if model_lower not in r['name'].lower()]
                results = exact_matches + other_matches
            
            return results[:20]
            
        except Exception as e:
            log.error(f"Error parsing model list: {e}")
            return []
    
    def parse_specs(self, url: str) -> Dict:
        try:
            log.info(f"Parsing specs from: {url}")
            self.driver.get(url)
            time.sleep(4)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            specs = {}
            
            h1 = soup.find('h1')
            if h1:
                model_name = h1.get_text(strip=True)
                model_name = re.sub(r'\s*specifications:.*', '', model_name, flags=re.IGNORECASE)
                model_name = re.sub(r'\s*versions\s*&\s*types.*', '', model_name, flags=re.IGNORECASE)
                model_name = re.sub(r'\s*data\s*and.*', '', model_name, flags=re.IGNORECASE)
                specs['model'] = model_name.strip()
                log.info(f"Model name: {specs['model']}")
            
            page_text = soup.get_text()
            
            # Парсинг характеристик (те же regex что и раньше)
            engine_patterns = [
                (r'(\d+\.?\d*\s*(?:L|l)\s+(?:V\d+|inline|boxer|turbo|twin[\s-]?turbo|bi[\s-]?turbo|TFSI|TSI)?[\w\s-]*)', 'full'),
                (r'(\d+\.?\d*\s*cm3)', 'cm3'),
                (r'(\d+\.?\d*L?\s+(?:TFSI|TSI|TDI|FSI))', 'tech'),
            ]
            
            for pattern, ptype in engine_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    engine_text = matches[0].strip() if isinstance(matches[0], str) else matches[0][0].strip()
                    engine_text = re.sub(r'\s+', ' ', engine_text)
                    specs['engine'] = engine_text
                    log.info(f"Found engine: {engine_text}")
                    break
            
            power_patterns = [r'(\d+)\s*(?:hp|HP|ps|PS)', r'power[:\s]+(\d+)\s*hp']
            for pattern in power_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    specs['power'] = f"{match.group(1)} HP"
                    log.info(f"Found power: {specs['power']}")
                    break
            
            torque_patterns = [r'(\d+)\s*(?:Nm|nm)', r'torque[:\s]+(\d+)\s*nm']
            for pattern in torque_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    specs['torque'] = f"{match.group(1)} Nm"
                    log.info(f"Found torque: {specs['torque']}")
                    break
            
            accel_patterns = [
                r'(\d+\.?\d*)\s*s(?:ec)?.*?(?:0[\s-]?100|hundred)',
                r'0[\s-]?100[^\d]*(\d+\.?\d*)\s*s',
            ]
            for pattern in accel_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    accel_val = match.group(1)
                    try:
                        if 2.0 <= float(accel_val) <= 15.0:
                            specs['acceleration'] = f"{accel_val} s"
                            log.info(f"Found acceleration: {specs['acceleration']}")
                            break
                    except:
                        continue
            
            speed_patterns = [
                r'(\d+)\s*km/h.*?(?:top|max).*?speed',
                r'(?:top|max)\s*speed[^\d]*(\d+)\s*km/h',
            ]
            for pattern in speed_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    speed_val = match.group(1)
                    try:
                        if 100 <= int(speed_val) <= 500:
                            specs['top_speed'] = f"{speed_val} km/h"
                            log.info(f"Found top speed: {specs['top_speed']}")
                            break
                    except:
                        continue
            
            weight_patterns = [
                r'(\d+)\s*kg.*?(?:weight|mass)',
                r'(?:weight|mass)[^\d]*(\d+)\s*kg',
            ]
            for pattern in weight_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    weight_val = match.group(1)
                    try:
                        if 800 <= int(weight_val) <= 3000:
                            specs['weight'] = f"{weight_val} kg"
                            log.info(f"Found weight: {specs['weight']}")
                            break
                    except:
                        continue
            
            year_patterns = [
                r'(20\d{2})\s*[-–—]\s*(20\d{2})',
                r'(19\d{2})\s*[-–—]\s*(20\d{2})',
            ]
            for pattern in year_patterns:
                match = re.search(pattern, page_text)
                if match:
                    specs['year'] = f"{match.group(1)}-{match.group(2)}"
                    log.info(f"Found year: {specs['year']}")
                    break
            
            extracted_count = sum(1 for k, v in specs.items() if k in ['engine', 'power', 'torque', 'acceleration', 'top_speed', 'weight', 'year'])
            log.info(f"Extracted {extracted_count}/7 specifications")
            
            return specs
            
        except Exception as e:
            log.error(f"Failed to parse specs: {e}")
            return {}
    
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                log.info("Browser closed")
            except:
                pass


# ═══════════════════════════════════════════════════════════════════════════
#  ПОЛУЧЕНИЕ ФОТО
# ═══════════════════════════════════════════════════════════════════════════
class ImageFetcher:
    def get(self, brand: str, model: str) -> Optional[Image.Image]:
        try:
            if not UNSPLASH_ACCESS_KEY:
                log.warning("No Unsplash API key")
                return None
            
            query = f"{brand} {model} car".strip()
            log.info(f"Fetching image from Unsplash: {query}")
            
            search_url = "https://api.unsplash.com/search/photos"
            params = {'query': query, 'per_page': 1, 'orientation': 'landscape'}
            headers = {'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'}
            
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    photo_url = data['results'][0]['urls']['regular']
                    log.info(f"Found image: {photo_url}")
                    
                    img_response = requests.get(photo_url, timeout=10)
                    if img_response.status_code == 200:
                        img = Image.open(io.BytesIO(img_response.content))
                        log.info("Image downloaded successfully")
                        
                        # ВСЕГДА вызываем remove.bg!
                        return self.remove_background(img)
                    
            log.warning("Could not fetch image from Unsplash")
            return None
            
        except Exception as e:
            log.error(f"Image fetch error: {e}")
            return None
    
    def remove_background(self, img: Image.Image) -> Image.Image:
        """Удаление фона через remove.bg API."""
        try:
            if not REMOVEBG_API_KEY:
                log.warning("No remove.bg API key, using original image")
                return img.convert("RGBA")
            
            log.info("Removing background via remove.bg API...")
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': buffer},
                data={'size': 'auto'},
                headers={'X-Api-Key': REMOVEBG_API_KEY},
                timeout=30
            )
            
            if response.status_code == 200:
                log.info("Background removed successfully!")
                return Image.open(io.BytesIO(response.content)).convert("RGBA")
            else:
                log.warning(f"Remove.bg failed with status {response.status_code}")
                if response.status_code == 403:
                    log.warning("API key may be invalid or credits exhausted")
                log.warning(f"Response: {response.text[:200]}")  # Первые 200 символов
                log.warning("Using original image without background removal")
                return img.convert("RGBA")
                
        except Exception as e:
            log.error(f"Background removal error: {e}")
            log.warning("Using original image without background removal")
            return img.convert("RGBA") if img.mode != 'RGBA' else img


# ═══════════════════════════════════════════════════════════════════════════
#  ГЕНЕРАЦИЯ ПОСТЕРА (PIXEL-PERFECT ПО РЕФЕРЕНСУ!)
# ═══════════════════════════════════════════════════════════════════════════
class PosterGenerator:
    # Canvas размеры
    WIDTH = 800
    HEIGHT = 1200
    
    # Layout сетка
    MARGIN_LEFT = 60
    TOP_OFFSET = 50
    BRAND_MODEL_GAP = 10
    
    # Цвета (RGB)
    BRAND_COLOR = (140, 140, 140)     # Серый для бренда
    TEXT_COLOR = (0, 0, 0)            # Черный для текста
    CAR_BG_COLOR = (225, 225, 225)    # Светло-серый фон за машиной
    LINE_COLOR = (150, 150, 150)      # Серый для линий
    FLAG_BORDER = (200, 200, 200)     # Серая рамка флага
    
    # Серый блок под машину — полная ширина как в референсе
    CAR_BG_WIDTH_PERCENT = 1.0        # 100% ширины canvas
    CAR_BG_HEIGHT_PERCENT = 0.38      # 38% высоты canvas
    
    # Характеристики — вычисляются динамически в generate()
    LINE_HEIGHT = 46
    COLUMN_GAP = 20
    DIVIDER_OFFSET = 30               # Отступ от вертикальной линии
    
    # Флаг
    FLAG_WIDTH = 50
    FLAG_HEIGHT = 35
    
    def __init__(self):
        self.font_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        self.font_path_regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    
    def draw_text_with_tracking(self, draw, text: str, x: int, y: int, 
                                font, color, tracking: int = 0):
        """Рисует текст с letter spacing (tracking)."""
        current_x = x
        for char in text:
            draw.text((current_x, y), char, fill=color, font=font)
            bbox = font.getbbox(char)
            char_width = bbox[2] - bbox[0]
            current_x += char_width + tracking
        return current_x
    
    def auto_fit_text(self, draw, text: str, font_path: str, 
                     max_width: int, start_size: int) -> ImageFont.FreeTypeFont:
        """Автоматически подбирает размер шрифта чтобы текст влез."""
        size = start_size
        while size > 20:  # Минимальный размер 20px
            try:
                font = ImageFont.truetype(font_path, size)
                bbox = font.getbbox(text)
                width = bbox[2] - bbox[0]
                if width <= max_width:
                    return font
                size -= 2
            except:
                return ImageFont.load_default()
        try:
            return ImageFont.truetype(font_path, 20)
        except:
            return ImageFont.load_default()
    
    def draw_flag(self, draw, country: str, x: int, y: int):
        """Рисует флаг страны с рамкой."""
        w, h = self.FLAG_WIDTH, self.FLAG_HEIGHT
        
        # Рамка
        draw.rectangle([(x, y), (x + w, y + h)], outline=self.FLAG_BORDER, width=1)
        
        if country == "GERMANY":
            # Немецкий: черный-красный-золотой (горизонтальные полосы)
            stripe_h = h // 3
            draw.rectangle([(x, y), (x + w, y + stripe_h)], fill=(0, 0, 0))
            draw.rectangle([(x, y + stripe_h), (x + w, y + stripe_h * 2)], fill=(221, 0, 0))
            draw.rectangle([(x, y + stripe_h * 2), (x + w, y + h)], fill=(255, 206, 0))
            
        elif country == "JAPAN":
            # Японский: белый с красным кругом
            draw.rectangle([(x + 1, y + 1), (x + w - 1, y + h - 1)], fill=(255, 255, 255))
            center_x = x + w // 2
            center_y = y + h // 2
            radius = min(w, h) // 3
            draw.ellipse([
                (center_x - radius, center_y - radius),
                (center_x + radius, center_y + radius)
            ], fill=(188, 0, 45))
            
        elif country == "ITALY":
            # Итальянский: зеленый-белый-красный (вертикальные полосы)
            stripe_w = w // 3
            draw.rectangle([(x, y), (x + stripe_w, y + h)], fill=(0, 146, 70))
            draw.rectangle([(x + stripe_w, y), (x + stripe_w * 2, y + h)], fill=(241, 242, 241))
            draw.rectangle([(x + stripe_w * 2, y), (x + w, y + h)], fill=(206, 43, 55))
            
        elif country == "USA":
            # Американский: упрощенная версия (полосы + синий квадрат)
            stripe_h = h // 7
            for i in range(7):
                color = (178, 34, 52) if i % 2 == 0 else (255, 255, 255)
                draw.rectangle([
                    (x, y + i * stripe_h),
                    (x + w, y + (i + 1) * stripe_h)
                ], fill=color)
            # Синий квадрат
            canton_w = int(w * 0.4)
            canton_h = int(h * 0.5)
            draw.rectangle([
                (x, y),
                (x + canton_w, y + canton_h)
            ], fill=(60, 59, 110))
            
        elif country == "FRANCE":
            # Французский: синий-белый-красный
            stripe_w = w // 3
            draw.rectangle([(x, y), (x + stripe_w, y + h)], fill=(0, 35, 149))
            draw.rectangle([(x + stripe_w, y), (x + stripe_w * 2, y + h)], fill=(255, 255, 255))
            draw.rectangle([(x + stripe_w * 2, y), (x + w, y + h)], fill=(237, 41, 57))
            
        elif country == "UK":
            # Британский: упрощенный Union Jack
            draw.rectangle([(x + 1, y + 1), (x + w - 1, y + h - 1)], fill=(1, 33, 105))
            # Белый крест
            cross_w = max(2, w // 10)
            draw.rectangle([
                (x + w // 2 - cross_w // 2, y),
                (x + w // 2 + cross_w // 2, y + h)
            ], fill=(255, 255, 255))
            draw.rectangle([
                (x, y + h // 2 - cross_w // 2),
                (x + w, y + h // 2 + cross_w // 2)
            ], fill=(255, 255, 255))
            # Красный крест
            cross_w_red = max(1, w // 15)
            draw.rectangle([
                (x + w // 2 - cross_w_red // 2, y),
                (x + w // 2 + cross_w_red // 2, y + h)
            ], fill=(200, 16, 46))
            draw.rectangle([
                (x, y + h // 2 - cross_w_red // 2),
                (x + w, y + h // 2 + cross_w_red // 2)
            ], fill=(200, 16, 46))
    
    def generate(self, specs: Dict, photo: Optional[Image.Image], output: str):
        """Генерирует постер с pixel-perfect дизайном по референсу."""
        try:
            log.info("Generating poster...")
            
            # Canvas
            canvas = Image.new('RGB', (self.WIDTH, self.HEIGHT), 'white')
            draw = ImageDraw.Draw(canvas)
            
            # ============ 1. ВЕРХНИЙ БЛОК: БРЕНД И МОДЕЛЬ ============
            
            # Парсим название
            model_full = specs.get('model', 'CAR MODEL')
            parts = model_full.split()
            brand = parts[0].upper() if parts else 'BRAND'
            model = ' '.join(parts[1:]).upper() if len(parts) > 1 else 'MODEL'
            
            # Шрифт для бренда — средний серый, как в референсе
            try:
                font_brand = ImageFont.truetype(self.font_path_bold, 80)
            except:
                font_brand = ImageFont.load_default()
            
            # Рисуем бренд с tracking +4px
            brand_y = self.TOP_OFFSET
            brand_end_x = self.draw_text_with_tracking(
                draw, brand, self.MARGIN_LEFT, brand_y,
                font_brand, self.BRAND_COLOR, tracking=4
            )
            brand_height = font_brand.getbbox(brand)[3] - font_brand.getbbox(brand)[1]
            
            # Шрифт для модели (auto-fit если длинная) — крупнее бренда, черный
            model_y = brand_y + brand_height + self.BRAND_MODEL_GAP
            max_model_width = self.WIDTH - self.MARGIN_LEFT * 2
            font_model = self.auto_fit_text(
                draw, model, self.font_path_bold, max_model_width, 72
            )
            draw.text((self.MARGIN_LEFT, model_y), model, fill=self.TEXT_COLOR, font=font_model)
            model_height = font_model.getbbox(model)[3] - font_model.getbbox(model)[1]
            
            # ============ 2. СЕРЫЙ БЛОК + ФОТО МАШИНЫ ============
            
            # Серый блок начинается сразу после заголовка с небольшим отступом
            car_bg_top_gap = 30
            car_bg_y = model_y + model_height + car_bg_top_gap
            
            # Блок — полная ширина (как в референсе)
            car_bg_width = self.WIDTH
            car_bg_height = int(self.HEIGHT * self.CAR_BG_HEIGHT_PERCENT)
            car_bg_x = 0
            
            # Рисуем серый блок
            draw.rectangle([
                (car_bg_x, car_bg_y),
                (car_bg_x + car_bg_width, car_bg_y + car_bg_height)
            ], fill=self.CAR_BG_COLOR)
            
            # Вставляем фото машины (если есть)
            if photo:
                # Внутренний отступ 5% с каждой стороны
                inner_pad_x = int(car_bg_width * 0.05)
                inner_pad_y = int(car_bg_height * 0.05)
                max_photo_width  = car_bg_width  - 2 * inner_pad_x
                max_photo_height = car_bg_height - 2 * inner_pad_y
                
                # Resize с сохранением пропорций
                photo.thumbnail((max_photo_width, max_photo_height), Image.Resampling.LANCZOS)
                
                # Центрируем фото внутри серого блока
                photo_x = car_bg_x + (car_bg_width  - photo.width)  // 2
                photo_y = car_bg_y + (car_bg_height - photo.height) // 2
                
                if photo.mode == 'RGBA':
                    canvas.paste(photo, (photo_x, photo_y), photo)
                else:
                    canvas.paste(photo, (photo_x, photo_y))
            
            # ============ 3. НИЖНИЙ БЛОК: ГОД + ХАРАКТЕРИСТИКИ ============
            
            # Старт характеристик — фиксированный отступ от нижнего края серого блока
            specs_gap = 55
            specs_start_y = car_bg_y + car_bg_height + specs_gap
            
            # Шрифты — соответствуют референсу (небольшие, чёткие)
            try:
                font_year_label = ImageFont.truetype(self.font_path_bold, 26)
                font_year_value = ImageFont.truetype(self.font_path_regular, 18)
                font_spec_label = ImageFont.truetype(self.font_path_bold, 20)
                font_spec_value = ImageFont.truetype(self.font_path_regular, 20)
            except:
                font_year_label = font_year_value = ImageFont.load_default()
                font_spec_label = font_spec_value = ImageFont.load_default()
            
            # --- Колонка ГОД (крайняя левая) ---
            year = specs.get('year', 'N/A')
            year_col_x = self.MARGIN_LEFT
            
            draw.text((year_col_x, specs_start_y), "YEAR", fill=self.TEXT_COLOR, font=font_year_label)
            draw.text((year_col_x, specs_start_y + 32), year, fill=self.TEXT_COLOR, font=font_year_value)
            
            # Вертикальная разделительная линия
            divider_x = year_col_x + 145          # Фиксированная позиция, не зависит от шрифта
            divider_y_start = specs_start_y - 5
            divider_y_end   = specs_start_y + 4 * self.LINE_HEIGHT + 10
            draw.line(
                [(divider_x, divider_y_start), (divider_x, divider_y_end)],
                fill=self.LINE_COLOR, width=2
            )
            
            # --- Левая колонка характеристик ---
            left_specs = [
                ("Engine", specs.get('engine', 'N/A')),
                ("Power",  specs.get('power',  'N/A')),
                ("Torque", specs.get('torque', 'N/A')),
                ("Weight", specs.get('weight', 'N/A')),
            ]
            left_col_label_x = divider_x + self.DIVIDER_OFFSET
            max_left_label_w = max(
                font_spec_label.getbbox(lbl)[2] - font_spec_label.getbbox(lbl)[0]
                for lbl, _ in left_specs
            )
            left_col_value_x = left_col_label_x + max_left_label_w + self.COLUMN_GAP

            # --- Правая колонка — вычисляем СНАЧАЛА, начиная с правого края ---
            right_specs = [
                ("0-100 km/h", specs.get('acceleration', 'N/A')),
                ("Top speed",  specs.get('top_speed',    'N/A')),
            ]
            max_right_label_w = max(
                font_spec_label.getbbox(lbl)[2] - font_spec_label.getbbox(lbl)[0]
                for lbl, _ in right_specs
            )
            max_right_value_w = max(
                font_spec_value.getbbox(val)[2] - font_spec_value.getbbox(val)[0]
                for _, val in right_specs
            )

            FLAG_W = 50
            FLAG_H = 35
            FLAG_MARGIN = 14

            # Anchor: flag right edge at canvas_right - 10px
            flag_right  = self.WIDTH - 10
            flag_x_base = flag_right - FLAG_W
            right_col_value_x = flag_x_base - FLAG_MARGIN - max_right_value_w
            right_col_label_x = right_col_value_x - self.COLUMN_GAP - max_right_label_w

            # Max width for left column values = gap to right label minus padding
            left_value_max_w = right_col_label_x - left_col_value_x - 35

            def truncate_text(text, font, max_w):
                """Truncate text with ellipsis if too wide."""
                if max_w <= 0:
                    return ''
                if font.getbbox(text)[2] - font.getbbox(text)[0] <= max_w:
                    return text
                while len(text) > 1:
                    text = text[:-1]
                    candidate = text + '…'
                    if font.getbbox(candidate)[2] - font.getbbox(candidate)[0] <= max_w:
                        return candidate
                return text

            for i, (label, value) in enumerate(left_specs):
                y = specs_start_y + i * self.LINE_HEIGHT
                draw.text((left_col_label_x, y), label, fill=self.TEXT_COLOR, font=font_spec_label)
                display_value = truncate_text(value, font_spec_value, left_value_max_w)
                draw.text((left_col_value_x, y), display_value, fill=self.TEXT_COLOR, font=font_spec_value)

            for i, (label, value) in enumerate(right_specs):
                y = specs_start_y + i * self.LINE_HEIGHT
                draw.text((right_col_label_x, y), label, fill=self.TEXT_COLOR, font=font_spec_label)
                draw.text((right_col_value_x,  y), value, fill=self.TEXT_COLOR, font=font_spec_value)
            
            # ============ 4. ФЛАГ СТРАНЫ ============
            
            country = specs.get('country', '')
            if country:
                # Флаг — позиция уже вычислена выше как flag_x_base
                flag_y = specs_start_y + self.LINE_HEIGHT + 4
                self.draw_flag(draw, country, flag_x_base, flag_y)
            
            # ============ СОХРАНЕНИЕ ============
            
            canvas.save(output)
            log.info(f"Poster saved: {output}")
            
        except Exception as e:
            log.error(f"Poster generation failed: {e}")
            import traceback
            traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="Auto Poster Generator v5.0")
    parser.add_argument("--car", required=True, help='Car name (e.g. "Porsche 911")')
    parser.add_argument("--output", default="", help="Output filename")
    args = parser.parse_args()
    
    car_query = args.car.strip()
    output_file = args.output or f"poster_{car_query.replace(' ', '_')}.png"
    
    log.info("=" * 70)
    log.info(f"  CAR: {car_query}")
    log.info(f"  OUTPUT: {output_file}")
    log.info("=" * 70)
    
    scraper = None
    specs = {}
    
    try:
        parts = car_query.split(None, 1)
        brand = parts[0]
        model = parts[1] if len(parts) > 1 else ""
        
        # 1. Парсинг
        scraper = AutoCatalogScraper()
        search_results = scraper.search_car(brand, model)
        
        if search_results:
            first_result = search_results[0]
            log.info(f"Selected model: {first_result['name']}")
            
            specs = scraper.parse_specs(first_result['url'])
        
        # 2. Fallback ДОПОЛНЯЕТ недостающие данные (не заменяет!)
        if specs:
            car_key = car_query.lower().strip()
            fallback = FALLBACK_DB.get(car_key)
            
            if not fallback:
                for key, value in FALLBACK_DB.items():
                    if brand.lower() in key:
                        fallback = value
                        break
            
            if fallback:
                # Дополняем ТОЛЬКО отсутствующие поля
                for key in ['engine', 'power', 'torque', 'acceleration', 'top_speed', 'weight', 'year']:
                    if key not in specs or not specs.get(key):
                        specs[key] = fallback.get(key, 'N/A')
                log.info(f"Filled missing specs from fallback")
        else:
            # Если парсинг совсем не сработал
            specs = {'model': car_query}
            car_key = car_query.lower().strip()
            fallback = FALLBACK_DB.get(car_key)
            if fallback:
                specs.update(fallback)
        
        # Страна
        if 'country' not in specs or not specs['country']:
            specs['country'] = BRAND_COUNTRIES.get(brand.lower(), '')
        
        log.info(f"Final specs: {specs}")
        
        # 3. Фото
        fetcher = ImageFetcher()
        photo = fetcher.get(brand, model)
        
        # 4. Постер
        generator = PosterGenerator()
        generator.generate(specs, photo, output_file)
        
        print()
        print("=" * 70)
        print(f"  SUCCESS! Poster saved to: {output_file}")
        print("=" * 70)
        print()
        
    except KeyboardInterrupt:
        log.warning("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        log.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()
