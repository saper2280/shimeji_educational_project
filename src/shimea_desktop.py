import sys, os, random, time
import json
import logging
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QDialog,
    QTextBrowser, QLineEdit, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QVariantAnimation, QEasingCurve, QPoint, QThread
from PyQt5.QtGui import QPixmap, QFontDatabase, QTransform
from pathlib import Path
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# явно загружаем .env из той же папки, где находится этот файл
dotenv_path = Path(__file__).resolve().parent / "OPENAI_API_KEY.env"
load_dotenv(dotenv_path=dotenv_path)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.warning("OPENAI_API_KEY не найден. Chat/AI funkce budou nedostupné.")
    client = None
else:
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
        "character_changed": "Postava změněna",
        "character_1": "Postava 1",
        "character_2": "Postava 2",
        "system_prompt": "jsi mily ucitel, ktery dovoluje vsechno",
        "joke_prompt": "Jsi vtipný asistent, který říká krátké vtipy.",
        "joke_request": "Řekni tatinkuvtip.",
        "character_3": "Postava 3",
        "delete history": "Smazat historii",
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
        "character_changed": "Character changed",
        "character_1": "Character 1",
        "character_2": "Character 2",
        "system_prompt": "you are a kind teacher who allows everything",
        "joke_prompt": "You are a funny assistant who tells short jokes.",
        "joke_request": "Tell me a dad joke.",
        "character_3": "Character 3",
        "delete history": "Delete history",
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
        "character_changed": "Персонаж изменен",
        "character_1": "Персонаж 1",
        "character_2": "Персонаж 2",
        "system_prompt": "ты добрый учитель, который позволяет всё",
        "joke_prompt": "Ты забавный помощник, который рассказывает короткие шутки.",
        "joke_request": "Расскажи мне шутку.",
        "character_3": "Персонаж 3",
        "delete history": "Удалить историю"
    }
}

