from __future__ import annotations

import os
from typing import Any

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, dash_table, dcc, html

from modelo import MESES, ejecutar_modelo, tabla_sensibilidad


PRODUCTOS_INICIALES = [
    {"Producto": "Calzado deportivo", "Cantidad mes 1": 85, "Costo unitario con IVA": 320_000, "Margen objetivo %": 30},
    {"Producto": "Sneakers / urbano", "Cantidad mes 1": 70, "Costo unitario con IVA": 280_000, "Margen objetivo %": 30},
    {"Producto": "Calzado femenino", "Cantidad mes 1": 55, "Costo unitario con IVA": 240_000, "Margen objetivo %": 30},
    {"Producto": "Calzado masculino", "Cantidad mes 1": 50, "Costo unitario con IVA": 260_000, "Margen objetivo %": 30},
    {"Producto": "Infantil / escolar", "Cantidad mes 1": 45, "Costo unitario con IVA": 190_000, "Margen objetivo %": 30},
]

PERSONAL_INICIAL = [
    {"Cargo": "Vendedor", "Cantidad": 2, "Salario mensual": 3_200_000, "Cargas %": 30},
    {"Cargo": "Administrador de tienda", "Cantidad": 1, "Salario mensual": 4_500_000, "Cargas %": 30},
    {"Cargo": "Depósito", "Cantidad": 1, "Salario mensual": 3_200_000, "Cargas %": 30},
    {"Cargo": "Limpieza", "Cantidad": 1, "Salario mensual": 3_200_000, "Cargas %": 30},
]

NO_PERSONALES_INICIALES = [
    {"Categoría": "Servicios inmobiliarios", "Concepto": "Alquiler", "Monto mensual con IVA": 12_000_000},
    {"Categoría": "Servicios públicos", "Concepto": "Energía, agua e internet", "Monto mensual con IVA": 1_500_000},
    {"Categoría": "Marketing", "Concepto": "Publicidad y promociones", "Monto mensual con IVA": 3_000_000},
    {"Categoría": "Servicios profesionales", "Concepto": "Contabilidad y asesoría", "Monto mensual con IVA": 1_200_000},
    {"Categoría": "Servicios financieros", "Concepto": "Comisiones bancarias y tarjetas", "Monto mensual con IVA": 1_000_000},
    {"Categoría": "Otros", "Concepto": "Otros servicios", "Monto mensual con IVA": 0},
]

CONSUMOS_INICIALES = [
    {"Concepto": "Bolsas y embalajes", "Monto mensual con IVA": 500_000},
    {"Concepto": "Papelería e insumos administrativos", "Monto mensual con IVA": 250_000},
    {"Concepto": "Materiales de limpieza", "Monto mensual con IVA": 250_000},
    {"Concepto": "Otros consumibles", "Monto mensual con IVA": 0},
]

CAPITAL_RECURRENTE_INICIAL = [
    {"Concepto": "Reposición de equipos", "Compra mensual con IVA": 0, "Vida útil meses": 36},
    {"Concepto": "Otros bienes de capital", "Compra mensual con IVA": 0, "Vida útil meses": 36},
]

INVERSIONES_INICIALES = [
    {"Concepto": "Adecuación del local", "Monto con IVA": 15_000_000, "Vida útil meses": 60},
    {"Concepto": "Mobiliario y exhibidores", "Monto con IVA": 10_000_000, "Vida útil meses": 60},
    {"Concepto": "Equipos informáticos y seguridad", "Monto con IVA": 5_000_000, "Vida útil meses": 36},
    {"Concepto": "Garantía de alquiler", "Monto con IVA": 12_000_000, "Vida útil meses": 0},
    {"Concepto": "Marketing de apertura", "Monto con IVA": 3_000_000, "Vida útil meses": 0},
    {"Concepto": "Constitución y habilitaciones", "Monto con IVA": 2_000_000, "Vida útil meses": 0},
    {"Concepto": "Otros gastos iniciales", "Monto con IVA": 0, "Vida útil meses": 0},
]


def dinero(valor: Any) -> str:
    if valor is None:
        return "No disponible"
    try:
        return f"Gs. {float(valor):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "No disponible"


def porcentaje(valor: Any, decimales: int = 1) -> str:
    if valor is None:
        return "No disponible"
    try:
        return f"{float(valor) * 100:.{decimales}f}%".replace(".", ",")
    except (TypeError, ValueError):
        return "No disponible"


def numero_tabla(valor: Any) -> str:
    try:
        return f"{float(valor):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return ""


