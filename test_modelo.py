import math

from modelo import (
    calcular_ire_por_ejercicio,
    ejecutar_modelo,
    iva_incluido,
    sin_iva,
    tabla_sensibilidad,
)


PARAMETROS = {
    "escenario": "CDE",
    "horizonte_meses": 12,
    "mes_inicio": 1,
    "crecimiento_mensual_pct": 0,
    "aumento_mes_bueno_pct": 20,
    "reduccion_mes_malo_pct": 10,
    "meses_buenos": [2],
    "meses_malos": [3],
    "meses_inventario_inicial": 3,
    "tasa_descuento_anual_pct": 15,
    "tasa_ire_pct": 10,
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


def test_margen_no_recargo_sobre_costo():
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
    assert math.isclose(
        fila["Ingresos con IVA"] - fila["IVA débito"],
        fila["Ventas netas"],
        rel_tol=1e-9,
    )


def test_inversion_inicial_calculada_y_tir_van():
    resultado = ejecutar()
    costo_tres_meses = 11_000_000 + 13_200_000 + 9_900_000
    assert math.isclose(
        resultado.indicadores["inventario_inicial_con_iva"],
        costo_tres_meses,
        rel_tol=1e-9,
    )
    assert math.isclose(
        resultado.indicadores["inversion_inicial"],
        11_000_000 + costo_tres_meses,
        rel_tol=1e-9,
    )
    assert isinstance(resultado.indicadores["van"], float)
    assert len(resultado.flujo) == 12


def test_inventario_cubre_primeros_meses_y_luego_compra_lo_vendido():
    resultado = ejecutar()
    primeras_compras = resultado.flujo.iloc[:3]["Compras de mercadería con IVA"]
    assert all(
        math.isclose(valor, 0.0, abs_tol=1e-9)
        for valor in primeras_compras
    )
    assert math.isclose(
        resultado.flujo.iloc[2]["Inventario final con IVA"], 0.0, abs_tol=1e-9
    )
    assert math.isclose(
        resultado.flujo.iloc[3]["Compras de mercadería con IVA"],
        resultado.resultados.iloc[3]["Costo mercadería sin IVA"] * 1.10,
        rel_tol=1e-9,
    )


def test_ire_compensa_meses_positivos_y_negativos_del_ejercicio():
    resultado = ejecutar()
    resultado_anual = resultado.resultados["Resultado operativo"].sum()
    ire_esperado = max(0.0, resultado_anual) * 0.10
    assert math.isclose(
        resultado.resultados["IRE"].sum(), ire_esperado, rel_tol=1e-9
    )
    assert all(
        math.isclose(valor, 0.0, abs_tol=1e-9)
        for valor in resultado.resultados.iloc[:11]["IRE"]
    )


def test_ire_limita_compensacion_de_perdidas_anteriores_al_20_pct():
    ire_mensual, ejercicios = calcular_ire_por_ejercicio(
        [-10.0] * 12 + [10.0] * 12,
        mes_inicio=1,
        tasa_ire=0.10,
    )
    assert math.isclose(sum(ire_mensual), 9.6, rel_tol=1e-9)
    assert math.isclose(
        ejercicios[1]["Pérdidas anteriores compensadas"], 24.0, rel_tol=1e-9
    )
    assert math.isclose(
        ejercicios[1]["Saldo de pérdidas pendientes"], 96.0, rel_tol=1e-9
    )


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
        test_margen_no_recargo_sobre_costo,
        test_estacionalidad_buena_y_mala,
        test_iva_no_es_ingreso_neto,
        test_inversion_inicial_calculada_y_tir_van,
        test_inventario_cubre_primeros_meses_y_luego_compra_lo_vendido,
        test_ire_compensa_meses_positivos_y_negativos_del_ejercicio,
        test_ire_limita_compensacion_de_perdidas_anteriores_al_20_pct,
        test_sensibilidad_empeora_al_subir_costos_con_precio_fijo,
    ]
    for prueba in pruebas:
        prueba()
        print(f"CORRECTO: {prueba.__name__}")