# --- Конфигурационный класс ---
class Config:
    """Správa stavu aplikace (singleton pattern)"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.language = self._load_language()
        self.character = self._load_character()
    
    @staticmethod
    def _load_language():
        """Načti uložený jazyk z JSON nebo vrátí 'cs' jako výchozí"""
        json_path = Path(__file__).resolve().parent / "current language.json"
        try:
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("language", "cs")
        except Exception as e:
            logger.error(f"Chyba při čtení jazyka: {e}")
        return "cs"
    
    @staticmethod
    def _load_character():
        """Načti uložený personáž z JSON nebo vrátí '1' jako výchozí"""
        json_path = Path(__file__).resolve().parent / "current character.json"
        try:
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("character", "1")
        except Exception as e:
            logger.error(f"Chyba při čtení personáže: {e}")
        return "1"
    
    def set_language(self, lang_code):
        """Nastav a ulož jazyk"""
        self.language = lang_code
        json_path = Path(__file__).resolve().parent / "current language.json"
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({"language": lang_code}, f, ensure_ascii=False, indent=2)
            logger.info(f"Jazyk změněn na: {lang_code}")
        except Exception as e:
            logger.error(f"Chyba při ukládání jazyka: {e}")
    
    def set_character(self, character):
        """Nastav a ulož personáž"""
        self.character = character
        json_path = Path(__file__).resolve().parent / "current character.json"
        try:
            data = {}
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            data["character"] = character
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Personáž změněn na: {character}")
        except Exception as e:
            logger.error(f"Chyba při ukládání personáže: {e}")

# Inicijalizuj konfiguraci
config = Config()

def get_text(key):
    """Získej text pro aktuální jazyk"""
    return LANGUAGES[config.language].get(key, key)

# --- Постава ---
class Character(QLabel):
    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()

# --- Worker для асинхронных AI запросов ---
class AIResponseWorker(QThread):
    """Работник для обработки AI запроса в отдельном потоке"""
    response_ready = pyqtSignal(str)  # Сигнал для отправки готового результата
    error_occurred = pyqtSignal(str)  # Сигнал для ошибок

    def __init__(self, user_message, parent=None):
        super().__init__(parent)
        self.user_message = user_message

    def run(self):
        """Выполняется в отдельном потоке"""
        try:
            if not client:
                self.response_ready.emit("Omlouvám se, AI funkce nejsou k dispozici (chybí API klíč).")
                return
            
            # Обработка специальных команд
            if self.user_message == "do a backflip":
                self.response_ready.emit("backflip")
                return
            if self.user_message == "do a flip":
                self.response_ready.emit("flip")
                return
            
            # Получить ответ от OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": get_text("system_prompt")},
                    {"role": "user", "content": self.user_message}
                ]
            )
            result = response.choices[0].message.content
            self.response_ready.emit(result)
        except Exception as e:
            logger.error(f"Chyba AI odpovědi: {e}")
            self.error_occurred.emit(str(e))

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
        self.btnClear = QPushButton(get_text("delete history"))  # Новая кнопка

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
        
        # Инициализация worker thread переменной
        self.ai_worker = None

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
            self.get_ai_response_async("do a flip")
            save_chat_history(self.messages)
            return
        if text == "do a backflip":
            self.textOutput.append("<b>Vy:</b> do a backflip")
            self.textInput.clear()
            self.messages.append({"role": "user", "content": "do a backflip"})
            self.get_ai_response_async("do a backflip")
            save_chat_history(self.messages)
            return
        if text:
            self.textOutput.append(f"<b>Vy:</b> {text}")
            self.textInput.clear()
            self.messages.append({"role": "user", "content": text})
            # Отключить кнопку отправки во время обработки
            self.btnSend.setEnabled(False)
            self.get_ai_response_async(text)
            save_chat_history(self.messages)

    def get_ai_response_async(self, user_message):
        """Получить AI ответ асинхронно в отдельном потоке"""
        # Остановить предыдущий worker если он еще работает
        if self.ai_worker is not None and self.ai_worker.isRunning():
            self.ai_worker.quit()
            self.ai_worker.wait()
        
        # Создать новый worker
        self.ai_worker = AIResponseWorker(user_message)
        self.ai_worker.response_ready.connect(self.on_ai_response)
        self.ai_worker.error_occurred.connect(self.on_ai_error)
        self.ai_worker.finished.connect(self.on_worker_finished)
        self.ai_worker.start()

    def on_ai_response(self, response_text):
        """Обработать ответ от AI"""
        # Handle special commands
        if response_text == "backflip":
            if self.parent() is not None and hasattr(self.parent(), "do_a_backflip"):
                self.parent().do_a_backflip()
            response_text = "Provedl jsem backflip!"
        elif response_text == "flip":
            if self.parent() is not None and hasattr(self.parent(), "do_a_flip"):
                self.parent().do_a_flip()
            response_text = "Provedl jsem otočení!"
        
        # Показать ответ в чате
        self.textOutput.append(f"<b>Shimea:</b> {response_text}")
        self.messages.append({"role": "assistant", "content": response_text})
        save_chat_history(self.messages)

    def on_ai_error(self, error_text):
        """Обработать ошибку от AI"""
        error_message = f"Chyba: {error_text}"
        self.textOutput.append(f"<b>Shimea:</b> {error_message}")
        self.messages.append({"role": "assistant", "content": error_message})
        save_chat_history(self.messages)

    def on_worker_finished(self):
        """Вызывается когда worker поток завершился"""
        self.btnSend.setEnabled(True)

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
        # Остановить worker если он работает
        if self.ai_worker is not None and self.ai_worker.isRunning():
            self.ai_worker.quit()
            self.ai_worker.wait()
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

        stngs_rel = os.path.join(os.path.dirname(__file__), "data", "settings_background.png")
        stngs_path = Path(stngs_rel).resolve()
        logger.debug(f"Hledám pozadí: {stngs_path}")
        if not stngs_path.exists():
            logger.warning(f"Pozadí nenalezeno: {stngs_path}")
        else:
            # Načtení přes QPixmap z file systému
            pix = QPixmap(str(stngs_path))
            logger.debug(f"QPixmap isNull: {pix.isNull()}")
            if not pix.isNull():
                from PyQt5.QtGui import QBrush
                # Skalovat pozadí na velikost widgetu a nastavit jako pozadí
                pix = pix.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                pal = self.palette()
                pal.setBrush(self.backgroundRole(), QBrush(pix))
                self.setAutoFillBackground(True)
                self.setPalette(pal)
        
        # Tlačítko pro změnu jazyka
        btn_language = QPushButton(get_text("change_language"))
        btn_language.clicked.connect(self.change_language)
        
        btn_character = QPushButton(get_text("change_character"))
        btn_character.clicked.connect(self.change_character)
        
        btn_colour = QPushButton(get_text("change_color") + " (není implementováno)")
        btn_close = QPushButton(get_text("close"))
        btn_close.clicked.connect(self.accept)

        btn_img_path = Path(os.path.join(os.path.dirname(__file__), "data", "bottom.png")).resolve()
        if btn_img_path.exists():
            uri = btn_img_path.as_uri() # Získat URI souboru
            btn_style = f"""
            QPushButton {{
                border: none;
                color: white;
                font-size: 40px;
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
            btn_language.setStyleSheet(btn_style)
            btn_character.setStyleSheet(btn_style)
            btn_colour.setStyleSheet(btn_style)
            btn_close.setStyleSheet(btn_style)
        
        layout.addWidget(btn_language)
        layout.addWidget(btn_character)
        layout.addWidget(btn_colour)
        layout.addWidget(btn_close)
    
    def change_language(self):
        """Otevři dialog pro výběr jazyka"""
        
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
        config.set_language(lang_code)
        dialog.accept()
        
        # Zobraz zprávu
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Info", get_text("language_changed"))

    def change_character(self):
        """Otevři dialog pro výběr personáže"""
        
        characters = ["1", "2", "3"]
        char_names = {
            "1": get_text("character_1"),
            "2": get_text("character_2"),
            "3": get_text("character_3")
        }
        
        # Vytvoř dialog s tlačítky
        dlg = QDialog(self)
        dlg.setWindowTitle(get_text("change_character"))
        dlg.setFixedSize(300, 150)
        layout = QVBoxLayout(dlg)
        
        for char_id in characters:
            btn = QPushButton(char_names.get(char_id, char_id))
            btn.clicked.connect(lambda checked=False, cid=char_id: self.select_character(cid, dlg))
            layout.addWidget(btn)
        
        dlg.exec_()
    
    def select_character(self, character, dialog):
        """Nastav nový personáž a ulož ho"""
        config.set_character(character)
        dialog.accept()
        
        # Pokud je SettingsDialog otevřen z herního okna, znovu načti animace
        parent = self.parent()
        if parent and hasattr(parent, 'reload_character_animations'):
            parent.reload_character_animations()
        
        # Zobraz zprávu
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Info", get_text("character_changed"))


class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(840, 520)
        # Okno bez systémové lišty, vždy nahoře
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Cesta k souboru pozadí
        bg_rel = os.path.join(os.path.dirname(__file__), "data", "main_background.png")
        bg_path = Path(bg_rel).resolve()
        logger.debug(f"Hledám pozadí: {bg_path}")
        if not bg_path.exists():
            logger.warning(f"Pozadí nenalezeno: {bg_path}")
        else:
            # Načtení přes QPixmap z file systému
            pix = QPixmap(str(bg_path))
            logger.debug(f"QPixmap isNull: {pix.isNull()}")
            if not pix.isNull():
                from PyQt5.QtGui import QBrush
                # Skalovat pozadí na velikost widgetu a nastavit jako pozadí
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
            # Fallback: bez obrázků v tlačítcích 
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
                logger.warning(f"Složka s animacemi nenalezena: {p}")
                self.animations[name] = frames
                return
            files = sorted(p.glob(pattern))
            logger.debug(f"Načítám animaci '{name}' ze {folder} - nalezeno {len(files)} souborů")
            for f in files:
                pix = QPixmap(str(f))
                if pix.isNull():
                    logger.warning(f"Nelze načíst obrázek: {f}")
                    continue
                if scale_size:
                    pix = pix.scaled(scale_size[0], scale_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
                frames.append(pix)
            logger.info(f"Načteno {len(frames)} snímků pro '{name}'")
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

    def reload_character_animations(self):
        """Znovu načti animace pro aktuálně vybraného personáže"""
        char_num = str(config.character) if config.character else "1"
        logger.info(f"Opětovné načítání animací pro personáž: {char_num}")
        
        idle_folder = f"idle0{char_num}_animation"
        walk_folder = f"walk0{char_num}_animation"
        talk_folder = f"talk0{char_num}_animation"
        sleep_folder = f"sleep0{char_num}_animation"
        
        # Smaž staré animace a vymaž cache
        self.animations = {}
        self.mirrored_cache = {}
        self.stop_animation()
        
        # Načti nové animace
        base_frames_dir = os.path.join(os.path.dirname(__file__), "data", "frames")
        self.load_animation_frames("idle", os.path.join(base_frames_dir, idle_folder), pattern="*.png", scale_size=(500,400))
        self.load_animation_frames("walk", os.path.join(base_frames_dir, walk_folder), pattern="*.png", scale_size=(500,400))
        self.load_animation_frames("talk", os.path.join(base_frames_dir, talk_folder), pattern="*.png", scale_size=(500,400))
        
        sleep_path = os.path.join(base_frames_dir, sleep_folder)
        if os.path.exists(sleep_path):
            self.load_animation_frames("sleep", sleep_path, pattern="*.png", scale_size=(500,400))
        
        # Spusť idle animaci
        if self.animations.get("idle"):
            logger.info(f"Spuštění idle animace s {len(self.animations['idle'])} snímky")
            self.start_animation("idle", fps=6)
        else:
            logger.warning("Žádné idle animace nebyly načteny!")

    def __init__(self):
        super().__init__()
        # Nastavení okna: bez rámečku, průhledné pozadí, nahoře
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)

        # Vyber animace podle personáže
        char_num = config.character if config.character else "1"
        char_num = str(char_num)  # Ujisti se, že je to řetězec
        idle_folder = f"idle0{char_num}_animation"
        walk_folder = f"walk0{char_num}_animation"
        talk_folder = f"talk0{char_num}_animation"
        sleep_folder = f"sleep0{char_num}_animation"
        
        # Ulož parametry pro znovupoužití
        self.char_num = char_num
        self.idle_folder = idle_folder
        self.walk_folder = walk_folder
        self.talk_folder = talk_folder
        self.sleep_folder = sleep_folder

        # Vytvoření widgetu postavy (Character dědí z QLabel)
        self.image_label = Character(self)
        # Zkus najít první obrázek ve složce
        frames_dir = os.path.join(os.path.dirname(__file__), "data", "frames", idle_folder)
        img_files = sorted(Path(frames_dir).glob("*.png"))
        if img_files:
            img_path = str(img_files[0])
        else:
            img_path = os.path.join(os.path.dirname(__file__), "data", "frames", "idle01_animation", "000.png")
        
        pixmap = QPixmap(img_path)
        if pixmap.isNull():
            logger.warning("Obrázek nebyl nalezen nebo nelze načíst!")
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
        self.fps = 12                    # dефолт кадров в секунду
        self.mirrored_cache = {}         # кеш зеркалированных списков

        # Pример: папка src/data/frames содержит subfolders: idle01/02, walk01/02, sleep01, talk01/02
        base_frames_dir = os.path.join(os.path.dirname(__file__), "data", "frames")
        logger.debug(f"Inicijalizace ShimeaWindow - char_num = {char_num}")
        self.load_animation_frames("idle", os.path.join(base_frames_dir, idle_folder), pattern="*.png", scale_size=(500,400))
        self.load_animation_frames("walk", os.path.join(base_frames_dir, walk_folder), pattern="*.png", scale_size=(500,400))
        self.load_animation_frames("talk", os.path.join(base_frames_dir, talk_folder), pattern="*.png", scale_size=(500,400))
        
        logger.debug(f"Načtené animace - idle: {len(self.animations.get('idle', []))}, walk: {len(self.animations.get('walk', []))}, talk: {len(self.animations.get('talk', []))}")
        
        # Проверka наличия sleep anимace
        sleep_path = os.path.join(base_frames_dir, sleep_folder)
        if os.path.exists(sleep_path):
            self.load_animation_frames("sleep", sleep_path, pattern="*.png", scale_size=(500,400))

        # установить стартовый кадр (если есть idle)
        if self.animations.get("idle"):
            logger.info(f"Spuštění idle animace se {len(self.animations['idle'])} snímky")
            self.start_animation("idle", fps=6)
        else:
            logger.warning("Žádné idle animace nebyly načteny!")

    def set_start_pos(self):
        x = 50
        # Náhodná výška v rámci okna (s rezervou od spodního okraje)
        y = random.randint(100, self.height() - self.image_label.height() - 100)
        self.image_label.move(x, y)
        # Spustit gravitační efekt (vrácení dolů) - asynchronně!
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
        """Asynchronní pád dolů bez zamrznutí integrátoru (pomocí animace)"""
        target_y = self.geometry().height() - self.image_label.height()
        current_y = self.image_label.y()
        
        if current_y >= target_y:
            return  # Už je dole
        
        # Vytvořit animaci pádu
        if hasattr(self, "_gravity_anim") and self._gravity_anim is not None:
            try:
                self._gravity_anim.stop()
            except Exception:
                pass
        
        anim = QPropertyAnimation(self.image_label, b"pos", self)
        anim.setDuration(max(500, (target_y - current_y) * 2))  # čas padání závisí na vzdálenosti
        anim.setStartValue(self.image_label.pos())
        anim.setEndValue(QPoint(self.image_label.x(), target_y))
        anim.setEasingCurve(QEasingCurve.InQuad)  # gravitační křivka
        anim.start()
        self._gravity_anim = anim

    def auto_move(self):
        x = self.image_label.x() + self.dx
        y = self.image_label.y() + self.dy
        self.image_label.move(x, y)

    def do_random_action(self):
        action = random.choice(self.actions)
        action()

    def do_a_flip(self):
        """Otočení postavy s animací (otočení vpřed)"""
        self._perform_rotation_animation(360.0, 500)

    def do_a_backflip(self):
        """Otočení postavy s animací (otočení vzad)"""
        self._perform_rotation_animation(-360.0, 500)

    def _perform_rotation_animation(self, end_angle, duration):
        """Běžná funkce pro rotační animace"""
        base = self.image_label.pixmap()
        if base is None:
            logger.warning("Žádný obrázek k otočení")
            return
        base = base.copy()

        # Zastavit předchozí animaci pokud existuje
        if hasattr(self, "_flip_anim") and self._flip_anim is not None:
            try:
                self._flip_anim.stop()
            except Exception:
                pass
            self._flip_anim = None

        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(end_angle)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def on_value_changed(value):
            angle = float(value)
            t = QTransform()
            t.rotate(angle)
            rotated = base.transformed(t, Qt.SmoothTransformation)
            self.image_label.setPixmap(rotated)
            self.image_label.setFixedSize(rotated.size())

        def on_finished():
            # Reset na původní obrázek
            self.image_label.setPixmap(base)
            self.image_label.setFixedSize(base.size())
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

        logger.debug(f"Shimea jde! y={y}, dx={self.dx}, facing_left={self.facing_left}")

    def sleep(self):
        self.dx = 0
        self.dy = 0
        logger.debug("Shimea spí!")
        if hasattr(self, "joke_label") and self.joke_label is not None:
            self.joke_label.hide()

    def joke_generate(self):
        if not client:
            logger.warning("OpenAI klíč není dostupný, vrácení výchozího vtipu")
            return "Proč byl matematik smutný? Protože svůj život vydělil na části!"
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": get_text("joke_prompt")},
                    {"role": "user", "content": get_text("joke_request")}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Chyba při generování vtipu: {e}")
            return "Nemůžu si vzpomenout na vtip, omlouvám se!"

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
        y = 700
        self.joke_label.move(x, y)
        self.joke_label.show()

        if self.animations.get("talk"):
            self.start_animation("talk", fps=12)
            # vернуться к idle через 3 секунды
            QTimer.singleShot(14000, lambda: self.start_animation("idle", fps=6))

        logger.info(f"Shimea vypráví vtip: {joke_text}")

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
        self.stop_random_action()

    def open_settings_from_game(self):
        # Otevřít nastavení z herního okna
        dlg = SettingsDialog(self)
        dlg.exec_()

def load_chat_history():
    """Načti historii chatu z JSON"""
    json_path = Path(__file__).resolve().parent / "chat_history.json"
    try:
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("messages", [])
    except Exception as e:
        logger.error(f"Chyba při čtení historie chatu: {e}")
    return []

def save_chat_history(messages):
    """Ulož historii chatu do JSON"""
    json_path = Path(__file__).resolve().parent / "chat_history.json"
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"messages": messages}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Chyba při ukládání historie chatu: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font_path = os.path.join(os.path.dirname(__file__), "data", "BoldPixels.otf")
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)
        logger.info("Vlastní font načten")
    else:
        logger.warning(f"Vlastní font nenalezen: {font_path}")

    # Zobrazit hlavní menu před spuštěním postavy
    logger.info("Spouštění Shimea aplikace")
    menu = MainMenu()
    menu.show()

    sys.exit(app.exec_())
