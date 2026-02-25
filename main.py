# main.py
# Punto de entrada principal del proyecto podcast-reader
# Orquesta el pipeline completo: extracción → diarización → PDF
# Uso: python main.py "URL_del_video_de_youtube"

import sys
import os
from extractor import extraer_transcripcion
from diarizador import diarizar_transcripcion
from generador_pdf import generar_pdf

def main():
    """
    Función principal que ejecuta el pipeline completo.
    Recibe la URL del video como argumento desde la terminal.
    """
    
    # Verificar que el usuario pasó la URL como argumento
    if len(sys.argv) < 2:
        print("Error: debes proporcionar la URL del video de YouTube.")
        print("Uso: python main.py \"https://www.youtube.com/watch?v=XXXXXXX\"")
        sys.exit(1)
    
    # Obtener la URL desde los argumentos de la terminal
    url = sys.argv[1]
    
    # Obtener el título del podcast desde los argumentos opcionales
    # Si no se proporciona, usa un título genérico
    titulo = sys.argv[2] if len(sys.argv) > 2 else "Podcast Transcript"
    
    print("=" * 60)
    print("PODCAST READER - Pipeline de transcripción")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Título: {titulo}")
    print("=" * 60)
    
    # PASO 1: Extraer transcripción desde YouTube
    print("\n[PASO 1/3] Extrayendo transcripción de YouTube...")
    
    # Verificar si ya existe una transcripción cruda guardada
    # para evitar llamadas innecesarias a YouTube
    ruta_cruda = "outputs/transcripcion_cruda.txt"
    
    if os.path.exists(ruta_cruda):
        # Si ya existe, leerla directamente sin volver a descargar
        print(f"Transcripción cruda ya existe en {ruta_cruda}, usando archivo existente.")
        with open(ruta_cruda, "r", encoding="utf-8") as archivo:
            transcripcion_cruda = archivo.read()
    else:
        # Si no existe, extraerla desde YouTube
        transcripcion_cruda = extraer_transcripcion(url)
    
    print(f"✓ Transcripción cruda lista ({len(transcripcion_cruda)} caracteres)")
    
    # PASO 2: Diarizar la transcripción con Gemini
    print("\n[PASO 2/3] Diarizando transcripción con Gemini...")
    
    # Verificar si ya existe una transcripción diarizada guardada
    # para evitar llamadas innecesarias a la API de Gemini
    ruta_diarizada = "outputs/transcripcion_diarizada.txt"
    
    if os.path.exists(ruta_diarizada):
        # Si ya existe, leerla directamente sin volver a llamar a Gemini
        print(f"Transcripción diarizada ya existe en {ruta_diarizada}, usando archivo existente.")
        with open(ruta_diarizada, "r", encoding="utf-8") as archivo:
            transcripcion_diarizada = archivo.read()
    else:
        # Si no existe, diarizarla con Gemini
        transcripcion_diarizada = diarizar_transcripcion(transcripcion_cruda)
    
    print(f"✓ Transcripción diarizada lista ({len(transcripcion_diarizada)} caracteres)")
    
    # PASO 3: Generar el PDF final
    print("\n[PASO 3/3] Generando PDF...")
    ruta_pdf = generar_pdf(transcripcion_diarizada, titulo_podcast=titulo)
    
    print(f"✓ PDF generado en: {ruta_pdf}")
    
    # Resumen final del pipeline
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETADO EXITOSAMENTE")
    print("=" * 60)
    print(f"  Transcripción cruda:    outputs/transcripcion_cruda.txt")
    print(f"  Transcripción diarizada: outputs/transcripcion_diarizada.txt")
    print(f"  PDF final:              outputs/podcast_final.pdf")
    print("=" * 60)

# Punto de entrada del script
if __name__ == "__main__":
    main()