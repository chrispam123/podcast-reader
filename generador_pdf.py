# generador_pdf.py
# Módulo encargado de convertir la transcripción diarizada
# en un archivo PDF limpio y legible en cualquier visor de PDF

import os
from datetime import datetime
from fpdf import FPDF


def _normalizar_texto_pdf(texto: str) -> str:
    """
    Convierte caracteres Unicode comunes a equivalentes compatibles con
    fuentes base de FPDF (latin-1).
    """
    reemplazos = {
        "–": "-",
        "—": "-",
        "…": "...",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "-",
        "\u00a0": " ",
    }
    texto_normalizado = texto
    for origen, destino in reemplazos.items():
        texto_normalizado = texto_normalizado.replace(origen, destino)

    return texto_normalizado.encode("latin-1", errors="replace").decode("latin-1")


def _partir_tokens_largos(texto: str, max_largo_token: int = 60) -> str:
    """
    Inserta espacios en tokens extremadamente largos para evitar errores de salto
    de línea en FPDF cuando no existe espacio horizontal suficiente.
    """
    tokens = texto.split(" ")
    tokens_ajustados: list[str] = []

    for token in tokens:
        if len(token) <= max_largo_token:
            tokens_ajustados.append(token)
            continue

        partes = [token[i : i + max_largo_token] for i in range(0, len(token), max_largo_token)]
        tokens_ajustados.append(" ".join(partes))

    return " ".join(tokens_ajustados)

class GeneradorPodcastPDF(FPDF):
    """
    Clase que extiende FPDF para personalizar el diseño del PDF.
    Hereda de FPDF para poder sobreescribir header y footer.
    """
    
    def __init__(self, titulo_podcast: str = "Podcast Transcript"):
        # Inicializar la clase padre con orientación vertical y tamaño carta
        super().__init__(orientation="P", unit="mm", format="A4")
        
        # Guardar el título para usarlo en el encabezado
        self.titulo_podcast = _normalizar_texto_pdf(titulo_podcast)
        
        # Márgenes: izquierda, arriba, derecha
        self.set_margins(20, 25, 20)
        
        # Salto de página automático con margen inferior
        self.set_auto_page_break(auto=True, margin=20)
    
    def header(self):
        """
        Encabezado deshabilitado para evitar texto repetido en cada página.
        """
        return
    
    def footer(self):
        """
        Pie de página con número de página centrado.
        """
        # Posicionarse a 15mm del fondo
        self.set_y(-15)
        
        # Fuente pequeña para el footer
        self.set_font("Helvetica", style="I", size=8)
        
        # Color gris
        self.set_text_color(150, 150, 150)
        
        # Número de página centrado
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def procesar_lineas(texto_diarizado: str) -> list:
    """
    Convierte el texto diarizado en una lista de tuplas (tipo, contenido).
    tipo puede ser: 'etiqueta' (ENTREVISTADOR/INVITADO) o 'texto'
    Esto facilita aplicar estilos diferentes a cada parte.
    """
    lineas = texto_diarizado.strip().split("\n")
    resultado = []
    
    for linea in lineas:
        linea = linea.strip()
        
        # Ignorar líneas vacías
        if not linea:
            continue
        
        # Detectar si la línea es una etiqueta de hablante
        if linea in ("ENTREVISTADOR", "INVITADO"):
            resultado.append(("etiqueta", linea))
        else:
            resultado.append(("texto", linea))
    
    return resultado


def generar_pdf(
    texto_diarizado: str,
    titulo_podcast: str = "Podcast Transcript",
    ruta_salida: str | None = None,
) -> str:
    """
    Genera el PDF final a partir del texto diarizado.
    Guarda el resultado en outputs/podcast_final.pdf
    Retorna la ruta del archivo generado.
    """
    print("Iniciando generación del PDF...")
    
    # Crear instancia del generador con el título del podcast
    pdf = GeneradorPodcastPDF(titulo_podcast=titulo_podcast)
    
    # Agregar primera página
    pdf.add_page()
    
    # Título principal en la primera página
    pdf.set_font("Helvetica", style="B", size=18)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(
        0,
        15,
        _partir_tokens_largos(_normalizar_texto_pdf(titulo_podcast)),
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(5)
    
    # Procesar el texto diarizado en líneas clasificadas
    lineas = procesar_lineas(texto_diarizado)
    
    for tipo, contenido in lineas:
        
        if tipo == "etiqueta":
            # Espacio antes de cada etiqueta para separar visualmente los turnos
            pdf.ln(4)
            pdf.set_x(pdf.l_margin)
            
            # Color diferente para cada hablante para identificarlos visualmente
            if contenido == "ENTREVISTADOR":
                # Azul oscuro para el entrevistador
                pdf.set_text_color(0, 70, 130)
            else:
                # Verde oscuro para el invitado
                pdf.set_text_color(0, 110, 60)
            
            # Etiqueta en negrita y tamaño ligeramente mayor
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.cell(
                0,
                7,
                _partir_tokens_largos(_normalizar_texto_pdf(contenido)),
                new_x="LMARGIN",
                new_y="NEXT",
            )
        
        else:
            # Texto normal del hablante en color negro estándar
            pdf.set_text_color(40, 40, 40)
            pdf.set_font("Helvetica", size=10)
            pdf.set_x(pdf.l_margin)
            
            # multi_cell permite que el texto haga salto de línea automático
            # cuando llega al margen derecho
            pdf.multi_cell(0, 6, _partir_tokens_largos(_normalizar_texto_pdf(contenido)))
    
    # Crear la carpeta outputs/ si no existe
    os.makedirs("outputs", exist_ok=True)
    
    # Guardar el PDF en la carpeta outputs
    if not ruta_salida:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_salida = f"outputs/podcast_final_{timestamp}.pdf"
    pdf.output(ruta_salida)
    
    print(f"PDF generado correctamente en: {ruta_salida}")
    
    return ruta_salida