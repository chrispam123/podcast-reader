# generador_pdf.py
# Módulo encargado de convertir la transcripción diarizada
# en un archivo PDF limpio y legible en cualquier visor de PDF

import os
from fpdf import FPDF

class GeneradorPodcastPDF(FPDF):
    """
    Clase que extiende FPDF para personalizar el diseño del PDF.
    Hereda de FPDF para poder sobreescribir header y footer.
    """
    
    def __init__(self, titulo_podcast: str = "Podcast Transcript"):
        # Inicializar la clase padre con orientación vertical y tamaño carta
        super().__init__(orientation="P", unit="mm", format="A4")
        
        # Guardar el título para usarlo en el encabezado
        self.titulo_podcast = titulo_podcast
        
        # Márgenes: izquierda, arriba, derecha
        self.set_margins(20, 25, 20)
        
        # Salto de página automático con margen inferior
        self.set_auto_page_break(auto=True, margin=20)
    
    def header(self):
        """
        Encabezado que aparece en todas las páginas con el título del podcast.
        """
        # Fuente del encabezado: negrita, tamaño 10
        self.set_font("Helvetica", style="B", size=10)
        
        # Color gris para el encabezado para no distraer del contenido
        self.set_text_color(120, 120, 120)
        
        # Escribir el título centrado
        self.cell(0, 10, self.titulo_podcast, align="C", new_x="LMARGIN", new_y="NEXT")
        
        # Línea separadora debajo del encabezado
        self.set_draw_color(200, 200, 200)
        self.line(20, self.get_y(), 190, self.get_y())
        
        # Espacio después del encabezado
        self.ln(5)
    
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


def generar_pdf(texto_diarizado: str, titulo_podcast: str = "Podcast Transcript") -> str:
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
    pdf.cell(0, 15, titulo_podcast, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Procesar el texto diarizado en líneas clasificadas
    lineas = procesar_lineas(texto_diarizado)
    
    for tipo, contenido in lineas:
        
        if tipo == "etiqueta":
            # Espacio antes de cada etiqueta para separar visualmente los turnos
            pdf.ln(4)
            
            # Color diferente para cada hablante para identificarlos visualmente
            if contenido == "ENTREVISTADOR":
                # Azul oscuro para el entrevistador
                pdf.set_text_color(0, 70, 130)
            else:
                # Verde oscuro para el invitado
                pdf.set_text_color(0, 110, 60)
            
            # Etiqueta en negrita y tamaño ligeramente mayor
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.cell(0, 7, contenido, new_x="LMARGIN", new_y="NEXT")
        
        else:
            # Texto normal del hablante en color negro estándar
            pdf.set_text_color(40, 40, 40)
            pdf.set_font("Helvetica", size=10)
            
            # multi_cell permite que el texto haga salto de línea automático
            # cuando llega al margen derecho
            pdf.multi_cell(0, 6, contenido)
    
    # Crear la carpeta outputs/ si no existe
    os.makedirs("outputs", exist_ok=True)
    
    # Guardar el PDF en la carpeta outputs
    ruta_salida = "outputs/podcast_final.pdf"
    pdf.output(ruta_salida)
    
    print(f"PDF generado correctamente en: {ruta_salida}")
    
    return ruta_salida