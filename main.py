import sys
import os
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import QIcon

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super(ConfigDialog, self).__init__(parent)
        self.setWindowTitle('Configurações')
        self.setFixedSize(600, 400)

        layout = QVBoxLayout()

        self.block_downloads_checkbox = QCheckBox('Bloquear Downloads')
        layout.addWidget(self.block_downloads_checkbox)

        self.block_links_checkbox = QCheckBox('Bloquear Links (Exceto Favoritos)')
        layout.addWidget(self.block_links_checkbox)

        self.block_url_checkbox = QCheckBox('Bloquear URL Específica:')
        layout.addWidget(self.block_url_checkbox)

        self.block_url_edit = QLineEdit()
        self.block_url_edit.setPlaceholderText('Digite a URL a ser bloqueada')
        layout.addWidget(self.block_url_edit)

        self.tab_mode_checkbox = QCheckBox('ED optimise')
        layout.addWidget(self.tab_mode_checkbox)

        self.home_url_group = QGroupBox('Site Inicial:')
        home_url_layout = QVBoxLayout()

        options = [
            ('Google', 'https://www.google.com/'),
            ('YouTube', 'https://www.youtube.com/'),
            ('ChatGPT', 'https://www.chatgpt.com/'),
            ('GitHub', 'https://github.com/'),
            ('DSW', 'https://sites.google.com/view/dsw-wheel/baixar?authuser=0'),
            ('SBD', 'https://sites.google.com/view/sbdrp/in%C3%ADcio'),
            ('Media fire', 'https://app.mediafire.com/')
        ]

        self.radio_buttons = []

        for name, url in options:
            radio_button = QRadioButton(name)
            home_url_layout.addWidget(radio_button)
            self.radio_buttons.append((radio_button, url))

        self.custom_radio = QRadioButton('Personalizado')
        self.custom_url_edit = QLineEdit()
        self.custom_url_edit.setPlaceholderText('URL Personalizada')

        home_url_layout.addWidget(self.custom_radio)
        home_url_layout.addWidget(self.custom_url_edit)

        self.home_url_group.setLayout(home_url_layout)
        layout.addWidget(self.home_url_group)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_selected_home_url(self):
        for radio_button, url in self.radio_buttons:
            if radio_button.isChecked():
                return url

        if self.custom_radio.isChecked():
            return self.custom_url_edit.text()

        return ""

    def get_blocked_url(self):
        if self.block_url_checkbox.isChecked():
            return self.block_url_edit.text()
        else:
            return ""

    def get_tab_mode(self):
        return self.tab_mode_checkbox.isChecked()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.settings = QSettings("MyApp", "VALDABrowser")
        self.block_downloads = False
        self.block_links = False
        self.blocked_url = ""
        self.tab_mode = False
        self.home_url = "https://www.google.com/"

        self.load_settings()

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(self.home_url))
        self.setCentralWidget(self.browser)
        self.showMaximized()

        self.navbar = QToolBar()
        self.addToolBar(self.navbar)

        back_btn = QAction('⏪Voltar', self)
        back_btn.triggered.connect(self.browser.back)
        self.navbar.addAction(back_btn)

        forward_btn = QAction('Avançar ▶', self)
        forward_btn.triggered.connect(self.browser.forward)
        self.navbar.addAction(forward_btn)

        reload_btn = QAction('🔃Recarregar', self)
        reload_btn.triggered.connect(self.browser.reload)
        self.navbar.addAction(reload_btn)

        home_btn = QAction('🏠GO Home', self)
        home_btn.triggered.connect(self.navigate_home)
        self.navbar.addAction(home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.navbar.addWidget(self.url_bar)

        favorite_btn = QAction('Favoritar⭐', self)
        favorite_btn.triggered.connect(self.toggle_favorite)
        self.navbar.addAction(favorite_btn)

        self.favorites_combo = QComboBox()
        self.favorites_combo.setMaxVisibleItems(10)
        self.favorites_combo.setFixedWidth(150)
        self.favorites_combo.currentIndexChanged.connect(self.navigate_to_favorite)
        self.navbar.addWidget(self.favorites_combo)

        config_btn = QAction('| Configurações', self)
        config_btn.triggered.connect(self.show_config_dialog)
        self.navbar.addAction(config_btn)

        self.progress_bar = QProgressBar()
        self.navbar.addWidget(self.progress_bar)

        self.browser.loadProgress.connect(self.update_load_progress)

        self.favorites_file_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'favorites.txt')
        self.favorites = self.load_favorites()
        self.update_favorites_combo()

        self.download_manager = self.browser.page().profile().downloadRequested.connect(self.handle_download)

        # Correção: Crie a instância do ConfigDialog
        self.config_dialog = ConfigDialog(self)
        self.config_dialog.block_downloads_checkbox.stateChanged.connect(self.toggle_download_block)

    def handle_download(self, download):
        if self.block_downloads:
            QMessageBox.warning(self, 'Download Bloqueado', 'Os downloads estão bloqueados.')
            return

        suggested_file_name = download.suggestedFileName()
        if not suggested_file_name:
            suggested_file_name = 'downloaded_file'

        save_path, _ = QFileDialog.getSaveFileName(self, 'Salvar Arquivo', suggested_file_name, 'All Files (*)')

        if save_path:
            _, ext = os.path.splitext(suggested_file_name)
            if not save_path.lower().endswith(ext.lower()):
                save_path += ext.lower()

            download.setPath(save_path)
            download.accept()

    def navigate_home(self):
        self.browser.setUrl(QUrl(self.home_url))

    def navigate_to_url(self):
        url = self.url_bar.text()
        self.browser.setUrl(QUrl(url))

    def navigate_to_favorite(self, index):
        if index >= 0 and index < len(self.favorites):
            favorite_url = list(self.favorites)[index]
            self.browser.setUrl(QUrl(favorite_url))

    def update_load_progress(self, progress):
        self.progress_bar.setValue(progress)

    def toggle_favorite(self):
        current_url = self.browser.url().toString()

        if current_url in self.favorites:
            self.favorites.remove(current_url)
            self.update_favorites_combo()
            QMessageBox.information(self, 'Remover Favorito', 'Site removido dos favoritos.')
        else:
            name, ok = QInputDialog.getText(self, 'Adicionar Favorito', 'Digite um nome para o favorito:')
            if ok and name:
                self.favorites.add(current_url)
                self.update_favorites_combo()
                self.save_favorites()
                QMessageBox.information(self, 'Adicionar Favorito', 'Site adicionado aos favoritos com o nome: {}'.format(name))

    def update_favorites_combo(self):
        self.favorites_combo.clear()
        self.favorites_combo.addItems(self.favorites)

    def load_favorites(self):
        if os.path.exists(self.favorites_file_path):
            with open(self.favorites_file_path, 'r') as file:
                return set(file.read().splitlines())
        else:
            return set()

    def save_favorites(self):
        favorites_dir = os.path.dirname(self.favorites_file_path)
        if not os.path.exists(favorites_dir):
            os.makedirs(favorites_dir)

        with open(self.favorites_file_path, 'w') as file:
            file.write('\n'.join(self.favorites))

    def show_config_dialog(self):
        self.config_dialog.block_downloads_checkbox.setChecked(self.block_downloads)
        self.config_dialog.block_links_checkbox.setChecked(self.block_links)
        self.config_dialog.block_url_checkbox.setChecked(bool(self.blocked_url))
        self.config_dialog.block_url_edit.setText(self.blocked_url)
        self.config_dialog.tab_mode_checkbox.setChecked(self.tab_mode)

        for radio_button, url in self.config_dialog.radio_buttons:
            if url == self.home_url:
                radio_button.setChecked(True)

        if self.home_url not in [url for _, url in self.config_dialog.radio_buttons]:
            self.config_dialog.custom_radio.setChecked(True)
            self.config_dialog.custom_url_edit.setText(self.home_url)

        if self.config_dialog.exec_() == QDialog.Accepted:
            self.block_downloads = self.config_dialog.block_downloads_checkbox.isChecked()
            self.block_links = self.config_dialog.block_links_checkbox.isChecked()
            self.home_url = self.config_dialog.get_selected_home_url()
            self.blocked_url = self.config_dialog.get_blocked_url()
            self.tab_mode = self.config_dialog.get_tab_mode()
            self.save_settings()

    def toggle_download_block(self, state):
        self.block_downloads = state == Qt.Checked

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

    def save_settings(self):
        self.settings.setValue("block_downloads", self.block_downloads)
        self.settings.setValue("block_links", self.block_links)
        self.settings.setValue("blocked_url", self.blocked_url)
        self.settings.setValue("tab_mode", self.tab_mode)
        self.settings.setValue("home_url", self.home_url)

    def load_settings(self):
        self.block_downloads = self.settings.value("block_downloads", False, type=bool)
        self.block_links = self.settings.value("block_links", False, type=bool)
        self.blocked_url = self.settings.value("blocked_url", "")
        self.tab_mode = self.settings.value("tab_mode", False, type=bool)
        self.home_url = self.settings.value("home_url", "https://www.google.com/")

app = QApplication(sys.argv)
app.setWindowIcon(QIcon(os.path.abspath("ICO.ico")))
QApplication.setApplicationName('VALDA Browser')
window = MainWindow()
app.exec_()
