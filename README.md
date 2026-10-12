# Agente Investigador V4

Cambios principales:

- Se corrigió el parser de Hallazgos principales.
- El nombre ya no mezcla descripción, fuente ni URL.
- Cada hallazgo se muestra como una tarjeta independiente.
- La descripción se presenta en un bloque de lectura.
- La fuente aparece en un panel separado.
- La URL larga se reemplaza visualmente por:
  - nombre de fuente,
  - dominio,
  - botón "Abrir fuente".
- El prompt obliga al modelo a separar:
  - Nombre
  - Descripción
  - Fuente
  - URL
- Mantiene:
  - streaming,
  - fuentes en vivo,
  - tabla comparativa,
  - plan visual,
  - reporte estructurado.

## Ejecutar

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Configura antes tu API Key en `config.py`.

## V5 - Corrección de alineación

- Se eliminó el scroll horizontal general de la página.
- Todas las secciones del reporte usan el mismo ancho.
- El plan de investigación responde al tamaño de pantalla.
- La tabla comparativa hace scroll únicamente dentro de su tarjeta.
- Se añadieron reglas para textos y URLs largas.
- Coincidencias, tendencias, hallazgos y fuentes ya no desbordan el contenedor.
