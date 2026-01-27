import sys, os, random, time
import json
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QDialog,
    QTextBrowser, QLineEdit, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QVariantAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QPixmap, QFontDatabase, QTransform
from pathlib import Path
from dotenv import load_dotenv

# явно загружаем .env из той же папки, где находится этот файл
#dotenv_path = Path(__file__).resolve().parent / ".env"
#load_dotenv(dotenv_path=dotenv_path)

api_key = "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"
#if not api_key:
#    print("WARNING: OPENAI_API_KEY не задан. Chat/AI функции отключены.")
#    client = None
#else:
from openai import OpenAI
client = OpenAI(api_key=api_key)

# Jazykové soubory (slovník)
LANGUAGES = {
    "cs": {
        "chat_title": "Chat se Shimea",
        "send": "Odeslat",
        "close": "Zavřít",
        "start": "Start",
        "settings": "Nastavení",
        "exit": "Ukončit",
        "change_language": "Změnit jazyk",
        "change_color": "Změnit barevní paletu",
        "change_character": "Změnit postavu",
        "language_changed": "Jazyk změněn na čeština",
        "system_prompt": "jsi mily ucitel, ktery dovoluje vsechno",
        "joke_prompt": "Jsi vtipný asistent, který říká krátké vtipy.",
        "joke_request": "Řekni tatinkuvtip.",
    },
    "en": {
        "chat_title": "Chat with Shimea",
        "send": "Send",
        "close": "Close",
        "start": "Start",
        "settings": "Settings",
        "exit": "Exit",
        "change_language": "Change language",
        "change_color": "Change color palette",
        "change_character": "Change character",
        "language_changed": "Language changed to English",
        "system_prompt": "you are a kind teacher who allows everything",
        "joke_prompt": "You are a funny assistant who tells short jokes.",
        "joke_request": "Tell me a dad joke.",
    },
    "ru": {
        "chat_title": "Чат с Shimea",
        "send": "Отправить",
        "close": "Закрыть",
        "start": "Начать",
        "settings": "Настройки",
        "exit": "Выход",
        "change_language": "Изменить язык",
        "change_color": "Изменить палитру",
        "change_character": "Изменить персонажа",
        "language_changed": "Язык изменен на русский",
        "system_prompt": "ты добрый учитель, который позволяет всё",
        "joke_prompt": "Ты забавный помощник, который рассказывает короткие шутки.",
        "joke_request": "Расскажи мне шутку.",
    }
}

# Funkce pro načtení jazyka z JSON
def load_language():
    """Načti uložený jazyk z JSON nebo vrátí 'cs' jako výchozí"""
    json_path = Path(__file__).resolve().parent / "current language.json"
    try:
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("language", "cs")
    except Exception as e:
        print(f"Chyba při čtení jazyka: {e}")
    return "cs"

def save_language(lang_code):
    """Ulož jazyk do JSON"""
    json_path = Path(__file__).resolve().parent / "current language.json"
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"language": lang_code}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Chyba při ukládání jazyka: {e}")

# Načti jazyk při spuštění
current_language = load_language()

def get_text(key):
    """Получи текст для текущего языка"""
    return LANGUAGES[current_language].get(key, key)

# --- Postava ---
class Character(QLabel):
    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()