def tarjeta(titulo: str, valor: str, nota: str = "", color: str = "primary") -> dbc.Col:
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.Div(titulo, className="text-muted small fw-semibold"),
                    html.H4(valor, className=f"my-2 text-{color}"),
                    html.Div(nota, className="text-muted small"),
                ]
            ),
            className="border-0 shadow-sm h-100",
        ),
        lg=3,
        md=4,
        sm=6,
        xs=12,
    )


def entrada_numero(
    etiqueta: str,
    id_: str,
    valor: float,
    sufijo: str = "",
    paso: float = 1,
    minimo: float | None = 0,
    maximo: float | None = None,
    ayuda: str = "",
    ancho: int = 3,
) -> dbc.Col:
    return dbc.Col(
        [
            dbc.Label(etiqueta, className="small fw-semibold"),
            dbc.InputGroup(
                [
                    dbc.Input(
                        id=id_,
                        type="number",
                        value=valor,
                        step=paso,
                        min=minimo,
                        max=maximo,
                    ),
                    dbc.InputGroupText(sufijo) if sufijo else html.Span(),
                ]
            ),
            html.Div(ayuda, className="form-text") if ayuda else None,
        ],
        lg=ancho,
        md=6,
        xs=12,
        className="mb-3",
    )


ESTILO_TABLA = {
    "style_table": {"overflowX": "auto"},
    "style_cell": {
        "fontFamily": "Inter, Arial, sans-serif",
        "fontSize": "13px",
        "padding": "8px",
        "minWidth": "130px",
        "whiteSpace": "normal",
        "height": "auto",
        "textAlign": "right",
    },
    "style_cell_conditional": [
        {"if": {"column_id": "Producto"}, "textAlign": "left", "minWidth": "180px"},
        {"if": {"column_id": "Cargo"}, "textAlign": "left", "minWidth": "180px"},
        {"if": {"column_id": "Categoría"}, "textAlign": "left", "minWidth": "180px"},
        {"if": {"column_id": "Concepto"}, "textAlign": "left", "minWidth": "220px"},
        {"if": {"column_id": "Calendario"}, "textAlign": "left"},
        {"if": {"column_id": "Tipo"}, "textAlign": "left"},
    ],
    "style_header": {"fontWeight": "700", "backgroundColor": "#eef2f7", "textAlign": "center"},
}


def tabla_editable(id_: str, datos: list[dict[str, Any]], columnas: list[str]) -> dash_table.DataTable:
    return dash_table.DataTable(
        id=id_,
        data=datos,
        columns=[{"name": columna, "id": columna, "editable": True} for columna in columnas],
        editable=True,
        row_deletable=True,
        page_size=12,
        **ESTILO_TABLA,
    )


def bloque_tabla(
    titulo: str,
    descripcion: str,
    tabla: dash_table.DataTable,
    boton_id: str,
) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.Div([html.H5(titulo, className="mb-1"), html.P(descripcion, className="text-muted small mb-0")]),
                        dbc.Button("Agregar fila", id=boton_id, color="secondary", outline=True, size="sm"),
                    ],
                    className="d-flex justify-content-between align-items-start mb-3 gap-3",
                ),
                tabla,
            ]
        ),
        className="border-0 shadow-sm mb-4",
    )


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
)
server = app.server
app.title = "Viabilidad económica | Tienda de calzados"


