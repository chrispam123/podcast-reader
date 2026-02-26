# diarizador.py
# Módulo encargado de enviar la transcripción cruda a Gemini
# para identificar quién es el entrevistador y quién el invitado
# y guardar el resultado en outputs/transcripcion_diarizada.txt

import os
from dotenv import load_dotenv
from google import genai

# Cargar las variables de entorno desde el archivo .env
load_dotenv()


def _dividir_en_bloques(texto: str, max_chars: int = 14000) -> list[str]:
    """
    Divide la transcripción en bloques para evitar truncamiento por límites
    de salida del modelo.
    """
    palabras = texto.split()
    if not palabras:
        return []

    bloques: list[str] = []
    bloque_actual: list[str] = []
    largo_actual = 0

    for palabra in palabras:
        largo_palabra = len(palabra) + (1 if bloque_actual else 0)
        if largo_actual + largo_palabra > max_chars and bloque_actual:
            bloques.append(" ".join(bloque_actual))
            bloque_actual = [palabra]
            largo_actual = len(palabra)
        else:
            bloque_actual.append(palabra)
            largo_actual += largo_palabra

    if bloque_actual:
        bloques.append(" ".join(bloque_actual))

    return bloques

def _obtener_modelo_objetivo() -> str:
    """
    Devuelve el modelo objetivo para ejecutar una sola llamada a la API.
    Prioriza GEMINI_MODEL si existe en .env.
    """
    modelo_preferido = os.getenv("GEMINI_MODEL")
    if modelo_preferido:
        return modelo_preferido
    return "models/gemini-2.5-flash"

def configurar_gemini() -> tuple[genai.Client, str]:
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
    
    cliente = genai.Client(api_key=api_key)
    modelo = _obtener_modelo_objetivo()
    print(f"Gemini configurado. Modelo seleccionado: {modelo}")
    return cliente, modelo

def construir_prompt(transcripcion: str) -> str:
    """
    Construye el prompt que se enviará a Gemini.
    Le indica exactamente cómo debe identificar y formatear los hablantes.
    """
    return f"""Eres un asistente especializado en analizar transcripciones de podcasts en formato de entrevista.

Tu tarea es analizar la siguiente transcripción, identificar quién es el ENTREVISTADOR y quién es el INVITADO,
y traducir TODO el contenido al español.

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

5. Todo el contenido debe estar traducido al español natural, manteniendo el sentido original.
6. No agregues explicaciones, encabezados ni comentarios extra, solo la transcripción reformateada.
7. Si hay una sección de introducción o presentación al inicio, asígnala al ENTREVISTADOR.
8. No resumas ni omitas partes; conserva el contenido completo.

TRANSCRIPCIÓN:
{transcripcion}
"""


def construir_prompt_bloque(transcripcion_bloque: str, indice: int, total: int) -> str:
    """
    Prompt para traducir + diarizar un bloque de la transcripción.
    """
    return f"""Eres un asistente especializado en analizar transcripciones de podcasts en formato de entrevista.

Estás procesando el BLOQUE {indice} de {total} de una transcripción más larga.
Tu tarea es identificar hablantes y traducir TODO este bloque al español.

REGLAS IMPORTANTES:
1. El ENTREVISTADOR es quien hace las preguntas, introduce temas y cede la palabra.
2. El INVITADO es quien responde, desarrolla ideas y comparte experiencias.
3. Cada vez que cambie el hablante, pon su etiqueta en una línea nueva en mayúsculas.
4. Traduce todo al español natural, sin resumir ni omitir frases.
5. No agregues explicaciones ni comentarios extra.

FORMATO DE SALIDA:
ENTREVISTADOR
[texto en español]

INVITADO
[texto en español]

TRANSCRIPCIÓN DEL BLOQUE:
{transcripcion_bloque}
"""

def diarizar_transcripcion(transcripcion: str, ruta_salida: str | None = None) -> str:
    """
    Envía la transcripción a Gemini y obtiene el texto diarizado y traducido al español.
    Guarda el resultado en outputs/transcripcion_diarizada.txt
    Retorna el texto diarizado como string para usarlo en el siguiente paso.
    """
    print("Iniciando diarización con Gemini...")
    print(f"Tamaño de la transcripción: {len(transcripcion)} caracteres")

    if not transcripcion or not transcripcion.strip():
        raise RuntimeError(
            "La transcripción está vacía. Reintenta la extracción antes de diarizar."
        )
    
    # Configurar Gemini y obtener cliente + modelo
    cliente, modelo = configurar_gemini()

    bloques = _dividir_en_bloques(transcripcion)
    if not bloques:
        raise RuntimeError("No se pudo dividir la transcripción en bloques válidos.")
    print(f"Total de bloques a procesar: {len(bloques)}")

    partes_diarizadas: list[str] = []
    
    try:
        for indice, bloque in enumerate(bloques, start=1):
            print(f"Enviando bloque {indice}/{len(bloques)} a Gemini...")
            prompt_bloque = construir_prompt_bloque(bloque, indice, len(bloques))
            respuesta = cliente.models.generate_content(
                model=modelo,
                contents=prompt_bloque,
            )

            texto_bloque = (getattr(respuesta, "text", "") or "").strip()
            if not texto_bloque:
                raise RuntimeError(
                    f"Gemini devolvió una respuesta vacía en el bloque {indice}/{len(bloques)}."
                )
            partes_diarizadas.append(texto_bloque)

        texto_diarizado = "\n\n".join(partes_diarizadas)

        if len(texto_diarizado) < max(200, int(len(transcripcion) * 0.55)):
            raise RuntimeError(
                "La salida parece incompleta para el tamaño de la transcripción. "
                "Reintenta con otro GEMINI_MODEL o ajusta max_chars por bloque."
            )
        
    except Exception as e:
        raise RuntimeError(f"Error al comunicarse con Gemini: {e}")
    
    # Crear la carpeta outputs/ si no existe
    os.makedirs("outputs", exist_ok=True)
    
    # Guardar la transcripción diarizada en un archivo .txt
    if not ruta_salida:
        ruta_salida = "outputs/transcripcion_diarizada.txt"
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        archivo.write(texto_diarizado)
    
    print(f"Transcripción diarizada guardada en: {ruta_salida}")
    print(f"Total de caracteres en respuesta: {len(texto_diarizado)}")
    
    return texto_diarizado