# Viabilidad económica de una tienda de calzados

Aplicación interactiva en Dash para proyectar hasta 60 meses la operación de una tienda de calzados en Ciudad del Este o el Departamento Central.

## Funcionalidades

- Cinco o más productos editables.
- Precio determinado por costo y margen objetivo sobre ventas.
- Valores comerciales cargados en guaraníes con IVA incluido.
- IVA débito y crédito al 10%, con traslado de saldos a favor.
- Servicios personales, no personales, insumos y bienes de capital.
- Crecimiento promedio mensual y estacionalidad mediante meses buenos y malos.
- Estado de resultados mensual.
- Inventario inicial, reposición y cobertura objetivo.
- Flujo de caja con financiación 100% propia.
- Punto de equilibrio, ROI, periodo de recuperación, VAN y TIR.
- Matriz de sensibilidad de ventas y costos unitarios.

## Criterios centrales

Si `m` es el margen objetivo sobre ventas y `CU` el costo unitario sin IVA:

```text
Precio sin IVA = CU / (1 - m)
Precio con IVA = Precio sin IVA x 1,10
```

Para montos ingresados con IVA incluido:

```text
IVA incluido = Monto con IVA / 11
Monto sin IVA = Monto con IVA - IVA incluido
```

El IVA se liquida mensualmente como diferencia entre débito y crédito. El IRE se estima aplicando la tasa ingresada sobre resultados operativos mensuales positivos. Es una aproximación para evaluación económica, no una liquidación fiscal completa.

## Ejecución local

Requiere Python 3.11 o superior.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abrir `http://localhost:8050`.

## Despliegue en Railway

1. Crear un repositorio con los archivos de esta carpeta.
2. Crear un proyecto nuevo en Railway y seleccionar **Deploy from GitHub repo**.
3. Elegir el repositorio.
4. Railway detectará `requirements.txt` y utilizará el comando de `railway.json`.
5. En **Settings > Networking**, generar un dominio público.

No es necesario definir manualmente la variable `PORT`; Railway la proporciona automáticamente.

## Archivos principales

- `app.py`: interfaz Dash, gráficos y callbacks.
- `modelo.py`: cálculos operativos, tributarios y financieros.
- `requirements.txt`: dependencias.
- `railway.json` y `Procfile`: configuración de despliegue.
- `test_modelo.py`: controles automatizados de las fórmulas principales.

