# extractor.py
# Módulo encargado de extraer la transcripción de un video de YouTube
# y guardarla como archivo .txt en la carpeta outputs/

import os
from importlib import import_module


def _cargar_api_transcripciones():
    """
    Carga youtube-transcript-api en tiempo de ejecución para evitar
    errores de resolución estática del entorno en el editor.
    """
    try:
        api_mod = import_module("youtube_transcript_api")
        errors_mod = import_module("youtube_transcript_api._errors")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Falta la dependencia 'youtube-transcript-api'. Instálala con: pip install -r requirements.txt"
        ) from exc

    return (
        api_mod.YouTubeTranscriptApi,
        errors_mod.TranscriptsDisabled,
        errors_mod.NoTranscriptFound,
    )

def obtener_id_video(url: str) -> str:
    """
    Extrae el ID del video desde la URL de YouTube.
    Ejemplo: https://www.youtube.com/watch?v=ABC123 → ABC123
    """
    if "v=" in url:
        # Formato estándar: youtube.com/watch?v=ID
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        # Formato corto: youtu.be/ID
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("URL de YouTube no válida")

def extraer_transcripcion(url: str, ruta_salida: str | None = None) -> str:
    """
    Extrae la transcripción completa del video y la guarda en outputs/transcripcion_cruda.txt
    Retorna el texto completo como string para usarlo en el siguiente paso.
    """
    # Obtener el ID del video desde la URL
    video_id = obtener_id_video(url)
    print(f"ID del video detectado: {video_id}")

    YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound = _cargar_api_transcripciones()
    api_cliente = YouTubeTranscriptApi()

    try:
        # Intentar obtener transcripción en inglés primero
        # fetch() devuelve una lista de fragmentos con texto y timestamps
        transcript = api_cliente.fetch(video_id, languages=["en"])
        print("Transcripción en inglés encontrada.")
    except NoTranscriptFound:
        try:
            # Si no hay en inglés, intentar obtener cualquier transcripción disponible
            transcript = api_cliente.fetch(video_id)
            print("Transcripción encontrada en idioma alternativo.")
        except TranscriptsDisabled:
            # El video no tiene subtítulos habilitados
            
            raise RuntimeError("Este video no tiene transcripciones disponibles.")

    # Unir todos los fragmentos de texto en un solo string limpio
    # Cada fragmento tiene 'text', 'start' y 'duration', solo nos interesa el texto
    texto_completo = " ".join([fragmento.text for fragmento in transcript])

    # Crear la carpeta outputs/ si no existe
    os.makedirs("outputs", exist_ok=True)

    # Guardar la transcripción cruda en un archivo .txt
    if not ruta_salida:
        ruta_salida = "outputs/transcripcion_cruda.txt"
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        archivo.write(texto_completo)

    print(f"Transcripción guardada en: {ruta_salida}")
    print(f"Total de caracteres extraídos: {len(texto_completo)}")

    return texto_completo