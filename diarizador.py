# diarizador.py
# Módulo encargado de enviar la transcripción cruda a Gemini
# para identificar quién es el entrevistador y quién el invitado
# y guardar el resultado en outputs/transcripcion_diarizada.txt

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

def configurar_gemini():
    """
    Configura el cliente de Gemini con la API key del archivo .env
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Verificar que la API key existe antes de continuar
    if not api_key:
        raise RuntimeError(
            "No se encontró GEMINI_API_KEY en el archivo .env. "
            "Asegúrate de haberla configurado correctamente."
        )
    
    # Inicializar el SDK de Google con la API key
    genai.configure(api_key=api_key)
    
    # Usar gemini-1.5-pro por su ventana de contexto de 1 millón de tokens
    modelo = genai.GenerativeModel("gemini-1.5-pro")
    print("Gemini configurado correctamente.")
    
    return modelo

def construir_prompt(transcripcion: str) -> str:
    """
    Construye el prompt que se enviará a Gemini.
    Le indica exactamente cómo debe identificar y formatear los hablantes.
    """
    return f"""Eres un asistente especializado en analizar transcripciones de podcasts en formato de entrevista.

Tu tarea es analizar la siguiente transcripción y reformatearla identificando quién es el ENTREVISTADOR y quién es el INVITADO.

REGLAS IMPORTANTES:
1. El ENTREVISTADOR es quien hace las preguntas, introduce temas y cede la palabra.
2. El INVITADO es quien responde, desarrolla ideas y comparte experiencias.
3. Cada vez que cambie el hablante, pon su etiqueta en una línea nueva en mayúsculas.
4. El formato de salida debe ser exactamente así:

ENTREVISTADOR
[lo que dice el entrevistador]

INVITADO
[lo que dice el invitado]

ENTREVISTADOR
[lo que dice el entrevistador]

5. No agregues explicaciones, encabezados ni comentarios extra, solo la transcripción reformateada.
6. Si hay una sección de introducción o presentación al inicio, asígnala al ENTREVISTADOR.
7. Mantén el texto original, no lo traduzcas ni lo resumas.

TRANSCRIPCIÓN:
{transcripcion}
"""

def diarizar_transcripcion(transcripcion: str) -> str:
    """
    Envía la transcripción a Gemini y obtiene el texto diarizado.
    Guarda el resultado en outputs/transcripcion_diarizada.txt
    Retorna el texto diarizado como string para usarlo en el siguiente paso.
    """
    print("Iniciando diarización con Gemini...")
    print(f"Tamaño de la transcripción: {len(transcripcion)} caracteres")
    
    # Configurar Gemini y obtener el modelo
    modelo = configurar_gemini()
    
    # Construir el prompt con la transcripción incluida
    prompt = construir_prompt(transcripcion)
    
    try:
        # Enviar el prompt a Gemini y esperar la respuesta
        # Esto puede tardar varios minutos para transcripciones largas
        print("Enviando transcripción a Gemini... (puede tardar varios minutos)")
        respuesta = modelo.generate_content(prompt)
        
        # Extraer el texto de la respuesta
        texto_diarizado = respuesta.text
        
    except Exception as e:
        raise RuntimeError(f"Error al comunicarse con Gemini: {e}")
    
    # Crear la carpeta outputs/ si no existe
    os.makedirs("outputs", exist_ok=True)
    
    # Guardar la transcripción diarizada en un archivo .txt
    ruta_salida = "outputs/transcripcion_diarizada.txt"
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        archivo.write(texto_diarizado)
    
    print(f"Transcripción diarizada guardada en: {ruta_salida}")
    print(f"Total de caracteres en respuesta: {len(texto_diarizado)}")
    
    return texto_diarizado