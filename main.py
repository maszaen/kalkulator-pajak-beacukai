import os
import sys
import json
import shutil
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QDialog,
    QHeaderView,
    QFrame,
    QDialogButtonBox,
    QFormLayout,
    QCheckBox,
    QTreeView,
    QMenu,
    QInputDialog,
    QFileDialog,
    QFileSystemModel,
)
from PySide6.QtCore import Qt, QRegularExpression, QDir, QSortFilterProxyModel
from PySide6.QtGui import (
    QFont,
    QAction,
    QRegularExpressionValidator,
    QIcon,
)


class FileFilterProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        source_model = self.sourceModel()
        index = source_model.index(source_row, 0, source_parent)
        file_name = source_model.fileName(index)

        # Blokir config.json dan sembunyikan folder sistem
        if file_name == "config.json" or file_name.startswith("."):
            return False

        return super().filterAcceptsRow(source_row, source_parent)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            source_index = self.mapToSource(index)
            name = self.sourceModel().fileName(source_index)

            # Hapus ekstensi .json untuk file
            if not self.sourceModel().isDir(source_index):
                if name.endswith(".json"):
                    return name[:-5]

            return name

        return super().data(index, role)


class BeaCukaiApp(QMainWindow):
    def __init__(self):
        # ...
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.script_dir)
        self.file_model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.file_model.setNameFilters(["*.json"])
        self.file_model.setNameFilterDisables(False)
        # ...


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Konfigurasi")
        self.setWindowIcon(QIcon("./favicon.ico"))
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.kurs_input = QLineEdit()
        self.batas_input = QLineEdit()
        self.npwp_checkbox = QCheckBox("Memiliki NPWP")

        form_layout.addRow("Kurs Pajak (IDR):", self.kurs_input)
        form_layout.addRow("Batas Pembebasan (USD):", self.batas_input)
        form_layout.addRow(self.npwp_checkbox)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(buttons)

    def validate(self):
        try:
            float(self.kurs_input.text())
            float(self.batas_input.text())
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Error", "Input harus berupa angka!")


class BeaCukaiApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_edit_name = None
        self.setWindowTitle("Kalkulator Pajak Bea Cukai")
        self.setMinimumSize(1400, 900)

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.script_dir, "config.json")

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.script_dir)
        self.file_model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.file_model.setNameFilters(["*.json"])
        self.file_model.setNameFilterDisables(False)

        self.proxy_model = FileFilterProxyModel()
        self.proxy_model.setSourceModel(self.file_model)

        self.load_config()
        self.init_current_data_file()

        self.setWindowIcon(QIcon("./favicon.ico"))
        self.setup_ui()
        self.setup_menu()
        self.load_data()

    def init_current_data_file(self):
        json_files = [
            f
            for f in os.listdir(self.script_dir)
            if f.endswith(".json") and f != "config.json"
        ]

        if os.path.exists(os.path.join(self.script_dir, self.LAST_OPENED_FILE)):
            self.current_data_file = os.path.join(
                self.script_dir, self.LAST_OPENED_FILE
            )
        else:
            if len(json_files) == 0:
                self.current_data_file = os.path.join(
                    self.script_dir, "pajak_data.json"
                )
                with open(self.current_data_file, "w") as f:
                    json.dump({}, f)
                self.LAST_OPENED_FILE = "pajak_data.json"
                self.save_config()
            elif len(json_files) == 1:
                self.current_data_file = os.path.join(self.script_dir, json_files[0])
                self.LAST_OPENED_FILE = json_files[0]
                self.save_config()
            else:
                most_recent = max(
                    json_files,
                    key=lambda f: os.path.getmtime(os.path.join(self.script_dir, f)),
                )
                self.current_data_file = os.path.join(self.script_dir, most_recent)
                self.LAST_OPENED_FILE = most_recent
                self.save_config()

    def setup_menu(self):
        menu_bar = self.menuBar()
        config_menu = menu_bar.addMenu("Konfigurasi")

        config_action = QAction("Pengaturan", self)
        config_action.triggered.connect(self.show_config_dialog)
        config_menu.addAction(config_action)

    def show_config_dialog(self):
        dialog = ConfigDialog(self)
        dialog.kurs_input.setText(str(self.KURS_PAJAK))
        dialog.batas_input.setText(str(self.PEMBEBASAN))
        dialog.npwp_checkbox.setChecked(self.NPWP)

        if dialog.exec() == QDialog.Accepted:
            try:
                new_config = {
                    "KURS_PAJAK": int(dialog.kurs_input.text()),
                    "PEMBEBASAN": int(dialog.batas_input.text()),
                    "NPWP": dialog.npwp_checkbox.isChecked(),
                    "LAST_OPENED_FILE": self.LAST_OPENED_FILE,
                }

                self.KURS_PAJAK = new_config["KURS_PAJAK"]
                self.PEMBEBASAN = new_config["PEMBEBASAN"]
                self.NPWP = new_config["NPWP"]

                with open(self.config_path, "w") as f:
                    json.dump(new_config, f, indent=4)

                self.setup_ui()
                self.data = {}
                self.load_data()

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Gagal menyimpan konfigurasi: {str(e)}"
                )

    def load_config(self):
        default_config = {
            "KURS_PAJAK": 16275,
            "PEMBEBASAN": 500,
            "NPWP": True,
            "LAST_OPENED_FILE": "pajak_data.json",
        }

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)

                self.KURS_PAJAK = int(
                    config.get("KURS_PAJAK", default_config["KURS_PAJAK"])
                )
                self.PEMBEBASAN = int(
                    config.get("PEMBEBASAN", default_config["PEMBEBASAN"])
                )
                self.NPWP = bool(config.get("NPWP", default_config["NPWP"]))
                self.LAST_OPENED_FILE = config.get(
                    "LAST_OPENED_FILE", default_config["LAST_OPENED_FILE"]
                )
            else:
                self.KURS_PAJAK = default_config["KURS_PAJAK"]
                self.PEMBEBASAN = default_config["PEMBEBASAN"]
                self.NPWP = default_config["NPWP"]
                self.LAST_OPENED_FILE = default_config["LAST_OPENED_FILE"]
                with open(self.config_path, "w") as f:
                    json.dump(default_config, f, indent=4)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat konfigurasi: {str(e)}")
            self.KURS_PAJAK = default_config["KURS_PAJAK"]
            self.PEMBEBASAN = default_config["PEMBEBASAN"]
            self.NPWP = default_config["NPWP"]
            self.LAST_OPENED_FILE = default_config["LAST_OPENED_FILE"]
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=4)

    def setup_ui(self):
        # Main container
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Top row container
        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(20)
        top_container.setMaximumHeight(280)

        # Navigation pane (with white background)
        nav_container = QWidget()
        nav_container.setStyleSheet(
            "background-color: white; border: 1px solid #C9CCD3;"
        )
        nav_container.setMaximumWidth(200)
        nav_container.setMaximumHeight(280)
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(20, 20, 20, 20)
        nav_layout.setSpacing(5)

        # Navigation content
        self.active_db_label = QLabel()
        self.active_db_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.active_db_label.setContentsMargins(0, 0, 0, 10)
        self.active_db_label.setStyleSheet("border: none;")
        self.active_db_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.update_active_db_label()
        nav_layout.addWidget(self.active_db_label)

        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_container.setStyleSheet("border: none;")
        btn_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_add_db = QPushButton("+ Data")
        self.btn_add_folder = QPushButton("+ Folder")
        self.btn_add_db.clicked.connect(self.tambah_database)
        self.btn_add_folder.clicked.connect(self.tambah_folder)

        btn_layout.addWidget(self.btn_add_db)
        btn_layout.addWidget(self.btn_add_folder)
        self.btn_add_db.setStyleSheet(
            """
            QPushButton {
                border: none;
                background-color: #f0f0f0; 
                padding: 5px 10px; 
                border: 1px solid #C9CCD3;
            }
            
            QPushButton:hover { 
                background-color: #e0e0e0; 
            }
            """
        )

        self.btn_add_folder.setStyleSheet(
            """
            QPushButton {
                border: none; 
                background-color: #f0f0f0; 
                padding: 5px 10px; 
                border: 1px solid #C9CCD3;
            }
            
            QPushButton:hover { 
                background-color: #e0e0e0; 
            }
            """
        )

        self.btn_add_folder.setCursor(Qt.PointingHandCursor)
        self.btn_add_db.setCursor(Qt.PointingHandCursor)

        nav_layout.addWidget(btn_container)

        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setRootIndex(
            self.proxy_model.mapFromSource(self.file_model.index(self.script_dir))
        )

        self.tree_view.setColumnWidth(0, 120)
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.doubleClicked.connect(self.on_tree_double_click)

        nav_layout.addWidget(self.tree_view)

        # Form and Preview container (with white background)
        form_preview_container = QWidget()
        form_preview_container.setStyleSheet("background-color: white;")
        form_preview_layout = QHBoxLayout(form_preview_container)
        form_preview_layout.setContentsMargins(10, 10, 10, 10)
        form_preview_layout.setSpacing(20)

        # Form Container
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_preview_container.setStyleSheet(
            """
            QWidget {
                background-color: white; 
                border: 1px solid #C9CCD3;
            }
            
            QLabel, QPushButton {
                border: none;
            }
            
            QLineEdit {
                border: 1px solid #C9CCD3;
                border-radius: 3px;
                padding: 5px 10px;
                font-size: 11pt;
            }
            
            """
        )

        form_container.setStyleSheet(
            """
            QWidget {
                border: none;
            }
            QLineEdit {
                border: 1px solid #C9CCD3;
                border-radius: 3px;
                padding: 5px 10px;
                font-size: 11pt;
            }
          """
        )

        form_layout.setSpacing(10)

        nama_layout = QVBoxLayout()
        nama_label = QLabel("Nama Barang:")
        nama_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.nama_input = QLineEdit()
        self.nama_input.setMinimumHeight(35)
        self.nama_input.setFont(QFont("Arial", 10))
        nama_layout.addWidget(nama_label)
        nama_layout.addWidget(self.nama_input)

        harga_layout = QVBoxLayout()
        harga_label = QLabel("Harga (IDR):")
        harga_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        harga_label.setContentsMargins(0, 10, 0, 0)
        self.harga_input = QLineEdit()
        self.harga_input.setMinimumHeight(45)
        self.harga_input.setFont(QFont("Arial", 10))
        self.harga_input.setContentsMargins(0, 0, 0, 10)
        self.harga_input.setValidator(
            QRegularExpressionValidator(QRegularExpression("[0-9]*"))
        )
        self.harga_input.textChanged.connect(self.update_preview)
        harga_layout.addWidget(harga_label)
        harga_layout.addWidget(self.harga_input)

        form_layout.addLayout(nama_layout)
        form_layout.addLayout(harga_layout)

        button_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Hapus")
        self.hitung_button = QPushButton("Simpan Data")

        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:pressed { background-color: #0D47A1; }
        """

        sec_button_style = """
          QPushButton {
            background-color: #5b5b5b;
            color: white;
            border: 1px solid #d3d3d3;
            border-radius: 3px;
            padding: 5px 15px;
          }
          QPushButton:hover {
            background-color: #2196F3;
          }
          QPushButton:pressed { 
            background-color: #d3d3d3;
          }
        """

        for btn in [self.hitung_button, self.edit_button, self.delete_button]:
            btn.setStyleSheet(button_style)
            btn.setMinimumHeight(35)
            btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        for btn in [self.edit_button, self.delete_button]:
            btn.setStyleSheet(sec_button_style)

        form_layout.addWidget(self.hitung_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        form_layout.addLayout(button_layout)

        # Preview Container
        preview_container = QWidget()
        preview_container.setFixedWidth(400)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setSpacing(0)
        preview_container.setStyleSheet(
            """
            QWidget {
                border: none;
            }
            QLabel {
                border-bottom: 1px solid #C9CCD3;
                border-radius: 0px;
                text-align: end;
                font-size: 11pt;
            }
          """
        )

        self.preview_labels = {
            "harga_barang": QLabel("Rp 0"),
            "selisih": QLabel("$ 0.00"),
            "bea_masuk": QLabel("$ 0.00"),
            "ppn": QLabel("Rp 0"),
            "pph": QLabel("Rp 0"),
            "total_usd": QLabel("$ 0.00"),
            "total_idr": QLabel("Rp 0"),
        }

        preview_items = [
            ("Harga Barang:", self.preview_labels["harga_barang"]),
            ("Selisih Pembebasan:", self.preview_labels["selisih"]),
            ("Bea Masuk (10%):", self.preview_labels["bea_masuk"]),
            ("PPN (11%):", self.preview_labels["ppn"]),
            (
                "PPh 22 (%s):" % ("10%" if self.NPWP else "20%"),
                self.preview_labels["pph"],
            ),
            ("Total Pajak (USD):", self.preview_labels["total_usd"]),
            ("Total Pajak (IDR):", self.preview_labels["total_idr"]),
        ]

        for title, value_label in preview_items:
            item_layout = QHBoxLayout()
            title_label = QLabel(title)
            title_label.setFont(QFont("Arial", 10))
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            value_label.setStyleSheet("color: #1976D2;")
            item_layout.addWidget(title_label)
            item_layout.addWidget(value_label)
            preview_layout.addLayout(item_layout)

        form_preview_layout.addWidget(form_container)
        form_preview_layout.addWidget(preview_container)

        # Add containers to top layout
        top_layout.addWidget(nav_container)
        top_layout.addWidget(form_preview_container)
        main_layout.addWidget(top_container)

        # Table container (bottom)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Nama Barang",
                "Harga (IDR)",
                "Selisih ($)",
                "Bea Masuk ($)",
                "PPN (IDR)",
                "PPh (IDR)",
                "Total ($)",
                "Total (IDR)",
            ]
        )
        self.table.setStyleSheet(
            """
            QTableWidget { 
              gridline-color: #d0d0d0;
              background: white; 
              border: 1px solid #d0d0d0; 
              border-radius: 5px; 
            }
            QHeaderView::section { 
              background: #f0f0f0; 
              padding: 0px; 
              border: 1px solid #d0d0d0; 
              font-size: 9pt;
              padding-left: 12px;
              padding-right: 12px;
            }
            QTableWidget::item { 
              padding: 0px;
              font-size: 10pt;
            }
        """
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(2, 8):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(1, 150)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        header.resizeSection(7, 150)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(4, 150)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.resizeSection(5, 150)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # Info Layout at bottom of table container
        self.info_layout = QHBoxLayout()
        info_pairs = [
            ("Kurs Pajak (USD): ", f"Rp {self.KURS_PAJAK:,}"),
            ("Batas Pembebasan: ", f"$ {self.PEMBEBASAN}"),
            ("Status NPWP: ", "Ada" if self.NPWP else "Tidak Ada"),
        ]

        self.info_labels = []
        for label_text, value_text in info_pairs:
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            container_layout.setContentsMargins(20, 0, 0, 0)
            container_layout.setSpacing(5)

            label = QLabel(label_text)
            label.setFont(QFont("Arial", 9))
            label.setStyleSheet("color: #666666;")

            value = QLabel(value_text)
            value.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            value.setStyleSheet("color: #666666;")

            container_layout.addWidget(label)
            container_layout.addWidget(value)
            self.info_labels.extend([label, value])
            container.setMaximumWidth(200)
            self.info_layout.addWidget(container)

        table_layout.addWidget(self.table)
        table_layout.addLayout(self.info_layout)
        main_layout.addWidget(table_container)

        # Connect buttons
        self.hitung_button.clicked.connect(self.hitung_pajak)
        self.edit_button.clicked.connect(self.edit_entry)
        self.delete_button.clicked.connect(self.delete_entry)

    def update_active_db_label(self):
        base_name = os.path.basename(self.current_data_file)
        formatted_name = base_name[:-5].replace("_", " ").title()
        self.active_db_label.setText(formatted_name)

    def get_selected_dir(self):
        indexes = self.tree_view.selectedIndexes()
        if indexes:
            index = self.proxy_model.mapToSource(indexes[0])
            path = self.file_model.filePath(index)
            if os.path.isdir(path):
                return path
            return os.path.dirname(path)
        return self.script_dir

    def tambah_database(self):
        parent_dir = self.get_selected_dir()

        dialog = QInputDialog(self)
        dialog.setWindowTitle("Buat Database")
        dialog.setLabelText("Masukkan nama database:                 ")

        if dialog.exec() == QDialog.Accepted:
            name = dialog.textValue()
            if name:
                file_path = os.path.join(parent_dir, f"{name}.json")
                if os.path.exists(file_path):
                    QMessageBox.warning(self, "Error", "File sudah ada!")
                    return
                try:
                    with open(file_path, "w") as f:
                        json.dump({}, f)
                    self.file_model.setRootPath(self.file_model.rootPath())
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Gagal membuat: {str(e)}")

    def tambah_folder(self):
        parent_dir = self.script_dir
        name, ok = QInputDialog.getText(self, "Buat Folder", "Nama folder:")
        if ok and name:
            folder_path = os.path.join(parent_dir, name)
            if os.path.exists(folder_path):
                QMessageBox.warning(self, "Error", "Folder sudah ada!")
                return
            try:
                os.mkdir(folder_path)
                self.file_model.setRootPath(self.file_model.rootPath())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal membuat: {str(e)}")

    def copy_file(self, src_path):
        dest_dir = QFileDialog.getExistingDirectory(
            self, "Pilih Folder Tujuan", self.script_dir
        )
        if not dest_dir:
            return

        base_name = os.path.basename(src_path)
        name, ext = os.path.splitext(base_name)
        counter = 1
        new_name = base_name
        while os.path.exists(os.path.join(dest_dir, new_name)):
            new_name = f"{name} ({counter}){ext}"
            counter += 1

        try:
            shutil.copy2(src_path, os.path.join(dest_dir, new_name))
            self.file_model.setRootPath(self.file_model.rootPath())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menyalin: {str(e)}")

    def on_tree_double_click(self, index):
        try:
            source_index = self.proxy_model.mapToSource(index)
            path = self.file_model.filePath(source_index)

            if (
                os.path.isfile(path)
                and path.endswith(".json")
                and os.path.basename(path) != "config.json"
            ):

                self.current_data_file = path
                self.LAST_OPENED_FILE = os.path.basename(path)
                self.save_config()
                self.load_data()
                self.update_active_db_label()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal membuka file: {str(e)}")

    def show_context_menu(self, pos):
        try:
            index = self.tree_view.indexAt(pos)
            if not index.isValid():
                return

            source_index = self.proxy_model.mapToSource(index)
            path = self.file_model.filePath(source_index)

            is_dir = os.path.isdir(path)
            is_file = os.path.isfile(path)
            menu = QMenu()

            if is_file and os.path.basename(path) != "config.json":
                copy_action = QAction("Salin", self)
                copy_action.triggered.connect(lambda: self.copy_file(path))
                move_action = QAction("Pindahkan", self)
                move_action.triggered.connect(lambda: self.move_file(path))
                delete_action = QAction("Hapus", self)
                delete_action.triggered.connect(lambda: self.delete_file(path))
                rename_action = QAction("Ganti Nama", self)
                rename_action.triggered.connect(lambda: self.rename_file(path))

                menu.addAction(copy_action)
                menu.addAction(move_action)
                menu.addAction(delete_action)
                menu.addAction(rename_action)

            elif is_dir:
                new_file_action = QAction("Buat File Baru", self)
                new_file_action.triggered.connect(lambda: self.create_new_file(path))
                new_folder_action = QAction("Buat Folder Baru", self)
                new_folder_action.triggered.connect(
                    lambda: self.create_new_folder(path)
                )
                rename_action = QAction("Ganti Nama", self)
                rename_action.triggered.connect(lambda: self.rename_folder(path))
                delete_action = QAction("Hapus", self)
                delete_action.triggered.connect(lambda: self.delete_folder(path))

                menu.addAction(new_file_action)
                menu.addAction(new_folder_action)
                menu.addAction(rename_action)
                menu.addAction(delete_action)

            menu.exec(self.tree_view.viewport().mapToGlobal(pos))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menampilkan menu: {str(e)}")

    def copy_file(self, src_path):
        dest_dir = QFileDialog.getExistingDirectory(
            self, "Pilih Folder Tujuan", self.script_dir
        )
        if not dest_dir:
            return

        file_name = os.path.basename(src_path)
        dest_path = os.path.join(dest_dir, file_name)

        if os.path.exists(dest_path):
            QMessageBox.warning(self, "Error", "File sudah ada di folder tujuan.")
            return

        try:
            shutil.copy2(src_path, dest_path)
            self.file_model.setRootPath(self.file_model.rootPath())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menyalin file: {str(e)}")

    def move_file(self, src_path):
        dest_dir = QFileDialog.getExistingDirectory(
            self, "Pilih Folder Tujuan", self.script_dir
        )
        if not dest_dir:
            return

        file_name = os.path.basename(src_path)
        dest_path = os.path.join(dest_dir, file_name)

        if os.path.exists(dest_path):
            QMessageBox.warning(self, "Error", "File sudah ada di folder tujuan.")
            return

        try:
            shutil.move(src_path, dest_path)
            self.file_model.setRootPath(self.file_model.rootPath())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memindahkan file: {str(e)}")

    def delete_file(self, path):
        confirm = QMessageBox.question(
            self,
            "Konfirmasi Penghapusan",
            f"Apakah Anda yakin ingin menghapus file {os.path.basename(path)}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            try:
                os.remove(path)
                self.file_model.setRootPath(self.file_model.rootPath())
                if path == self.current_data_file:
                    self.handle_current_file_deleted()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menghapus file: {str(e)}")

    def rename_file(self, path):
        new_name, ok = QInputDialog.getText(
            self,
            "Ganti Nama File",
            "Masukkan nama baru:",
            QLineEdit.Normal,
            os.path.basename(path),
        )
        if ok and new_name:
            if not new_name.endswith(".json"):
                new_name += ".json"
            dir_path = os.path.dirname(path)
            new_path = os.path.join(dir_path, new_name)
            if os.path.exists(new_path):
                QMessageBox.warning(self, "Error", "Nama file sudah ada.")
                return
            try:
                os.rename(path, new_path)
                self.file_model.setRootPath(self.file_model.rootPath())
                if path == self.current_data_file:
                    self.current_data_file = new_path
                    self.LAST_OPENED_FILE = os.path.basename(new_path)
                    self.save_config()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal mengganti nama: {str(e)}")

    def create_new_file(self, parent_dir):
        new_name, ok = QInputDialog.getText(
            self, "Buat File Baru", "Masukkan nama file (tanpa ekstensi):"
        )
        if ok and new_name:
            new_path = os.path.join(parent_dir, f"{new_name}.json")
            if os.path.exists(new_path):
                QMessageBox.warning(self, "Error", "File sudah ada.")
                return
            try:
                with open(new_path, "w") as f:
                    json.dump({}, f)
                self.file_model.setRootPath(self.file_model.rootPath())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal membuat file: {str(e)}")

    def create_new_folder(self, parent_dir):
        new_name, ok = QInputDialog.getText(
            self, "Buat Folder Baru", "Masukkan nama folder:"
        )
        if ok and new_name:
            new_path = os.path.join(parent_dir, new_name)
            if os.path.exists(new_path):
                QMessageBox.warning(self, "Error", "Folder sudah ada.")
                return
            try:
                os.mkdir(new_path)
                self.file_model.setRootPath(self.file_model.rootPath())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal membuat folder: {str(e)}")

    def rename_folder(self, path):
        new_name, ok = QInputDialog.getText(
            self,
            "Ganti Nama Folder",
            "Masukkan nama baru:",
            QLineEdit.Normal,
            os.path.basename(path),
        )
        if ok and new_name:
            parent_dir = os.path.dirname(path)
            new_path = os.path.join(parent_dir, new_name)
            if os.path.exists(new_path):
                QMessageBox.warning(self, "Error", "Nama folder sudah ada.")
                return
            try:
                os.rename(path, new_path)
                self.file_model.setRootPath(self.file_model.rootPath())
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Gagal mengganti nama folder: {str(e)}"
                )

    def delete_folder(self, path):
        if not os.listdir(path):
            confirm = QMessageBox.question(
                self,
                "Konfirmasi Penghapusan",
                f"Apakah Anda yakin ingin menghapus folder {os.path.basename(path)}?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                try:
                    os.rmdir(path)
                    self.file_model.setRootPath(self.file_model.rootPath())
                except Exception as e:
                    QMessageBox.critical(
                        self, "Error", f"Gagal menghapus folder: {str(e)}"
                    )
        else:
            QMessageBox.warning(
                self, "Error", "Folder tidak kosong. Tidak bisa dihapus."
            )

    def handle_current_file_deleted(self):
        json_files = [
            f
            for f in os.listdir(self.script_dir)
            if f.endswith(".json") and f != "config.json"
        ]
        if json_files:
            self.current_data_file = os.path.join(self.script_dir, json_files[0])
            self.LAST_OPENED_FILE = json_files[0]
            self.save_config()
            self.load_data()
        else:
            self.current_data_file = os.path.join(self.script_dir, "pajak_data.json")
            self.LAST_OPENED_FILE = "pajak_data.json"
            with open(self.current_data_file, "w") as f:
                json.dump({}, f)
            self.save_config()

    def save_config(self):
        config = {
            "KURS_PAJAK": self.KURS_PAJAK,
            "PEMBEBASAN": self.PEMBEBASAN,
            "NPWP": self.NPWP,
            "LAST_OPENED_FILE": self.LAST_OPENED_FILE,
        }
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=4)

    def update_preview(self):
        try:
            harga_text = self.harga_input.text().strip().replace(",", "")
            if not harga_text:
                self.clear_preview()
                return

            harga_idr = int(harga_text)
            if harga_idr <= 0:
                self.clear_preview()
                return

            harga_usd = harga_idr / self.KURS_PAJAK
            selisih_pembebasan = max(0, harga_usd - self.PEMBEBASAN)
            bea_masuk = selisih_pembebasan * 0.10
            nilai_impor = selisih_pembebasan + bea_masuk
            ppn_usd = nilai_impor * 0.11
            pph_usd = nilai_impor * (0.10 if self.NPWP else 0.20)
            total_usd = bea_masuk + ppn_usd + pph_usd

            self.preview_labels["harga_barang"].setText(f"Rp {harga_idr:,}")
            self.preview_labels["selisih"].setText(f"$ {selisih_pembebasan:,.2f}")
            self.preview_labels["bea_masuk"].setText(f"$ {bea_masuk:,.2f}")
            self.preview_labels["ppn"].setText(f"Rp {int(ppn_usd * self.KURS_PAJAK):,}")
            self.preview_labels["pph"].setText(f"Rp {int(pph_usd * self.KURS_PAJAK):,}")
            self.preview_labels["total_usd"].setText(f"$ {total_usd:,.2f}")
            self.preview_labels["total_idr"].setText(
                f"Rp {int(total_usd * self.KURS_PAJAK):,}"
            )

        except ValueError:
            self.clear_preview()

    def clear_preview(self):
        for label in self.preview_labels.values():
            label.setText("Rp0" if "Rp" in label.text() else "$0.00")

    def delete_entry(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            nama = self.table.item(selected_row, 0).text()
            if nama in self.data:
                del self.data[nama]
                self.save_data()
                self.update_table()
        else:
            QMessageBox.warning(self, "Peringatan", "Pilih baris yang akan dihapus.")

    def edit_entry(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            original_name = self.table.item(selected_row, 0).text()
            if original_name in self.data:
                data = self.data[original_name]
                self.nama_input.setText(original_name)
                self.harga_input.setText(str(data["harga_idr"]))
                self.current_edit_name = original_name
        else:
            QMessageBox.warning(self, "Peringatan", "Pilih baris yang akan diedit.")

    def hitung_pajak(self):
        try:
            nama = self.nama_input.text().strip()
            if not nama:
                raise ValueError("Nama barang harus diisi")

            harga_text = self.harga_input.text().replace(",", "").strip()
            if not harga_text:
                raise ValueError("Harga harus diisi")
            if not harga_text.isdigit():
                raise ValueError("Harga harus berupa angka")

            harga_idr = int(harga_text)
            if harga_idr <= 0:
                raise ValueError("Harga harus > 0")

            if self.current_edit_name:
                if self.current_edit_name in self.data:
                    del self.data[self.current_edit_name]
                self.current_edit_name = None

            harga_usd = harga_idr / self.KURS_PAJAK
            selisih_pembebasan = max(0, harga_usd - self.PEMBEBASAN)
            bea_masuk = selisih_pembebasan * 0.10
            nilai_impor = selisih_pembebasan + bea_masuk
            ppn_usd = nilai_impor * 0.11
            ppn_idr = int(ppn_usd * self.KURS_PAJAK)
            pph_usd = nilai_impor * (0.10 if self.NPWP else 0.20)
            pph_idr = int(pph_usd * self.KURS_PAJAK)
            total_usd = bea_masuk + ppn_usd + pph_usd
            total_idr = int(total_usd * self.KURS_PAJAK)

            self.data[nama] = {
                "harga_idr": harga_idr,
                "selisih_pembebasan": selisih_pembebasan,
                "bea_masuk": bea_masuk,
                "ppn_idr": ppn_idr,
                "pph_idr": pph_idr,
                "total_usd": total_usd,
                "total_idr": total_idr,
            }

            self.save_data()
            self.update_table()
            self.clear_inputs()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Kesalahan sistem: {str(e)}")

    def update_table(self):
        self.table.setRowCount(len(self.data))
        for row, (nama, data) in enumerate(self.data.items()):
            items = [
                QTableWidgetItem(nama),
                QTableWidgetItem(f"Rp {data['harga_idr']:,}"),
                QTableWidgetItem(f"$ {data['selisih_pembebasan']:,.2f}"),
                QTableWidgetItem(f"$ {data['bea_masuk']:,.2f}"),
                QTableWidgetItem(f"Rp {data['ppn_idr']:,}"),
                QTableWidgetItem(f"Rp {data['pph_idr']:,}"),
                QTableWidgetItem(f"$ {data['total_usd']:,.2f}"),
                QTableWidgetItem(f"Rp {data['total_idr']:,}"),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(
                    Qt.AlignRight | Qt.AlignVCenter
                    if col > 0
                    else Qt.AlignLeft | Qt.AlignVCenter
                )
                self.table.setItem(row, col, item)
        self.table.scrollToBottom()

    def clear_inputs(self):
        self.nama_input.clear()
        self.harga_input.clear()

    def load_data(self):
        try:
            if not os.path.exists(self.current_data_file):
                self.data = {}
                self.save_data()
                return

            with open(self.current_data_file, "r") as f:
                self.data = json.load(f)
            self.update_table()
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Warning", "File data rusak. Membuat data baru.")
            self.data = {}
            self.save_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat data: {str(e)}")
            self.data = {}

    def save_data(self):
        with open(self.current_data_file, "w") as f:
            json.dump(self.data, f, indent=4)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = BeaCukaiApp()
    window.show()
    sys.exit(app.exec())