# --- Chat dialog ---
# Po dvojkliku na postavu se otevře okno chatu s AI
class ChatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(get_text("chat_title"))
        self.setFixedSize(600, 400)
        self.setWindowFlags(Qt.Dialog)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.textOutput = QTextBrowser()
        textOut_stylte = """
        QTextBrowser {
            border: 1px solid #ccc;
            border-color: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 10px;
        }
        """
        self.textOutput.setStyleSheet(textOut_stylte)

        self.textInput = QLineEdit()
        self.btnSend = QPushButton(get_text("send"))
        self.btnClose = QPushButton(get_text("close"))
        self.btnClear = QPushButton("Vymazat historii")  # Новая кнопка

        bottomLayout = QHBoxLayout()
        bottomLayout.addWidget(self.textInput)
        bottomLayout.addWidget(self.btnSend)
        bottomLayout.addWidget(self.btnClear)
        bottomLayout.addWidget(self.btnClose)

        layout = QVBoxLayout(self)
        layout.addWidget(self.textOutput)
        layout.addLayout(bottomLayout)

        self.btnClose.clicked.connect(self.close)
        self.btnSend.clicked.connect(self.send_message)
        self.btnClear.clicked.connect(self.clear_history)

        # Загрузи предыдущую историю чату
        self.messages = load_chat_history()
        self.display_chat_history()

    def display_chat_history(self):
        """Выведи всю историю чату в текстовое поле"""
        self.textOutput.clear()
        for msg in self.messages:
            if msg["role"] == "user":
                self.textOutput.append(f"<b>Vy:</b> {msg['content']}")
            else:
                self.textOutput.append(f"<b>Shimea:</b> {msg['content']}")

    def send_message(self):
        text = self.textInput.text().strip()
        if text == "bye":
            self.textOutput.append("<b>Vy:</b> bye")
            self.textInput.clear()
            self.close()
            return
        if text == "do a flip":
            self.textOutput.append("<b>Vy:</b> do a flip")
            self.textInput.clear()
            self.messages.append({"role": "user", "content": "do a flip"})
            self.get_ai_response("do a flip")
            save_chat_history(self.messages)
            return
        if text == "do a backflip":
            self.textOutput.append("<b>Vy:</b> do a backflip")
            self.textInput.clear()
            self.messages.append({"role": "user", "content": "do a backflip"})
            self.get_ai_response("do a backflip")
            save_chat_history(self.messages)
            return
        if text:
            self.textOutput.append(f"<b>Vy:</b> {text}")
            self.textInput.clear()
            self.messages.append({"role": "user", "content": text})
            response_text = self.get_ai_response(text)
            self.textOutput.append(f"<b>Shimea:</b> {response_text}")
            self.messages.append({"role": "assistant", "content": response_text})
            save_chat_history(self.messages)

    def get_ai_response(self, user_message):
        if user_message == "do a backflip":
            if self.parent() is not None and hasattr(self.parent(), "do_a_backflip"):
                self.parent().do_a_backflip()
            return "Provedl jsem backflip!"
        if user_message == "do a flip":
            if self.parent() is not None and hasattr(self.parent(), "do_a_flip"):
                self.parent().do_a_flip()
            return "Provedl jsem otočení!"
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": get_text("system_prompt")},
                    {"role": "user", "content": user_message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Chyba: {e}"

    def clear_history(self):
        """Vymazat historii chatu"""
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Potvrdit", "Opravdu chceš vymazat historii chatu?")
        if reply == QMessageBox.Yes:
            self.messages = []
            self.textOutput.clear()
            save_chat_history([])
            QMessageBox.information(self, "Info", "Historie chatu byla vymazána")

    def closeEvent(self, event):
        # Ulož historii při zavření
        save_chat_history(self.messages)
        event.accept()

# --- Nastavení a hlavní menu ---
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(get_text("settings"))
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFixedSize(840, 520)
        layout = QVBoxLayout(self)
        
        # Tlačítko pro změnu jazyka - nyní funkční
        btn_language = QPushButton(get_text("change_language"))
        btn_language.clicked.connect(self.change_language)
        
        btn_colour = QPushButton(get_text("change_color") + " (není implementováno)")
        btn_character = QPushButton(get_text("change_character") + " (není implementováno)")
        btn_close = QPushButton(get_text("close"))
        btn_close.clicked.connect(self.accept)
        
        layout.addWidget(btn_language)
        layout.addWidget(btn_colour)
        layout.addWidget(btn_character)
        layout.addWidget(btn_close)
    
    def change_language(self):
        """Otevři dialog pro výběr jazyka"""
        global current_language
        
        languages_list = list(LANGUAGES.keys())
        lang_names = {
            "cs": "Čeština",
            "en": "English",
            "ru": "Русский"
        }
        
        # Vytvoř dialog s tlačítky
        dlg = QDialog(self)
        dlg.setWindowTitle("Vybrat jazyk")
        dlg.setFixedSize(300, 150)
        layout = QVBoxLayout(dlg)
        
        for lang_code in languages_list:
            btn = QPushButton(lang_names.get(lang_code, lang_code))
            btn.clicked.connect(lambda checked=False, code=lang_code: self.select_language(code, dlg))
            layout.addWidget(btn)
        
        dlg.exec_()
    
    def select_language(self, lang_code, dialog):
        """Nastav nový jazyk a ulož ho"""
        global current_language
        current_language = lang_code
        save_language(lang_code)  # Ulož do JSON
        dialog.accept()
        
        # Zobraz zprávu
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Info", get_text("language_changed"))


class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(840, 520)
        # Okno bez systémové lišty, vždy nahoře
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Cesta k souboru pozadí (používáme přímou cestu místo URI)
        bg_rel = os.path.join(os.path.dirname(__file__), "data", "main_background.png")
        bg_path = Path(bg_rel).resolve()
        print("DEBUG: bg_path:", bg_path)
        if not bg_path.exists():
            print(f"Pozadí nenalezeno: {bg_path}")
        else:
            # Načtení přes QPixmap z file systému
            pix = QPixmap(str(bg_path))
            print("DEBUG: pix.isNull():", pix.isNull())
            if not pix.isNull():
                from PyQt5.QtGui import QBrush
                # Skalovat pozadí na velikost widgetu (může být (0,0), pokud ještě není zobrazeno)
                pix = pix.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                pal = self.palette()
                pal.setBrush(self.backgroundRole(), QBrush(pix))
                self.setAutoFillBackground(True)
                self.setPalette(pal)

        layout = QVBoxLayout(self)
        layout.addStretch()

        btn_start = QPushButton(get_text("start"))
        btn_settings = QPushButton(get_text("settings"))
        btn_exit = QPushButton(get_text("exit"))

        btn_start.setFixedSize(320, 70)
        btn_settings.setFixedSize(320, 70)
        btn_exit.setFixedSize(320, 70)

        # Pozadí tlačítka z obrázku pokud existuje
        btn_img_path = Path(os.path.join(os.path.dirname(__file__), "data", "bottom.png")).resolve()
        if btn_img_path.exists():
            uri = btn_img_path.as_uri() # Získat URI souboru
            btn_style = f"""
            QPushButton {{
                border: none;
                color: white;
                font-size: 50px;
                font-family: 'BoldPixels', sans-serif;
                border-radius: 12px;
                padding: 8px 16px;
                border-image: url("{uri}") 0 0 0 0 stretch stretch;
            }}
            QPushButton:hover {{
                opacity: 0.95;
            }}
            QPushButton:pressed {{
                background-color: rgba(0,0,0,0.15);
            }}
            """
            btn_start.setStyleSheet(btn_style)
            btn_settings.setStyleSheet(btn_style)
            btn_exit.setStyleSheet(btn_style)

        else:
            # Fallback: bez obrázků v tlačítcích — jen jednoduché styly
            btn_style = """
            QPushButton {
                border: none;
                color: white;
                font-size: 50px;
                font-family: 'BoldPixels', sans-serif;
                border-radius: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: rgba(150, 150, 150, 0.7);
            }
            QPushButton:pressed {
                background-color: rgba(50, 50, 50, 0.8);
            }
            """
            btn_start.setStyleSheet(btn_style)
            btn_settings.setStyleSheet(btn_style)
            btn_exit.setStyleSheet(btn_style)

        btn_start.clicked.connect(self.start_game)
        btn_settings.clicked.connect(self.open_settings)
        btn_exit.clicked.connect(QApplication.instance().quit)

        layout.addWidget(btn_start)
        layout.addWidget(btn_settings)
        layout.addWidget(btn_exit)

        layout.setSpacing(20)
        # Okraje layoutu (left, top, right, bottom)
        layout.setContentsMargins(350, 80, 50, 200)
        layout.addStretch()

        # Uchováme referenci na okno postavy, aby GC ho nesmazal
        self.shimea_window = None

    def start_game(self):
        self.shimea_window = ShimeaWindow()
        QApplication.instance().shimea_window = self.shimea_window
        QApplication.instance().shimea_menu = self  # uchovat referenci na menu
        self.shimea_window.show()
        self.hide()

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec_()

# --- Hlavní okno (Shimea) ---
class ShimeaWindow(QWidget):

    def load_animation_frames(self, name, folder, pattern="*.png", scale_size=None):
            p = Path(folder)
            frames = []
            if not p.exists():
                print(f"Frames folder not found: {p}")
                self.animations[name] = frames
                return
            files = sorted(p.glob(pattern))
            for f in files:
                pix = QPixmap(str(f))
                if pix.isNull():
                    continue
                if scale_size:
                    pix = pix.scaled(scale_size[0], scale_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
                frames.append(pix)
            self.animations[name] = frames

    def _next_frame(self):
            if not self.current_anim or self.current_anim not in self.animations:
                return
            frames = self.animations.get(self.current_anim, [])
            if not frames:
                return
            self.frame_index = (self.frame_index + 1) % len(frames)
            pix = frames[self.frame_index]
            if getattr(self, "facing_left", False):
                key = (self.current_anim, True)
                if key not in self.mirrored_cache:
                    self.mirrored_cache[key] = [p.transformed(QTransform().scale(-1, 1)) for p in frames]
                pix = self.mirrored_cache[key][self.frame_index]
            self.image_label.setPixmap(pix)
            self.image_label.setFixedSize(pix.size())

    def start_animation(self, name, fps=None):
            if name == self.current_anim and self.frame_timer.isActive():
                return
            frames = self.animations.get(name, [])
            if not frames:
                return
            self.current_anim = name
            self.frame_index = 0
            if fps:
                self.fps = fps
            interval = max(1, int(1000 / self.fps))
            self.frame_timer.start(interval)
            pix = frames[0]
            if getattr(self, "facing_left", False):
                key = (name, True)
                if key not in self.mirrored_cache:
                    self.mirrored_cache[key] = [p.transformed(QTransform().scale(-1, 1)) for p in frames]
                pix = self.mirrored_cache[key][0]
            self.image_label.setPixmap(pix)
            self.image_label.setFixedSize(pix.size())

    def stop_animation(self):
            if self.frame_timer.isActive():
                self.frame_timer.stop()
            self.current_anim = None
            self.frame_index = 0

    def __init__(self):
        super().__init__()
        # Nastavení okna: bez rámečku, průhledné pozadí, nahoře
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)

        # Vytvoření widgetu postavy (Character dědí z QLabel)
        self.image_label = Character(self)
        img_path = os.path.join(os.path.dirname(__file__), "data", "frames", "idle_animation", "000.png")
        pixmap = QPixmap(img_path)
        if pixmap.isNull():
            print("Obrázek nebyl nalezen nebo nelze načíst!")
        pixmap = pixmap.scaled(500, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.size())
        self.image_label.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.addStretch()

        # создаём поля вместо локальных переменных
        self.btn_back = QPushButton("<-", self)
        self.btn_settings = QPushButton("#", self)
        self.btn_exit = QPushButton("X", self)

        # небольшой контейнер с вертикальным layout'ом, чтобы управлять группой кнопок
        btn_container = QWidget(self)
        vbox = QVBoxLayout(btn_container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(5)
        vbox.addWidget(self.btn_back)
        vbox.addWidget(self.btn_settings)
        vbox.addWidget(self.btn_exit)
        btn_container.setFixedSize(60, 170)

        # разместить контейнер в правом верхнем углу (с отступами)
        btn_container.move(self.width() - btn_container.width() - 10, 455)

        # Fallback styl (bez obrázků) — jednoduché text/ikonky
        btn_style = """
        QPushButton {
            border: none;
            background-color: rgba(0, 0, 0, 0.7);
            font-family: 'BoldPixels', sans-serif;
            color: white;
            font-size: 24px;
            border-radius: 8px;
            padding: 4px;
        }
        QPushButton:hover {
            background-color: rgba(150, 150, 150, 0.7);
        }
        QPushButton:pressed {
            background-color: rgba(50, 50, 50, 0.8);
        }
        """
        self.btn_back.setStyleSheet(btn_style)
        self.btn_settings.setStyleSheet(btn_style)
        self.btn_exit.setStyleSheet(btn_style)

        # Připoj tlačítka na akce (vraťit se do menu, otevřít nastavení, zavřít)
        self.btn_back.clicked.connect(self.go_back)
        self.btn_settings.clicked.connect(self.open_settings_from_game)
        self.btn_exit.clicked.connect(QApplication.instance().quit)

        # Připojení dvojkliku k otevření chatu
        self.image_label.doubleClicked.connect(self.open_chat)

        # Nastavení počáteční pozice po zobrazení okna
        QTimer.singleShot(0, self.set_start_pos)

        # Nastaveni animací a dalších vlastností
        self.animations = {}             # {'idle': [QPixmap,...], 'walk': [...], ...}
        self.current_anim = None
        self.frame_index = 0
        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self._next_frame)
        self.fps = 12                    # дефолт кадров в секунду
        self.mirrored_cache = {}         # кеш зеркалированных списков

        # Пример: папка src/data/frames содержит subfolders: idle, walk, sleep
        base_frames_dir = os.path.join(os.path.dirname(__file__), "data", "frames")
        self.load_animation_frames("idle", os.path.join(base_frames_dir, "idle_animation"), pattern="*.png", scale_size=(500,400))
        self.load_animation_frames("walk", os.path.join(base_frames_dir, "walk_animation"), pattern="*.png", scale_size=(500,400))
        self.load_animation_frames("sleep", os.path.join(base_frames_dir, "sleep_animation"), pattern="*.png", scale_size=(500,400))
        self.load_animation_frames("talk", os.path.join(base_frames_dir, "talk_animation"), pattern="*.png", scale_size=(500,400))

        # установить стартовый кадр (если есть idle)
        if self.animations.get("idle"):
            self.start_animation("idle", fps=6)
        else:
            # fallback: оставляем существующий статичный pixmap
            pass

    def set_start_pos(self):
        x = 50
        # Náhodná výška v rámci okna (s rezervou od spodního okraje)
        y = random.randint(100, self.height() - self.image_label.height() - 100)
        self.image_label.move(x, y)
        # Spustit gravitační efekt (vrácení dolů)
        self.gravity()
        # Inicializace pohybu a timerů
        self.dx = 0
        self.dy = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_move)
        self.timer.start(15)

        self.actions = [self.walk, self.sleep, self.joke]
        self.action_timer = QTimer()
        self.action_timer.timeout.connect(self.do_random_action)
        self.action_timer.start(15000)

    def gravity(self):
        # Blokující pád dolů (jednoduchá implementace) — lze nahradit animací pro plynulost
        while self.image_label.y() < self.geometry().height() - self.image_label.height():
            self.image_label.move(self.image_label.x(), self.image_label.y() + 1)
            QApplication.processEvents()
            time.sleep(0.001)

    def auto_move(self):
        x = self.image_label.x() + self.dx
        y = self.image_label.y() + self.dy
        self.image_label.move(x, y)

    def do_random_action(self):
        action = random.choice(self.actions)
        action()

    def do_a_flip(self):
        base = self.image_label.pixmap()
        if base is None:
            print("Žádný obrázek k otočení")
            return
        base = base.copy()  # uchovat původní pixmapu

        # Zastavit předchozí animaci pokud existuje
        if hasattr(self, "_flip_anim") and self._flip_anim is not None:
            try:
                self._flip_anim.stop()
            except Exception:
                pass
            self._flip_anim = None

        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(360.0)            # rotace o 360 stupňů
        anim.setDuration(500)             # doba trvání v ms
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def on_value_changed(value):
            angle = float(value)
            t = QTransform()
            t.rotate(angle)
            rotated = base.transformed(t, Qt.SmoothTransformation)
            self.image_label.setPixmap(rotated)
            self.image_label.setFixedSize(rotated.size())

        def on_finished():
            t = QTransform()
            t.rotate(360)
            final = base.transformed(t, Qt.SmoothTransformation)
            self.image_label.setPixmap(final)
            self.image_label.setFixedSize(final.size())
            self._flip_anim = None

        anim.valueChanged.connect(on_value_changed)
        anim.finished.connect(on_finished)

        self._flip_anim = anim
        anim.start()

    def do_a_backflip(self):
        base = self.image_label.pixmap()
        if base is None:
            print("Žádný obrázek k otočení")
            return
        base = base.copy()  # uchovat původní pixmapu

        # Zastavit předchozí animaci pokud existuje
        if hasattr(self, "_flip_anim") and self._flip_anim is not None:
            try:
                self._flip_anim.stop()
            except Exception:
                pass
            self._flip_anim = None

        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(-360.0)            # rotace o -360 stupňů
        anim.setDuration(500)             # doba trvání v ms
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def on_value_changed(value):
            angle = float(value)
            t = QTransform()
            t.rotate(angle)
            rotated = base.transformed(t, Qt.SmoothTransformation)
            self.image_label.setPixmap(rotated)
            self.image_label.setFixedSize(rotated.size())

        def on_finished():
            t = QTransform()
            t.rotate(360)
            final = base.transformed(t, Qt.SmoothTransformation)
            self.image_label.setPixmap(final)
            self.image_label.setFixedSize(final.size())
            self._flip_anim = None

        anim.valueChanged.connect(on_value_changed)
        anim.finished.connect(on_finished)

        self._flip_anim = anim
        anim.start()


    def stop_random_action(self):
        self.dx = 0
        self.dy = 0
        if hasattr(self, "joke_label") and self.joke_label is not None:
            self.joke_label.hide()
        if self.animations is not None:
            self.start_animation("idle", fps=6)

    def walk(self):
        # Случайное число по оси Y: отрицательное → двигаться влево, положительное → вправо
        # избегаем 0; используем скорость 1 или 2 (можно настроить)
        y = 0
        while y == 0:
            y = random.choice([-2, -1, 1, 2])

        speed = 2  # базовая скорость по X (можно поставить 1 или 3)
        self.dx = -speed if y < 0 else speed
        self.dy = 0

        # Обновляем направление взгляда для зеркалирования кадров
        self.facing_left = (self.dx < 0)

        # Скрыть пузырёк, если он есть
        if hasattr(self, "joke_label") and self.joke_label is not None:
            self.joke_label.hide()

        # Запустить анимацию ходьбы (если кадры загружены)
        if self.animations.get("walk"):
            self.start_animation("walk", fps=12)
            # вернуться к idle через 3 секунды
            QTimer.singleShot(15000, lambda: self.start_animation("idle", fps=6))

        print(f"Shimea chodí! y={y}, dx={self.dx}, facing_left={self.facing_left}")

    def sleep(self):
        self.dx = 0
        self.dy = 0
        print("Shimea spí!")
        if hasattr(self, "joke_label") and self.joke_label is not None:
            self.joke_label.hide()

    def joke_generate(self):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": get_text("joke_prompt")},
                {"role": "user", "content": get_text("joke_request")}
            ]
        )
        return response.choices[0].message.content

    def joke(self):
        if hasattr(self, "joke_label") and self.joke_label is not None:
            self.joke_label.deleteLater()
            self.joke_label = None
        if self.animations is not None:
            self.start_animation("idle", fps=6)
        self.dx = 0
        self.dy = 0
        joke_text = self.joke_generate()

        self.joke_label = QLabel(joke_text, self)
        style = """
        QLabel {
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-family: 'BoldPixels', sans-serif;
            font-size: 24px;
        }
        """
        self.joke_label.setStyleSheet(style)
        self.joke_label.setWordWrap(True)
        self.joke_label.adjustSize()
        self.joke_label.resize(self.joke_label.sizeHint())
        x = self.image_label.x() + (self.image_label.width() - self.joke_label.width()) // 2
        y = max(0, self.image_label.y() - self.joke_label.height() - 10)
        self.joke_label.move(x, y)
        self.joke_label.show()
        print(f"Shimea vypráví vtip: {joke_text}")

    def open_chat(self):
        # Při otevření chatu zastavit autonomní chování
        self.stop_random_action()
        if hasattr(self, "action_timer") and self.action_timer.isActive():
            self.action_timer.stop()
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()

        if self.animations.get("talk"):
            self.start_animation("talk", fps=12)

        # Zablokovat interakci s postavou
        self.chat_open = True

        dialog = ChatDialog(self)
        dialog.setWindowModality(Qt.ApplicationModal)  # blokovat aplikaci, dokud je dialog otevřen
        dialog.exec_()  # modální dialog

        # Po zavření dialogu obnovit chování
        self.chat_open = False
        if hasattr(self, "action_timer"):
            self.action_timer.start()
        if hasattr(self, "timer"):
            self.timer.start()
        if self.animations is not None:
            self.start_animation("idle", fps=6)

