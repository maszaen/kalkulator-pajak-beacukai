import os
import sys
import json
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
    QSpacerItem,
    QSizePolicy,
    QDialogButtonBox,
    QFormLayout,
    QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor, QAction
from PySide6.QtGui import QIcon


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

        form_layout.addRow("Kurs Pajak (IDR/USD):", self.kurs_input)
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
        self.setMinimumSize(1200, 900)

        self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        self.load_config()

        # Set application icon
        self.setWindowIcon(QIcon("./favicon.ico"))

        # Setup UI
        self.setup_ui()
        self.setup_menu()

        # Data storage
        self.data = {}
        self.load_data()

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
                    "KURS_PAJAK": float(dialog.kurs_input.text()),
                    "PEMBEBASAN": float(dialog.batas_input.text()),
                    "NPWP": dialog.npwp_checkbox.isChecked(),
                }

                # Update config
                self.KURS_PAJAK = new_config["KURS_PAJAK"]
                self.PEMBEBASAN = new_config["PEMBEBASAN"]
                self.NPWP = new_config["NPWP"]

                # Update UI labels
                self.info_labels[0].setText(f"Kurs Pajak: Rp {self.KURS_PAJAK:,.2f}")
                self.info_labels[1].setText(
                    f"Batas Pembebasan: USD {self.PEMBEBASAN:,.2f}"
                )
                self.info_labels[2].setText(
                    "Status NPWP: Ada" if self.NPWP else "Status NPWP: Tidak Ada"
                )

                # Save to file
                with open(self.config_path, "w") as f:
                    json.dump(new_config, f, indent=4)

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Gagal menyimpan konfigurasi: {str(e)}"
                )

    def load_config(self):
        default_config = {"KURS_PAJAK": 16275.0, "PEMBEBASAN": 500.0, "NPWP": True}

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)

                # Validate config
                self.KURS_PAJAK = float(
                    config.get("KURS_PAJAK", default_config["KURS_PAJAK"])
                )
                self.PEMBEBASAN = float(
                    config.get("PEMBEBASAN", default_config["PEMBEBASAN"])
                )
                self.NPWP = bool(config.get("NPWP", default_config["NPWP"]))
            else:
                self.KURS_PAJAK = default_config["KURS_PAJAK"]
                self.PEMBEBASAN = default_config["PEMBEBASAN"]
                self.NPWP = default_config["NPWP"]
                # Create config file
                with open(self.config_path, "w") as f:
                    json.dump(default_config, f, indent=4)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat konfigurasi: {str(e)}")
            # Use default config and overwrite corrupt file
            self.KURS_PAJAK = default_config["KURS_PAJAK"]
            self.PEMBEBASAN = default_config["PEMBEBASAN"]
            self.NPWP = default_config["NPWP"]
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=4)

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # # Title
        # title_label = QLabel("Kalkulator Pajak Bea Cukai")
        # title_font = QFont()
        # title_font.setPointSize(16)
        # title_font.setBold(True)
        # title_label.setFont(title_font)
        # title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # layout.addWidget(title_label)

        # Form container
        form_container = QFrame()
        form_container.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        form_container.setLineWidth(1)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_container.setStyleSheet("background-color: white;")
        form_layout.setSpacing(10)

        # Form input
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
        harga_layout.addWidget(harga_label)
        harga_layout.addWidget(self.harga_input)

        self.hitung_button = QPushButton("Hitung Pajak")

        form_layout.addLayout(nama_layout)
        form_layout.addLayout(harga_layout)
        form_layout.addWidget(self.hitung_button)
        layout.addWidget(form_container)

        button_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Hapus")

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

        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)

        # Info
        info_layout = QHBoxLayout()
        self.info_labels = [
            QLabel(f"Kurs Pajak: Rp {self.KURS_PAJAK:,}"),
            QLabel(f"Batas Pembebasan: USD {self.PEMBEBASAN}"),
            QLabel("Status NPWP: Ada" if self.NPWP else "Status NPWP: Tidak Ada"),
        ]
        for label in self.info_labels:
            label.setFont(QFont("Arial", 9))
            label.setStyleSheet("color: #666666;")
            info_layout.addWidget(label)

        # Tabel
        # table_label = QLabel("Hasil Perhitungan")
        # table_label.setStyleSheet("padding-top: 10px;")
        # table_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        # layout.addWidget(table_label)
        form_layout.addLayout(button_layout)

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
        layout.addWidget(self.table)
        layout.addLayout(info_layout)

        # Atur seleksi tabel
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # Sambungkan tombol ke fungsi
        self.hitung_button.clicked.connect(self.hitung_pajak)
        self.edit_button.clicked.connect(self.edit_entry)
        self.delete_button.clicked.connect(self.delete_entry)

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

            # Konversi ke USD
            harga_usd = harga_idr / self.KURS_PAJAK
            selisih_pembebasan = max(0, harga_usd - self.PEMBEBASAN)

            # Kalkulasi pajak
            bea_masuk = selisih_pembebasan * 0.10
            nilai_impor = selisih_pembebasan + bea_masuk

            ppn_usd = nilai_impor * 0.11
            ppn_idr = int(ppn_usd * self.KURS_PAJAK)

            pph_usd = nilai_impor * (0.10 if self.NPWP else 0.20)
            pph_idr = int(pph_usd * self.KURS_PAJAK)

            total_usd = bea_masuk + ppn_usd + pph_usd
            total_idr = int(total_usd * self.KURS_PAJAK)

            # Simpan data
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
            # self.statusBar().showMessage("Perhitungan berhasil!", 3000)

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
            with open("pajak_data.json", "r") as f:
                self.data = json.load(f)
            self.update_table()
        except:
            pass

    def save_data(self):
        with open("pajak_data.json", "w") as f:
            json.dump(self.data, f, indent=4)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = BeaCukaiApp()
    window.show()
    sys.exit(app.exec())


# Reguler :

# 1 jt rupiah per unit : xr - 13 pro
# 1.3 jt rupiah per unit : 13 pm  - 15 pm

# Pajak :

# Xr : free
# 11 : free
# 11 pro : free - 300
# 11 promax : free - 300
# 12 : free - 300
# 12 pro : 150 - 350
# 12 promax : 300 - 500
# 13 128 : free - 350
# 13 pro : 450 - 650
# 13 pm : 500 - 800
