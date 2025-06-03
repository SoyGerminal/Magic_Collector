import sys
import sqlite3
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QDialog, QDialogButtonBox, QLabel, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from database import obtener_colecciones, RUTA_BD
from scryfall import ScryFall
import os

class DialogoAgregarCarta(QDialog):
    def __init__(self, cartas, colecciones, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Carta a Colección")
        self.cartas = cartas
        self.colecciones = colecciones
        self.layout = QVBoxLayout()

        # ComboBox para seleccionar la carta
        self.label_carta = QLabel("Selecciona una carta:")
        self.combo_cartas = QComboBox()
        for carta in cartas:
            self.combo_cartas.addItem(f"{carta['name']} ({carta['set_name']})", carta)
        self.layout.addWidget(self.label_carta)
        self.layout.addWidget(self.combo_cartas)

        # ComboBox para seleccionar la colección
        self.label_coleccion = QLabel("Selecciona una colección:")
        self.combo_colecciones = QComboBox()
        for coleccion in colecciones:
            self.combo_colecciones.addItem(coleccion[1], coleccion[0])  # Nombre y ID
        self.layout.addWidget(self.label_coleccion)
        self.layout.addWidget(self.combo_colecciones)

        # Botones de aceptar/cancelar
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)
        self.layout.addWidget(self.botones)

        self.setLayout(self.layout)

    def obtener_seleccion(self):
        carta_seleccionada = self.combo_cartas.currentData()
        coleccion_id = self.combo_colecciones.currentData()
        return carta_seleccionada, coleccion_id


class MagicCollectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Magic Collector")
        self.resize(1000, 600)

        # Widget y layout principal
        self.widget_central = QWidget()
        self.setCentralWidget(self.widget_central)
        self.layout_principal = QHBoxLayout()
        self.widget_central.setLayout(self.layout_principal)

        # Columna izquierda con ancho fijo
        self.widget_izquierda = QWidget()
        self.layout_izquierda = QVBoxLayout()
        self.layout_izquierda.setAlignment(Qt.AlignTop)
        self.widget_izquierda.setLayout(self.layout_izquierda)
        self.widget_izquierda.setFixedWidth(300)

        # Logotipo de Magic
        self.logo_label = QLabel()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "src", "App_images", "magic-logo.webp")  # Corregido a magic-logo.webp
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(200, 200, Qt.KeepAspectRatio)
            self.logo_label.setPixmap(pixmap)
            self.logo_label.setAlignment(Qt.AlignCenter)
        else:
            self.logo_label.setText(f"Logotipo no encontrado en: {logo_path}")
        self.layout_izquierda.addWidget(self.logo_label)

        # Botones de navegación
        self.boton_ver_coleccion = QPushButton("Ver colección")
        self.boton_ver_coleccion.clicked.connect(self.mostrar_colecciones)
        self.layout_izquierda.addWidget(self.boton_ver_coleccion)

        self.boton_agregar_cartas = QPushButton("Añadir cartas a la colección")
        self.boton_agregar_cartas.clicked.connect(self.mostrar_opcion_busqueda)
        self.layout_izquierda.addWidget(self.boton_agregar_cartas)

        # Relación de cartas (placeholder por ahora)
        self.label_relacion_cartas = QLabel("Cartas: 0 / 25000")
        self.label_relacion_cartas.setAlignment(Qt.AlignCenter)
        self.layout_izquierda.addWidget(self.label_relacion_cartas)

        # Espaciador para centrar verticalmente
        self.layout_izquierda.addStretch()

        # Botones inferiores
        self.layout_botones_inferiores = QHBoxLayout()
        self.boton_cerrar = QPushButton("Cerrar")
        self.boton_cerrar.clicked.connect(self.close)
        self.layout_botones_inferiores.addWidget(self.boton_cerrar)

        self.boton_settings = QPushButton("Settings")
        self.boton_settings.setEnabled(False)
        self.layout_botones_inferiores.addWidget(self.boton_settings)

        self.layout_izquierda.addLayout(self.layout_botones_inferiores)

        # Añadir columna izquierda al layout principal
        self.layout_principal.addWidget(self.widget_izquierda)

        # Columna derecha
        self.layout_derecha = QVBoxLayout()

        # Tabla para mostrar datos
        self.tabla = QTableWidget()
        self.layout_derecha.addWidget(self.tabla)

        # Layout para búsqueda de cartas
        self.layout_busqueda = QHBoxLayout()
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar carta (ejemplo: Castle)...")
        self.boton_buscar = QPushButton("Buscar Carta")
        self.boton_buscar.clicked.connect(self.buscar_cartas)
        self.layout_busqueda.addWidget(self.input_busqueda)
        self.layout_busqueda.addWidget(self.boton_buscar)
        self.layout_derecha.addLayout(self.layout_busqueda)
        # Ocultar el layout de búsqueda al inicio
        self.input_busqueda.setVisible(False)
        self.boton_buscar.setVisible(False)

        # Añadir columna derecha al layout principal
        self.layout_principal.addLayout(self.layout_derecha)

        # Instancia de la API
        self.scryfall = ScryFall()

        # Mostrar colecciones por defecto
        self.mostrar_colecciones()

    def mostrar_colecciones(self):
        self.input_busqueda.setVisible(False)
        self.boton_buscar.setVisible(False)

        self.tabla.clear()
        self.tabla.setRowCount(0)
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Código", "Fecha de Salida", "Total Cartas"])

        colecciones = obtener_colecciones()
        self.tabla.setRowCount(len(colecciones))
        for i, coleccion in enumerate(colecciones):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(coleccion[0])))
            self.tabla.setItem(i, 1, QTableWidgetItem(coleccion[1]))
            self.tabla.setItem(i, 2, QTableWidgetItem(coleccion[2]))
            self.tabla.setItem(i, 3, QTableWidgetItem(coleccion[3]))
            self.tabla.setItem(i, 4, QTableWidgetItem(str(coleccion[4]) if coleccion[4] else "N/A"))

        self.tabla.resizeColumnsToContents()

    def mostrar_opcion_busqueda(self):
        self.input_busqueda.setVisible(True)
        self.boton_buscar.setVisible(True)
        self.input_busqueda.clear()
        self.tabla.clear()
        self.tabla.setRowCount(0)

    def buscar_cartas(self):
        query = self.input_busqueda.text().strip()
        if not query:
            QMessageBox.warning(self, "Advertencia", "Por favor, ingresa un nombre de carta para buscar.")
            return

        cartas = self.scryfall.buscar_cartas(query)
        if not cartas:
            QMessageBox.information(self, "Información", f"No se encontraron cartas con el nombre '{query}'.")
            return

        self.tabla.clear()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Colección", "Número", "Colores", "Rareza"])
        self.tabla.setRowCount(len(cartas))

        for i, carta in enumerate(cartas):
            self.tabla.setItem(i, 0, QTableWidgetItem(carta["name"]))
            self.tabla.setItem(i, 1, QTableWidgetItem(carta["set_name"]))
            self.tabla.setItem(i, 2, QTableWidgetItem(carta["number"] if carta["number"] else "N/A"))
            self.tabla.setItem(i, 3, QTableWidgetItem(carta["colors"] if carta["colors"] else "N/A"))
            self.tabla.setItem(i, 4, QTableWidgetItem(carta["rarity"] if carta["rarity"] else "N/A"))

        self.tabla.resizeColumnsToContents()

        colecciones = obtener_colecciones()
        if not colecciones:
            QMessageBox.warning(self, "Advertencia", "No hay colecciones disponibles. Sincroniza primero.")
            return

        dialogo = DialogoAgregarCarta(cartas, colecciones, self)
        if dialogo.exec():
            carta_seleccionada, coleccion_id = dialogo.obtener_seleccion()
            self.agregar_carta_a_coleccion(carta_seleccionada, coleccion_id)

    def agregar_carta_a_coleccion(self, carta, coleccion_id):
        conn = sqlite3.connect(RUTA_BD, timeout=15)
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR IGNORE INTO cartas 
            (scryfall_id, nombre, coleccion_id, numero_serie, imagen_url, color, rareza, obtenida)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                carta["id"],
                carta["name"],
                coleccion_id,
                carta["number"] if carta["number"] else "N/A",
                carta["image_url"],
                carta["colors"],
                carta["rarity"],
                1
            ))
            conn.commit()
            QMessageBox.information(self, "Éxito", f"Carta '{carta['name']}' añadida a la colección.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Error al añadir carta: {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MagicCollectionApp()
    ventana.show()
    sys.exit(app.exec())