# Tažení myší
    def mousePressEvent(self, event):
        if getattr(self, "chat_open", False):
            return
        if event.button() == Qt.LeftButton and self.image_label.geometry().contains(event.pos()):
            self.drag_position = event.globalPos() - self.image_label.pos()
            self.stop_random_action()

    def mouseMoveEvent(self, event):
        if getattr(self, "chat_open", False):
            return
        if hasattr(self, "drag_position") and self.drag_position and event.buttons() == Qt.LeftButton:
            new_pos = event.globalPos() - self.drag_position
            self.image_label.move(new_pos)
            self.borders()

    def mouseReleaseEvent(self, event):
        self.drag_position = None
        self.gravity()

    def borders(self):
        screen_geometry = QApplication.desktop().availableGeometry(self)
        x, y = self.image_label.x(), self.image_label.y()
        w, h = self.image_label.width(), self.image_label.height()
        if x < screen_geometry.left() or x + w > screen_geometry.right():
            self.dx = -self.dx
        if y < screen_geometry.top() or y + h > screen_geometry.bottom():
            self.dy = -self.dy
        x = max(screen_geometry.left(), min(x, screen_geometry.right() - w))
        y = max(screen_geometry.top(), min(y, screen_geometry.bottom() - h))
        self.image_label.move(x, y)

    def go_back(self):
        margin = 20  # отступ от нижнего края
        screen_geom = QApplication.desktop().availableGeometry(self)

        # Центр по X внутри доступной области (учитывает левый отступ экрана)
        x = screen_geom.left() + (screen_geom.width() - self.image_label.width()) // 2
        # Нижняя позиция с учётом высоты персонажа и отступа
        y = screen_geom.bottom() - self.image_label.height() - margin

        # Плавное перемещение с помощью анимации
        anim = QPropertyAnimation(self.image_label, b"pos", self)
        anim.setDuration(400)
        anim.setStartValue(self.image_label.pos())
        anim.setEndValue(QPoint(x,y))
        anim.start()
        self._return_anim = anim

    def open_settings_from_game(self):
        # Otevřít nastavení z herního okna
        dlg = SettingsDialog(self)
        dlg.exec_()

def load_chat_history():
    """Загрузи историю чату из JSON"""
    json_path = Path(__file__).resolve().parent / "chat_history.json"
    try:
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("messages", [])
    except Exception as e:
        print(f"Chyba při čtení historie chatu: {e}")
    return []

def save_chat_history(messages):
    """Ulož historii chatu do JSON"""
    json_path = Path(__file__).resolve().parent / "chat_history.json"
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"messages": messages}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Chyba při ukládání historie chatu: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font_path = os.path.join(os.path.dirname(__file__), "data", "BoldPixels.otf")
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)

    # Zobrazit hlavní menu před spuštěním postavy
    menu = MainMenu()
    menu.show()

    sys.exit(app.exec_())
