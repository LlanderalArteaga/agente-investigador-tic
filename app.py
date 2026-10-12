import json

from flask import Flask, Response, render_template, request, stream_with_context
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL


app = Flask(
    __name__,
    static_folder="assets",
    static_url_path="/assets"
)

client = OpenAI(api_key=OPENAI_API_KEY)


@app.route("/")
def inicio():
    return render_template("index.html")


def sse(tipo, datos):
    return (
        f"event: {tipo}\n"
        f"data: {json.dumps(datos, ensure_ascii=False)}\n\n"
    )


def obtener_valor(objeto, atributo, valor_default=None):
    if objeto is None:
        return valor_default

    if isinstance(objeto, dict):
        return objeto.get(atributo, valor_default)

    return getattr(objeto, atributo, valor_default)


def emitir_fuentes_desde_accion(accion, urls_emitidas):
    if accion is None:
        return []

    nuevas_fuentes = []

    tipo_accion = obtener_valor(accion, "type", "")

    url_directa = obtener_valor(accion, "url")

    if url_directa and url_directa not in urls_emitidas:
        urls_emitidas.add(url_directa)

        nuevas_fuentes.append({
            "titulo": url_directa,
            "url": url_directa,
            "origen": tipo_accion or "web_search"
        })

    sources = obtener_valor(accion, "sources", []) or []

    for source in sources:
        url = obtener_valor(source, "url")

        if url and url not in urls_emitidas:
            urls_emitidas.add(url)

            nuevas_fuentes.append({
                "titulo": url,
                "url": url,
                "origen": "search"
            })

    return nuevas_fuentes


