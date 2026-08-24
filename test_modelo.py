import math

from modelo import ejecutar_modelo, iva_incluido, sin_iva, tabla_sensibilidad


PARAMETROS = {
    "escenario": "CDE",
    "horizonte_meses": 12,
    "mes_inicio": 1,
    "crecimiento_mensual_pct": 0,
    "aumento_mes_bueno_pct": 20,
    "reduccion_mes_malo_pct": 10,
    "meses_buenos": [2],
    "meses_malos": [3],
    "inventario_inicial_con_iva": 11_000_000,
    "cobertura_inventario_meses": 1,
    "capital_operativo_inicial": 5_000_000,
    "tasa_descuento_anual_pct": 15,
    "tasa_ire_pct": 10,
    "recuperacion_inventario_pct": 100,
    "recuperacion_capital_pct": 100,
    "valor_residual_final": 0,
}

PRODUCTOS = [
    {
        "Producto": "Prueba",
        "Cantidad mes 1": 100,
        "Costo unitario con IVA": 110_000,
        "Margen objetivo %": 30,
    }
]
PERSONAL = [{"Cargo": "Vendedor", "Cantidad": 1, "Salario mensual": 3_000_000, "Cargas %": 30}]
NO_PERSONALES = [{"Categoría": "Inmobiliario", "Concepto": "Alquiler", "Monto mensual con IVA": 1_100_000}]
CONSUMOS = [{"Concepto": "Bolsas", "Monto mensual con IVA": 110_000}]
CAPITAL = [{"Concepto": "Reposición", "Compra mensual con IVA": 0, "Vida útil meses": 36}]
INVERSIONES = [{"Concepto": "Muebles", "Monto con IVA": 11_000_000, "Vida útil meses": 60}]


def ejecutar():
    return ejecutar_modelo(
        PARAMETROS, PRODUCTOS, PERSONAL, NO_PERSONALES, CONSUMOS, CAPITAL, INVERSIONES
    )


def test_iva_incluido_y_neto():
    assert iva_incluido(110_000) == 10_000
    assert math.isclose(sin_iva(110_000), 100_000, rel_tol=1e-12)


def test_margen_no_markup():
    resultado = ejecutar()
    producto = resultado.productos.iloc[0]
    assert math.isclose(producto["Costo unitario sin IVA"], 100_000, rel_tol=1e-9)
    assert math.isclose(producto["Precio sin IVA"], 100_000 / 0.70, rel_tol=1e-9)
    margen = (producto["Precio sin IVA"] - producto["Costo unitario sin IVA"]) / producto["Precio sin IVA"]
    assert math.isclose(margen, 0.30, rel_tol=1e-9)
    assert producto["Markup equivalente"] > 0.42


def test_estacionalidad_buena_y_mala():
    resultado = ejecutar()
    enero = resultado.resultados.iloc[0]["Ingresos con IVA"]
    febrero = resultado.resultados.iloc[1]["Ingresos con IVA"]
    marzo = resultado.resultados.iloc[2]["Ingresos con IVA"]
    assert math.isclose(febrero / enero, 1.20, rel_tol=1e-9)
    assert math.isclose(marzo / enero, 0.90, rel_tol=1e-9)


def test_iva_no_es_ingreso_neto():
    resultado = ejecutar()
    fila = resultado.resultados.iloc[0]
    assert math.isclose(fila["Ingresos con IVA"] - fila["IVA débito"], fila["Ventas netas"], rel_tol=1e-9)


def test_flujo_incluye_mes_cero_y_tir_van():
    resultado = ejecutar()
    assert resultado.indicadores["inversion_inicial"] == 27_000_000
    assert isinstance(resultado.indicadores["van"], float)
    assert len(resultado.flujo) == 12


def test_sensibilidad_empeora_al_subir_costos_con_precio_fijo():
    sensibilidad = tabla_sensibilidad(
        PARAMETROS,
        PRODUCTOS,
        PERSONAL,
        NO_PERSONALES,
        CONSUMOS,
        CAPITAL,
        INVERSIONES,
        metrica="van",
    )
    fila_base = sensibilidad.iloc[2]
    assert fila_base["Costo +20%"] < fila_base["Costo +0%"]


if __name__ == "__main__":
    pruebas = [
        test_iva_incluido_y_neto,
        test_margen_no_markup,
        test_estacionalidad_buena_y_mala,
        test_iva_no_es_ingreso_neto,
        test_flujo_incluye_mes_cero_y_tir_van,
        test_sensibilidad_empeora_al_subir_costos_con_precio_fijo,
    ]
    for prueba in pruebas:
        prueba()
        print(f"OK: {prueba.__name__}")