panel_parametros = html.Div(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Escenario y horizonte", className="mb-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Escenario de localización", className="small fw-semibold"),
                                    dcc.Dropdown(
                                        id="escenario",
                                        options=[
                                            {"label": "Ciudad del Este", "value": "CDE"},
                                            {"label": "Departamento Central", "value": "Central"},
                                        ],
                                        value="CDE",
                                        clearable=False,
                                    ),
                                ],
                                lg=3,
                                md=6,
                                xs=12,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Localidad dentro de Central", className="small fw-semibold"),
                                    dbc.Input(
                                        id="localidad-central",
                                        value="San Lorenzo",
                                        placeholder="Ej.: San Lorenzo, Lambaré o Luque",
                                    ),
                                ],
                                lg=3,
                                md=6,
                                xs=12,
                                className="mb-3",
                            ),
                            entrada_numero("Horizonte", "horizonte", 36, "meses", 1, 1, 60),
                            dbc.Col(
                                [
                                    dbc.Label("Mes de inicio", className="small fw-semibold"),
                                    dcc.Dropdown(
                                        id="mes-inicio",
                                        options=[
                                            {"label": nombre, "value": numero_mes_desplegable}
                                            for numero_mes_desplegable, nombre in enumerate(
                                                MESES, start=1
                                            )
                                        ],
                                        value=1,
                                        clearable=False,
                                    ),
                                ],
                                lg=3,
                                md=6,
                                xs=12,
                                className="mb-3",
                            ),
                        ]
                    ),
                    html.Hr(),
                    html.H5("Crecimiento y estacionalidad", className="mb-3"),
                    dbc.Row(
                        [
                            entrada_numero("Crecimiento promedio mensual", "crecimiento", 2, "%", 0.1, -100, 100),
                            entrada_numero("Aumento en meses buenos", "aumento-bueno", 20, "%", 1, 0, 500),
                            entrada_numero("Disminución en meses malos", "reduccion-malo", 15, "%", 1, 0, 100),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Meses buenos", className="small fw-semibold"),
                                    dcc.Dropdown(
                                        id="meses-buenos",
                                        options=[
                                            {"label": nombre, "value": numero_mes_desplegable}
                                            for numero_mes_desplegable, nombre in enumerate(
                                                MESES, start=1
                                            )
                                        ],
                                        value=[2, 7, 12],
                                        multi=True,
                                    ),
                                ],
                                md=6,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Meses malos", className="small fw-semibold"),
                                    dcc.Dropdown(
                                        id="meses-malos",
                                        options=[
                                            {"label": nombre, "value": numero_mes_desplegable}
                                            for numero_mes_desplegable, nombre in enumerate(
                                                MESES, start=1
                                            )
                                        ],
                                        value=[3, 8],
                                        multi=True,
                                    ),
                                ],
                                md=6,
                                className="mb-3",
                            ),
                        ]
                    ),
                ]
            ),
            className="border-0 shadow-sm mb-4",
        ),
        bloque_tabla(
            "Productos e ingresos",
            "Todos los costos se ingresan con IVA incluido. El precio se calcula con margen sobre ventas, no con markup.",
            tabla_editable(
                "tabla-productos",
                PRODUCTOS_INICIALES,
                ["Producto", "Cantidad mes 1", "Costo unitario con IVA", "Margen objetivo %"],
            ),
            "agregar-producto",
        ),
        bloque_tabla(
            "Servicios personales",
            "Los salarios y cargas laborales no generan IVA crédito.",
            tabla_editable(
                "tabla-personal", PERSONAL_INICIAL, ["Cargo", "Cantidad", "Salario mensual", "Cargas %"]
            ),
            "agregar-personal",
        ),
        bloque_tabla(
            "Servicios no personales",
            "Cargue alquiler, servicios públicos, profesionales, marketing y otros importes con IVA incluido.",
            tabla_editable(
                "tabla-no-personales",
                NO_PERSONALES_INICIALES,
                ["Categoría", "Concepto", "Monto mensual con IVA"],
            ),
            "agregar-no-personal",
        ),
        bloque_tabla(
            "Bienes de consumo e insumos",
            "Importes mensuales con IVA incluido.",
            tabla_editable(
                "tabla-consumos", CONSUMOS_INICIALES, ["Concepto", "Monto mensual con IVA"]
            ),
            "agregar-consumo",
        ),
        bloque_tabla(
            "Bienes de capital recurrentes",
            "La compra afecta el flujo de caja; la depreciación afecta el estado de resultados.",
            tabla_editable(
                "tabla-capital",
                CAPITAL_RECURRENTE_INICIAL,
                ["Concepto", "Compra mensual con IVA", "Vida útil meses"],
            ),
            "agregar-capital",
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Inventario inicial y evaluación", className="mb-3"),
                    html.P(
                        "El inventario inicial se calcula automáticamente al costo de las ventas proyectadas de los primeros meses seleccionados.",
                        className="text-muted small",
                    ),
                    dbc.Row(
                        [
                            entrada_numero("Meses de inventario inicial", "meses-inventario-inicial", 3, "meses", 1, 0, 12),
                            entrada_numero("Tasa de descuento anual", "tasa-descuento", 15, "%", 0.1, -99, 500),
                            entrada_numero("Tasa IRE", "tasa-ire", 10, "%", 0.1, 0, 100),
                            entrada_numero("Valor residual final", "valor-residual", 0, "Gs.", 1_000_000),
                        ]
                    ),
                ]
            ),
            className="border-0 shadow-sm mb-4",
        ),
        bloque_tabla(
            "Gastos e inversiones iniciales",
            "Los montos se ingresan con IVA incluido. Una vida útil mayor a cero activa la depreciación mensual.",
            tabla_editable(
                "tabla-inversiones", INVERSIONES_INICIALES, ["Concepto", "Monto con IVA", "Vida útil meses"]
            ),
            "agregar-inversion",
        ),
    ]
)