@app.route("/api/investigar", methods=["POST"])
def investigar():
    datos = request.get_json(silent=True) or {}
    pregunta = datos.get("pregunta", "").strip()

    if not pregunta:
        return Response(
            sse(
                "error",
                {
                    "mensaje": "Debes escribir una pregunta de investigación."
                }
            ),
            mimetype="text/event-stream",
            status=400
        )

    instrucciones = """
Eres un agente investigador especializado en tecnologías de información
y comunicaciones.

Debes investigar la pregunta del usuario utilizando búsqueda web
y varias fuentes confiables. El tono debe ser claro, profesional y
académico, pensado para estudiantes universitarios.

Proceso que debes seguir:
1. Analiza la pregunta.
2. Define un plan breve de investigación.
3. Realiza búsquedas web.
4. Consulta varias fuentes.
5. Selecciona la información más relevante.
6. Compara la información obtenida.
7. Identifica coincidencias, diferencias y tendencias.
8. Sintetiza la evidencia.
9. Genera un reporte bien estructurado.

REGLAS IMPORTANTES:
- Escribe TODO en español.
- No inventes datos ni fuentes.
- Utiliza varias fuentes cuando sea posible.
- Prioriza fuentes oficiales, organismos, documentación técnica,
  universidades o medios especializados confiables.
- No agregues una sección manual de URLs al final.
- Las URLs se mostrarán por separado en la interfaz.

FORMATO OBLIGATORIO DE SALIDA:
Debes responder en Markdown usando exactamente esta estructura:

# [Título breve del reporte]

## 1. Pregunta de investigación
[Reformula claramente la pregunta del usuario en 1 párrafo.]

## 2. Plan de investigación
- [Paso 1 del plan]
- [Paso 2 del plan]
- [Paso 3 del plan]
- [Paso 4 del plan]
- [Paso 5 del plan]

## 3. Hallazgos principales

Para cada hallazgo utiliza EXACTAMENTE este formato y coloca cada campo
en una línea independiente:

### Hallazgo 1
**Nombre:** [Nombre breve y claro del hallazgo]
**Descripción:** [Explicación del hallazgo. No incluyas aquí la fuente ni la URL.]
**Fuente:** [Nombre del sitio, institución, empresa u organismo]
**URL:** [URL completa de la fuente principal]

### Hallazgo 2
**Nombre:** [Nombre breve y claro del hallazgo]
**Descripción:** [Explicación del hallazgo. No incluyas aquí la fuente ni la URL.]
**Fuente:** [Nombre del sitio, institución, empresa u organismo]
**URL:** [URL completa de la fuente principal]

### Hallazgo 3
**Nombre:** [Nombre breve y claro del hallazgo]
**Descripción:** [Explicación del hallazgo. No incluyas aquí la fuente ni la URL.]
**Fuente:** [Nombre del sitio, institución, empresa u organismo]
**URL:** [URL completa de la fuente principal]

Incluye más hallazgos si es necesario.

IMPORTANTE PARA HALLAZGOS:
- El nombre debe ser corto: máximo una línea.
- La descripción debe contener solo la explicación.
- La fuente debe contener solo el nombre de la fuente.
- La URL debe contener solo la dirección web.
- No combines Nombre, Descripción, Fuente y URL en una misma línea.

## 4. Comparación de información
Presenta una tabla Markdown con estas columnas exactas:
| Elemento | Descripción | Ventajas | Limitaciones | Escenarios recomendados |

Debes incluir al menos 3 filas cuando la pregunta lo permita.

## 5. Coincidencias y diferencias entre fuentes
### Coincidencias
- [Coincidencia 1]
- [Coincidencia 2]

### Diferencias
- [Diferencia 1]
- [Diferencia 2]

## 6. Tendencias identificadas
- [Tendencia 1]
- [Tendencia 2]
- [Tendencia 3]

## 7. Conclusiones
[Conclusión final en 1 o 2 párrafos.]
"""

    @stream_with_context
    def generar():
        urls_emitidas = set()
        reporte_acumulado = []

        try:
            yield sse(
                "estado",
                {
                    "etapa": "analizando",
                    "mensaje": "Analizando la pregunta de investigación..."
                }
            )

            stream = client.responses.create(
                model=OPENAI_MODEL,
                tools=[
                    {
                        "type": "web_search",
                        "search_context_size": "medium"
                    }
                ],
                input=[
                    {
                        "role": "system",
                        "content": instrucciones
                    },
                    {
                        "role": "user",
                        "content": pregunta
                    }
                ],
                stream=True
            )

            for event in stream:
                tipo = obtener_valor(event, "type", "")

                if tipo == "response.web_search_call.in_progress":
                    yield sse(
                        "estado",
                        {
                            "etapa": "busqueda",
                            "mensaje": "Iniciando una búsqueda en Internet..."
                        }
                    )

                elif tipo == "response.web_search_call.searching":
                    yield sse(
                        "estado",
                        {
                            "etapa": "busqueda",
                            "mensaje": "Buscando, contrastando y consultando fuentes..."
                        }
                    )

                elif tipo == "response.web_search_call.completed":
                    yield sse(
                        "estado",
                        {
                            "etapa": "revision",
                            "mensaje": "Búsqueda completada. Revisando la información encontrada..."
                        }
                    )

                elif tipo == "response.output_item.done":
                    item = obtener_valor(event, "item")

                    if obtener_valor(item, "type") == "web_search_call":
                        accion = obtener_valor(item, "action")

                        for fuente in emitir_fuentes_desde_accion(
                            accion,
                            urls_emitidas
                        ):
                            yield sse("fuente", fuente)

                elif tipo == "response.output_text.annotation.added":
                    anotacion = obtener_valor(event, "annotation")

                    if obtener_valor(anotacion, "type") == "url_citation":
                        url = obtener_valor(anotacion, "url")
                        titulo = obtener_valor(
                            anotacion,
                            "title",
                            url or "Fuente consultada"
                        )

                        if url and url not in urls_emitidas:
                            urls_emitidas.add(url)

                            yield sse(
                                "fuente",
                                {
                                    "titulo": titulo,
                                    "url": url,
                                    "origen": "cita"
                                }
                            )

                elif tipo == "response.output_text.delta":
                    delta = obtener_valor(event, "delta", "")

                    if delta:
                        reporte_acumulado.append(delta)

                        yield sse(
                            "texto",
                            {
                                "delta": delta
                            }
                        )

                elif tipo == "response.output_text.done":
                    yield sse(
                        "estado",
                        {
                            "etapa": "finalizando",
                            "mensaje": "Sintetizando y organizando el reporte final..."
                        }
                    )

                elif tipo == "response.completed":
                    yield sse(
                        "completado",
                        {
                            "mensaje": "Investigación completada.",
                            "reporte": "".join(reporte_acumulado),
                            "total_fuentes": len(urls_emitidas)
                        }
                    )

                elif tipo == "error":
                    mensaje = obtener_valor(
                        event,
                        "message",
                        "OpenAI devolvió un error durante la investigación."
                    )

                    yield sse(
                        "error",
                        {
                            "mensaje": mensaje
                        }
                    )

        except Exception as error:
            print("ERROR:", error)

            yield sse(
                "error",
                {
                    "mensaje": "Ocurrió un error al realizar la investigación.",
                    "detalle": str(error)
                }
            )

    return Response(
        generar(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        threaded=True
    )