panel_resultados = html.Div(
    [
        html.Div(id="alertas-modelo"),
        dbc.Row(id="kpis-operativos", className="g-3 mb-4"),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="grafico-ventas"), lg=7),
                dbc.Col(dcc.Graph(id="grafico-costos"), lg=5),
            ],
            className="mb-4",
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Precio y rentabilidad por producto"),
                    html.P("El precio con IVA se calcula después de determinar el precio neto compatible con el margen objetivo.", className="text-muted small"),
                    dash_table.DataTable(id="tabla-productos-calculados", page_size=10, **ESTILO_TABLA),
                ]
            ),
            className="border-0 shadow-sm mb-4",
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("State de resultados mensual"),
                    html.P("Los ingresos con IVA se muestran para conciliación; el resultado utiliza ventas y gastos netos de IVA recuperable. El IRE se provisiona al cierre de cada ejercicio incluido.", className="text-muted small"),
                    dash_table.DataTable(id="tabla-resultados", page_size=12, **ESTILO_TABLA),
                ]
            ),
            className="border-0 shadow-sm mb-4",
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Liquidación anual estimada del IRE"),
                    html.P(
                        "Compensa los resultados mensuales del ejercicio y aplica el arrastre de pérdidas fiscales dentro de los límites incorporados al modelo.",
                        className="text-muted small",
                    ),
                    dash_table.DataTable(id="tabla-ire-anual", page_size=10, **ESTILO_TABLA),
                ]
            ),
            className="border-0 shadow-sm mb-4",
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Liquidación mensual estimada del IVA"),
                    html.P("IVA débito y crédito al 10%. Los saldos a favor se trasladan al mes siguiente.", className="text-muted small"),
                    dash_table.DataTable(id="tabla-iva", page_size=12, **ESTILO_TABLA),
                ]
            ),
            className="border-0 shadow-sm mb-4",
        ),
    ]
)


panel_financiero = html.Div(
    [
        dbc.Row(id="kpis-financieros", className="g-3 mb-4"),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="grafico-flujo"), lg=7),
                dbc.Col(dcc.Graph(id="grafico-inventario"), lg=5),
            ],
            className="mb-4",
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Flujo de caja del proyecto"),
                    html.P("Financiación 100% propia. El mes 0 reúne las inversiones y el inventario inicial calculado automáticamente.", className="text-muted small"),
                    dash_table.DataTable(id="tabla-flujo", page_size=12, **ESTILO_TABLA),
                ]
            ),
            className="border-0 shadow-sm mb-4",
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H5("Tabla de sensibilidad", className="mb-1"),
                                    html.P(
                                        "Cruza variaciones de unidades vendidas y costos unitarios. Los precios permanecen en el nivel base para medir el riesgo económico.",
                                        className="text-muted small mb-0",
                                    ),
                                ]
                            ),
                            dbc.RadioItems(
                                id="metrica-sensibilidad",
                                options=[
                                    {"label": "VAN", "value": "van"},
                                    {"label": "TIR anual", "value": "tir_anual"},
                                    {"label": "Resultado neto", "value": "resultado_neto"},
                                ],
                                value="van",
                                inline=True,
                            ),
                        ],
                        className="d-flex justify-content-between align-items-start flex-wrap gap-3 mb-3",
                    ),
                    dcc.Graph(id="grafico-sensibilidad"),
                    dash_table.DataTable(id="tabla-sensibilidad", page_size=10, **ESTILO_TABLA),
                ]
            ),
            className="border-0 shadow-sm mb-4",
        ),
        dbc.Alert(
            [
                html.Strong("Alcance tributario: "),
                "el IVA y el IRE son estimaciones para evaluación de proyectos. La liquidación fiscal real puede requerir ajustes, documentación y calendarios que no forman parte de esta herramienta.",
            ],
            color="warning",
        ),
    ]
)


app.layout = html.Div(
    [
        html.Header(
            dbc.Container(
                [
                    html.Div(
                        [
                            html.Div("CAMBRA BUSINESS ANALYTICS", className="small fw-bold text-primary mb-2"),
                            html.H1("Viabilidad económica de una tienda de calzados", className="mb-2"),
                            html.P(
                                "Ingresos, estructura de costos, impuestos, flujo de caja, VAN, TIR y sensibilidad hasta 60 meses.",
                                className="text-muted mb-0",
                            ),
                        ],
                        className="py-4",
                    )
                ],
                fluid=True,
            ),
            className="bg-white border-bottom",
        ),
        dbc.Container(
            [
                dbc.Alert(
                    [
                        html.Strong("Criterio de carga: "),
                        "todos los importes comerciales y gravados se ingresan en guaraníes con IVA incluido. La aplicación separa IVA débito y crédito al 10%.",
                    ],
                    color="info",
                    className="mt-3",
                ),
                dbc.Tabs(
                    [
                        dbc.Tab(panel_parametros, label="1. Parámetros", tab_id="parametros", className="pt-4"),
                        dbc.Tab(panel_resultados, label="2. State de resultados", tab_id="resultados", className="pt-4"),
                        dbc.Tab(panel_financiero, label="3. Evaluación financiera", tab_id="financiero", className="pt-4"),
                    ],
                    id="pestanas",
                    active_tab="parametros",
                ),
                html.Div(
                    [
                        html.Span("Modelo de evaluación económica — valores editables y resultados indicativos."),
                    ],
                    className="text-muted small py-4 text-center",
                ),
            ],
            fluid=True,
        ),
    ],
    style={"backgroundColor": "#f5f7fa", "minHeight": "100vh"},
)


def registrar_agregar_fila(boton: str, tabla: str, fila_vacia: dict[str, Any]) -> None:
    @app.callback(
        Output(tabla, "data"),
        Input(boton, "n_clicks"),
        State(tabla, "data"),
        prevent_initial_call=True,
    )
    def agregar(_: int, datos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return (datos or []) + [fila_vacia.copy()]


registrar_agregar_fila(
    "agregar-producto",
    "tabla-productos",
    {"Producto": "Nuevo producto", "Cantidad mes 1": 0, "Costo unitario con IVA": 0, "Margen objetivo %": 30},
)
registrar_agregar_fila(
    "agregar-personal",
    "tabla-personal",
    {"Cargo": "Nuevo cargo", "Cantidad": 1, "Salario mensual": 0, "Cargas %": 30},
)
registrar_agregar_fila(
    "agregar-no-personal",
    "tabla-no-personales",
    {"Categoría": "Otros", "Concepto": "Nuevo servicio", "Monto mensual con IVA": 0},
)
registrar_agregar_fila(
    "agregar-consumo",
    "tabla-consumos",
    {"Concepto": "Nuevo insumo", "Monto mensual con IVA": 0},
)
registrar_agregar_fila(
    "agregar-capital",
    "tabla-capital",
    {"Concepto": "Nuevo bien", "Compra mensual con IVA": 0, "Vida útil meses": 36},
)
registrar_agregar_fila(
    "agregar-inversion",
    "tabla-inversiones",
    {"Concepto": "Nueva inversión", "Monto con IVA": 0, "Vida útil meses": 0},
)


def parametros_desde_interfaz(
    escenario: str,
    localidad: str,
    horizonte: Any,
    mes_inicio: Any,
    crecimiento: Any,
    aumento: Any,
    reduccion: Any,
    meses_buenos: list[int],
    meses_malos: list[int],
    meses_inventario_inicial: Any,
    tasa_descuento: Any,
    tasa_ire: Any,
    valor_residual: Any,
) -> dict[str, Any]:
    return {
        "escenario": escenario,
        "localidad_central": localidad,
        "horizonte_meses": horizonte,
        "mes_inicio": mes_inicio,
        "crecimiento_mensual_pct": crecimiento,
        "aumento_mes_bueno_pct": aumento,
        "reduccion_mes_malo_pct": reduccion,
        "meses_buenos": meses_buenos or [],
        "meses_malos": meses_malos or [],
        "meses_inventario_inicial": meses_inventario_inicial,
        "tasa_descuento_anual_pct": tasa_descuento,
        "tasa_ire_pct": tasa_ire,
        "valor_residual_final": valor_residual,
    }


def tabla_formateada(
    tabla_datos: pd.DataFrame,
    porcentajes: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    porcentajes = porcentajes or set()
    datos = []
    for _, fila in tabla_datos.iterrows():
        registro: dict[str, Any] = {}
        for columna, valor in fila.items():
            if columna in porcentajes:
                registro[columna] = porcentaje(valor)
            elif isinstance(valor, (int, float)) and columna != "Mes":
                registro[columna] = numero_tabla(valor)
            else:
                registro[columna] = valor
        datos.append(registro)
    columnas = [
        {"name": str(columna), "id": str(columna)}
        for columna in tabla_datos.columns
    ]
    return datos, columnas


@app.callback(
    Output("alertas-modelo", "children"),
    Output("kpis-operativos", "children"),
    Output("kpis-financieros", "children"),
    Output("grafico-ventas", "figure"),
    Output("grafico-costos", "figure"),
    Output("grafico-flujo", "figure"),
    Output("grafico-inventario", "figure"),
    Output("tabla-productos-calculados", "data"),
    Output("tabla-productos-calculados", "columns"),
    Output("tabla-resultados", "data"),
    Output("tabla-resultados", "columns"),
    Output("tabla-ire-anual", "data"),
    Output("tabla-ire-anual", "columns"),
    Output("tabla-iva", "data"),
    Output("tabla-iva", "columns"),
    Output("tabla-flujo", "data"),
    Output("tabla-flujo", "columns"),
    Output("grafico-sensibilidad", "figure"),
    Output("tabla-sensibilidad", "data"),
    Output("tabla-sensibilidad", "columns"),
    Input("escenario", "value"),
    Input("localidad-central", "value"),
    Input("horizonte", "value"),
    Input("mes-inicio", "value"),
    Input("crecimiento", "value"),
    Input("aumento-bueno", "value"),
    Input("reduccion-malo", "value"),
    Input("meses-buenos", "value"),
    Input("meses-malos", "value"),
    Input("meses-inventario-inicial", "value"),
    Input("tasa-descuento", "value"),
    Input("tasa-ire", "value"),
    Input("valor-residual", "value"),
    Input("tabla-productos", "data"),
    Input("tabla-personal", "data"),
    Input("tabla-no-personales", "data"),
    Input("tabla-consumos", "data"),
    Input("tabla-capital", "data"),
    Input("tabla-inversiones", "data"),
    Input("metrica-sensibilidad", "value"),
)
def actualizar_modelo(
    escenario: str,
    localidad: str,
    horizonte: Any,
    mes_inicio: Any,
    crecimiento: Any,
    aumento: Any,
    reduccion: Any,
    meses_buenos: list[int],
    meses_malos: list[int],
    meses_inventario_inicial: Any,
    tasa_descuento: Any,
    tasa_ire: Any,
    valor_residual: Any,
    productos: list[dict[str, Any]],
    personal: list[dict[str, Any]],
    no_personales: list[dict[str, Any]],
    consumos: list[dict[str, Any]],
    capital: list[dict[str, Any]],
    inversiones: list[dict[str, Any]],
    metrica_sensibilidad: str,
):
    parametros = parametros_desde_interfaz(
        escenario,
        localidad,
        horizonte,
        mes_inicio,
        crecimiento,
        aumento,
        reduccion,
        meses_buenos,
        meses_malos,
        meses_inventario_inicial,
        tasa_descuento,
        tasa_ire,
        valor_residual,
    )
    resultado = ejecutar_modelo(
        parametros, productos, personal, no_personales, consumos, capital, inversiones
    )
    indicadores = resultado.indicadores

    alertas = [dbc.Alert(texto, color="warning", dismissable=True) for texto in resultado.advertencias]
    if not alertas:
        alertas = dbc.Alert("Parámetros procesados correctamente.", color="success", className="py-2")

    tarjetas_operativas = [
        tarjeta(
            "Ingresos con IVA",
            dinero(indicadores["ventas_con_iva"]),
            f"Acumulado {indicadores['horizonte']} meses",
        ),
        tarjeta("Ventas netas", dinero(indicadores["ventas_netas"]), "Sin IVA"),
        tarjeta(
            "Margen bruto",
            porcentaje(indicadores["margen_bruto"]),
            dinero(indicadores["utilidad_bruta"]),
            "success",
        ),
        tarjeta(
            "Resultado neto",
            dinero(indicadores["resultado_neto"]),
            f"Margen neto: {porcentaje(indicadores['margen_neto'])}",
            "success" if indicadores["resultado_neto"] >= 0 else "danger",
        ),
        tarjeta(
            "Punto de equilibrio",
            dinero(indicadores["punto_equilibrio_con_iva"]),
            "Facturación mensual con IVA",
        ),
        tarjeta(
            "Unidades de equilibrio",
            f"{indicadores['punto_equilibrio_unidades']:.0f}"
            if indicadores["punto_equilibrio_unidades"] is not None
            else "No disponible",
            "Mix del mes 1",
        ),
        tarjeta(
            "IVA crédito inicial",
            dinero(indicadores["credito_iva_inicial"]),
            "Inventario inicial e inversiones",
        ),
        tarjeta(
            "IVA saldo final",
            dinero(indicadores["saldo_iva_final"]),
            "Saldo a favor proyectado",
        ),
    ]
    tarjetas_financieras = [
        tarjeta(
            "Inversión inicial",
            dinero(indicadores["inversion_inicial"]),
            "100% capital propio",
        ),
        tarjeta(
            "VAN",
            dinero(indicadores["van"]),
            f"Tasa anual: {tasa_descuento or 0}%",
            "success" if indicadores["van"] >= 0 else "danger",
        ),
        tarjeta(
            "TIR anualizada",
            porcentaje(indicadores["tir_anual"]),
            f"TIR mensual: {porcentaje(indicadores['tir_mensual'])}",
            "success" if (indicadores["tir_anual"] or -1) >= 0 else "danger",
        ),
        tarjeta(
            "ROI acumulado",
            porcentaje(indicadores["rendimiento_inversion"]),
            "Resultado neto / inversión inicial",
        ),
        tarjeta(
            "Recuperación",
            f"Mes {indicadores['periodo_recuperacion_meses']}"
            if indicadores["periodo_recuperacion_meses"]
            else "No recupera",
            f"Horizonte: {indicadores['horizonte']} meses",
        ),
        tarjeta(
            "Inversión máxima requerida",
            dinero(indicadores["inversion_maxima_requerida"]),
            "Máxima exposición acumulada de caja",
            "danger"
            if indicadores["inversion_maxima_requerida"]
            > indicadores["inversion_inicial"]
            else "success",
        ),
        tarjeta(
            "Inventario inicial",
            dinero(indicadores["inventario_inicial_con_iva"]),
            f"Costo de los primeros {indicadores['meses_inventario_inicial']} meses con IVA",
        ),
        tarjeta(
            "Resultado operativo",
            dinero(indicadores["resultado_operativo"]),
            f"Margen: {porcentaje(indicadores['margen_operativo'])}",
        ),
    ]

    grafico_ventas = go.Figure()
    grafico_ventas.add_trace(
        go.Bar(x=resultado.resultados["Mes"], y=resultado.resultados["Ingresos con IVA"], name="Ingresos con IVA")
    )
    grafico_ventas.add_trace(
        go.Scatter(x=resultado.resultados["Mes"], y=resultado.resultados["Resultado neto"], name="Resultado neto", mode="lines+markers")
    )
    grafico_ventas.update_layout(title="Ventas y resultado mensual", template="plotly_white", hovermode="x unified", legend_title_text="")

    costos = pd.DataFrame(
        {
            "Componente": ["Mercadería", "Personal", "Servicios", "Consumos", "Depreciación", "IRE"],
            "Valor": [
                resultado.resultados["Costo mercadería sin IVA"].sum(),
                resultado.resultados["Servicios personales"].sum(),
                resultado.resultados["Servicios no personales"].sum(),
                resultado.resultados["Bienes de consumo"].sum(),
                resultado.resultados["Depreciación"].sum(),
                resultado.resultados["IRE"].sum(),
            ],
        }
    )
    grafico_costos = px.pie(costos, names="Componente", values="Valor", hole=0.48, title="Composición acumulada de costos")
    grafico_costos.update_layout(template="plotly_white", legend_title_text="")

    grafico_flujo = go.Figure()
    grafico_flujo.add_trace(go.Bar(x=resultado.flujo["Mes"], y=resultado.flujo["Flujo neto"], name="Flujo neto"))
    grafico_flujo.add_trace(go.Scatter(x=resultado.flujo["Mes"], y=resultado.flujo["Flujo acumulado"], name="Flujo acumulado", mode="lines+markers"))
    grafico_flujo.add_hline(y=0, line_dash="dash", line_color="#6c757d")
    grafico_flujo.update_layout(title="Flujo de caja mensual y acumulado", template="plotly_white", hovermode="x unified", legend_title_text="")

    grafico_inventario = px.area(
        resultado.flujo,
        x="Mes",
        y="Inventario final con IVA",
        title="Inventario final proyectado",
        template="plotly_white",
    )

    tabla_productos = resultado.productos.copy()
    tabla_productos["Margen objetivo"] = tabla_productos["Margen objetivo"].map(
        porcentaje
    )
    tabla_productos["Markup equivalente"] = tabla_productos[
        "Markup equivalente"
    ].map(porcentaje)
    for columna in ["Cantidad mes 1", "Costo unitario con IVA", "Costo unitario sin IVA", "Precio sin IVA", "Precio con IVA"]:
        tabla_productos[columna] = tabla_productos[columna].map(numero_tabla)
    datos_productos = tabla_productos.to_dict("records")
    columnas_productos = [
        {"name": columna, "id": columna} for columna in tabla_productos.columns
    ]

    columnas_resultados_mostrar = [
        "Mes", "Calendario", "Tipo", "Ingresos con IVA", "IVA débito", "Ventas netas",
        "Costo mercadería sin IVA", "Utilidad bruta", "Servicios personales",
        "Servicios no personales", "Bienes de consumo", "Depreciación",
        "Resultado operativo", "IRE", "Resultado neto",
    ]
    datos_resultados, columnas_resultados = tabla_formateada(
        resultado.resultados[columnas_resultados_mostrar]
    )
    datos_ire_anual, columnas_ire_anual = tabla_formateada(resultado.ire_anual)
    datos_iva, columnas_iva = tabla_formateada(resultado.iva)

    flujo_con_mes_cero = pd.concat(
        [
            pd.DataFrame(
                [
                    {
                        "Mes": 0,
                        "Ingresos cobrados con IVA": 0,
                        "Compras de mercadería con IVA": indicadores[
                            "inventario_inicial_con_iva"
                        ],
                        "Gastos personales": 0,
                        "Otros gastos con IVA": 0,
                        "Bienes de capital con IVA": sum(
                            float(inversion.get("Monto con IVA") or 0)
                            for inversion in (inversiones or [])
                        ),
                        "IVA pagado": 0,
                        "IRE provisionado": 0,
                        "Recuperaciones finales": 0,
                        "Flujo neto": -indicadores["inversion_inicial"],
                        "Flujo acumulado": -indicadores["inversion_inicial"],
                        "Inventario final con IVA": indicadores[
                            "inventario_inicial_con_iva"
                        ],
                    }
                ]
            ),
            resultado.flujo,
        ],
        ignore_index=True,
    )
    datos_flujo, columnas_flujo = tabla_formateada(flujo_con_mes_cero)

    sensibilidad = tabla_sensibilidad(
        parametros,
        productos,
        personal,
        no_personales,
        consumos,
        capital,
        inversiones,
        metrica=metrica_sensibilidad,
    )
    columnas_costos = [
        columna for columna in sensibilidad.columns if columna != "Variación ventas"
    ]
    matriz_valores = sensibilidad[columnas_costos].astype(float).values
    etiquetas_x = [columna.replace("Costo ", "") for columna in columnas_costos]
    etiquetas_y = [
        f"{variacion:+.0%}" for variacion in sensibilidad["Variación ventas"]
    ]
    if metrica_sensibilidad == "tir_anual":
        texto = [
            [porcentaje(valor_celda) for valor_celda in fila]
            for fila in matriz_valores
        ]
        titulo_metrica = "TIR anualizada"
    else:
        texto = [
            [dinero(valor_celda) for valor_celda in fila]
            for fila in matriz_valores
        ]
        titulo_metrica = "VAN" if metrica_sensibilidad == "van" else "Resultado neto"
    grafico_sensibilidad = go.Figure(
        data=go.Heatmap(
            z=matriz_valores,
            x=etiquetas_x,
            y=etiquetas_y,
            colorscale=[[0, "#c0392b"], [0.5, "#f4d03f"], [1, "#1e8449"]],
            text=texto,
            texttemplate="%{text}",
            colorbar_title=titulo_metrica,
        )
    )
    grafico_sensibilidad.update_layout(
        title=f"Sensibilidad del {titulo_metrica}",
        xaxis_title="Variación del costo unitario",
        yaxis_title="Variación de unidades vendidas",
        template="plotly_white",
    )

    sensibilidad_tabla = sensibilidad.copy()
    sensibilidad_tabla["Variación ventas"] = sensibilidad_tabla[
        "Variación ventas"
    ].map(lambda variacion: f"{variacion:+.0%}")
    for columna in columnas_costos:
        sensibilidad_tabla[columna] = sensibilidad_tabla[columna].map(
            porcentaje if metrica_sensibilidad == "tir_anual" else dinero
        )
    datos_sensibilidad = sensibilidad_tabla.to_dict("records")
    columnas_sensibilidad = [
        {"name": columna, "id": columna}
        for columna in sensibilidad_tabla.columns
    ]

    return (
        alertas,
        tarjetas_operativas,
        tarjetas_financieras,
        grafico_ventas,
        grafico_costos,
        grafico_flujo,
        grafico_inventario,
        datos_productos,
        columnas_productos,
        datos_resultados,
        columnas_resultados,
        datos_ire_anual,
        columnas_ire_anual,
        datos_iva,
        columnas_iva,
        datos_flujo,
        columnas_flujo,
        grafico_sensibilidad,
        datos_sensibilidad,
        columnas_sensibilidad,
    )


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", "8050"))
    app.run(host="0.0.0.0", port=puerto, debug=False)
