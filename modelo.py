from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

import numpy_financial as npf
import pandas as pd


IVA_DIVISOR = 11.0
IVA_FACTOR = 1.10
MESES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


def numero(valor: Any, predeterminado: float = 0.0) -> float:
    try:
        resultado = float(valor)
        if math.isnan(resultado) or math.isinf(resultado):
            return predeterminado
        return resultado
    except (TypeError, ValueError):
        return predeterminado


def entero(valor: Any, predeterminado: int = 0) -> int:
    return int(round(numero(valor, predeterminado)))


def sin_iva(monto_con_iva: float) -> float:
    return max(0.0, monto_con_iva) / IVA_FACTOR


def iva_incluido(monto_con_iva: float) -> float:
    return max(0.0, monto_con_iva) / IVA_DIVISOR


def con_iva(monto_sin_iva: float) -> float:
    return max(0.0, monto_sin_iva) * IVA_FACTOR


def mensual_desde_anual(tasa_anual: float) -> float:
    if tasa_anual <= -1:
        return -1.0
    return (1.0 + tasa_anual) ** (1.0 / 12.0) - 1.0


def tir_anualizada(tir_mensual: float | None) -> float | None:
    if tir_mensual is None or not math.isfinite(tir_mensual) or tir_mensual <= -1:
        return None
    return (1.0 + tir_mensual) ** 12 - 1.0


def filas_validas(filas: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [dict(fila) for fila in (filas or []) if isinstance(fila, dict)]


def total_columna(filas: Iterable[dict[str, Any]], columna: str) -> float:
    return sum(max(0.0, numero(fila.get(columna))) for fila in filas)


def total_personal(filas: Iterable[dict[str, Any]]) -> float:
    total = 0.0
    for fila in filas:
        cantidad = max(0, entero(fila.get("Cantidad")))
        salario = max(0.0, numero(fila.get("Salario mensual")))
        cargas = max(0.0, numero(fila.get("Cargas %"))) / 100.0
        total += cantidad * salario * (1.0 + cargas)
    return total


def depreciacion_inicial_mensual(
    inversiones: Iterable[dict[str, Any]], mes: int
) -> float:
    total = 0.0
    for fila in inversiones:
        vida = max(0, entero(fila.get("Vida útil meses")))
        if vida and mes <= vida:
            total += sin_iva(numero(fila.get("Monto con IVA"))) / vida
    return total


def depreciacion_capital_recurrente(
    bienes_capital: Iterable[dict[str, Any]], mes: int
) -> float:
    total = 0.0
    for fila in bienes_capital:
        compra_neta = sin_iva(numero(fila.get("Compra mensual con IVA")))
        vida = max(0, entero(fila.get("Vida útil meses")))
        if compra_neta <= 0 or vida <= 0:
            continue
        adquisiciones_activas = min(mes, vida)
        total += compra_neta * adquisiciones_activas / vida
    return total


def nombre_mes(mes_inicio: int, indice: int) -> str:
    return MESES[(mes_inicio - 1 + indice) % 12]


@dataclass
class ResultadoModelo:
    productos: pd.DataFrame
    resultados: pd.DataFrame
    iva: pd.DataFrame
    ire_anual: pd.DataFrame
    flujo: pd.DataFrame
    indicadores: dict[str, Any]
    advertencias: list[str]


def calcular_ire_por_ejercicio(
    resultados_mensuales: Iterable[float],
    mes_inicio: int,
    tasa_ire: float,
) -> tuple[list[float], list[dict[str, Any]]]:
    """Estima el IRE por ejercicio fiscal y lo provisiona en el último mes incluido.

    Los resultados mensuales positivos y negativos se compensan dentro del mismo
    ejercicio. Las pérdidas anuales se arrastran hasta cinco ejercicios y pueden
    compensar como máximo el 20% de la renta neta positiva de cada ejercicio futuro.
    """
    resultados = [float(valor) for valor in resultados_mensuales]
    ire_por_mes = [0.0] * len(resultados)
    grupos: list[list[tuple[int, float]]] = []

    for indice, resultado in enumerate(resultados):
        ejercicio = (mes_inicio - 1 + indice) // 12
        while len(grupos) <= ejercicio:
            grupos.append([])
        grupos[ejercicio].append((indice, resultado))

    perdidas_pendientes: list[dict[str, float | int]] = []
    filas: list[dict[str, Any]] = []

    for ejercicio, meses in enumerate(grupos, start=1):
        if not meses:
            continue
        perdidas_pendientes = [
            perdida
            for perdida in perdidas_pendientes
            if int(perdida["vence_en_ejercicio"]) >= ejercicio
            and float(perdida["saldo"]) > 0
        ]
        resultado_fiscal = sum(resultado for _, resultado in meses)
        perdidas_compensadas = 0.0
        renta_imponible = 0.0
        perdida_generada = 0.0

        if resultado_fiscal > 0:
            disponible = resultado_fiscal * 0.20
            for perdida in perdidas_pendientes:
                if disponible <= 0:
                    break
                uso = min(float(perdida["saldo"]), disponible)
                perdida["saldo"] = float(perdida["saldo"]) - uso
                disponible -= uso
                perdidas_compensadas += uso
            renta_imponible = max(0.0, resultado_fiscal - perdidas_compensadas)
        elif resultado_fiscal < 0:
            perdida_generada = abs(resultado_fiscal)
            perdidas_pendientes.append(
                {"saldo": perdida_generada, "vence_en_ejercicio": ejercicio + 5}
            )

        ire_estimado = renta_imponible * tasa_ire
        ire_por_mes[meses[-1][0]] = ire_estimado
        saldo_perdidas = sum(float(perdida["saldo"]) for perdida in perdidas_pendientes)
        filas.append(
            {
                "Ejercicio fiscal": ejercicio,
                "Meses incluidos": len(meses),
                "Resultado fiscal antes de pérdidas": resultado_fiscal,
                "Pérdidas anteriores compensadas": perdidas_compensadas,
                "Renta neta imponible": renta_imponible,
                "IRE estimado": ire_estimado,
                "Pérdida fiscal generada": perdida_generada,
                "Saldo de pérdidas pendientes": saldo_perdidas,
            }
        )

    return ire_por_mes, filas


def preparar_productos(
    productos: Iterable[dict[str, Any]],
    multiplicador_cantidad: float = 1.0,
    multiplicador_costo: float = 1.0,
    precios_netos_fijos: list[float] | None = None,
) -> tuple[list[dict[str, float | str]], list[str]]:
    preparados: list[dict[str, float | str]] = []
    advertencias: list[str] = []
    for indice, fila in enumerate(filas_validas(productos), start=1):
        nombre_producto = str(fila.get("Producto") or f"Producto {indice}")
        cantidad = max(0.0, numero(fila.get("Cantidad mes 1"))) * multiplicador_cantidad
        costo_bruto_base = max(0.0, numero(fila.get("Costo unitario con IVA")))
        costo_bruto = costo_bruto_base * multiplicador_costo
        costo_neto = sin_iva(costo_bruto)
        margen = max(0.0, numero(fila.get("Margen objetivo %"))) / 100.0
        if margen >= 1.0:
            advertencias.append(
                f"{nombre_producto}: el margen debe ser menor que 100%; se limitó a 99,9%."
            )
            margen = 0.999
        if precios_netos_fijos is not None and indice - 1 < len(precios_netos_fijos):
            precio_neto = max(0.0, numero(precios_netos_fijos[indice - 1]))
        else:
            precio_neto = costo_neto / (1.0 - margen) if margen < 1.0 else 0.0
        precio_bruto = con_iva(precio_neto)
        recargo_sobre_costo = (precio_neto / costo_neto - 1.0) if costo_neto else 0.0
        preparados.append(
            {
                "Producto": nombre_producto,
                "Cantidad mes 1": cantidad,
                "Costo unitario con IVA": costo_bruto,
                "Costo unitario sin IVA": costo_neto,
                "Margen objetivo": margen,
                "Markup equivalente": recargo_sobre_costo,
                "Precio sin IVA": precio_neto,
                "Precio con IVA": precio_bruto,
            }
        )
    if not preparados:
        advertencias.append("No existen productos válidos para proyectar ventas.")
    return preparados, advertencias


def ejecutar_modelo(
    parametros: dict[str, Any],
    productos: Iterable[dict[str, Any]],
    personal: Iterable[dict[str, Any]],
    no_personales: Iterable[dict[str, Any]],
    consumos: Iterable[dict[str, Any]],
    bienes_capital: Iterable[dict[str, Any]],
    inversiones: Iterable[dict[str, Any]],
    *,
    multiplicador_cantidad: float = 1.0,
    multiplicador_costo: float = 1.0,
    precios_netos_fijos: list[float] | None = None,
) -> ResultadoModelo:
    horizonte = min(60, max(1, entero(parametros.get("horizonte_meses"), 36)))
    mes_inicio = min(12, max(1, entero(parametros.get("mes_inicio"), 1)))
    crecimiento = numero(parametros.get("crecimiento_mensual_pct")) / 100.0
    aumento_bueno = max(0.0, numero(parametros.get("aumento_mes_bueno_pct"))) / 100.0
    reduccion_malo = min(1.0, max(0.0, numero(parametros.get("reduccion_mes_malo_pct")) / 100.0))
    meses_buenos = {
        entero(mes_seleccionado)
        for mes_seleccionado in (parametros.get("meses_buenos") or [])
    }
    meses_malos = {
        entero(mes_seleccionado)
        for mes_seleccionado in (parametros.get("meses_malos") or [])
    }
    tasa_ire = max(0.0, numero(parametros.get("tasa_ire_pct"), 10.0)) / 100.0
    tasa_descuento_anual = numero(parametros.get("tasa_descuento_anual_pct"), 15.0) / 100.0
    tasa_descuento_mensual = mensual_desde_anual(tasa_descuento_anual)
    meses_inventario_solicitados = max(
        0, entero(parametros.get("meses_inventario_inicial"), 3)
    )
    meses_inventario = min(horizonte, meses_inventario_solicitados)
    valor_residual = max(0.0, numero(parametros.get("valor_residual_final")))

    productos_preparados, advertencias = preparar_productos(
        productos,
        multiplicador_cantidad=multiplicador_cantidad,
        multiplicador_costo=multiplicador_costo,
        precios_netos_fijos=precios_netos_fijos,
    )
    personal = filas_validas(personal)
    no_personales = filas_validas(no_personales)
    consumos = filas_validas(consumos)
    bienes_capital = filas_validas(bienes_capital)
    inversiones = filas_validas(inversiones)

    coincidencias = sorted(meses_buenos & meses_malos)
    if coincidencias:
        nombres = ", ".join(
            MESES[mes_coincidente - 1]
            for mes_coincidente in coincidencias
            if 1 <= mes_coincidente <= 12
        )
        advertencias.append(
            f"Los meses marcados simultáneamente como buenos y malos se trataron como normales: {nombres}."
        )

    gasto_personal = total_personal(personal)
    no_personal_bruto = total_columna(no_personales, "Monto mensual con IVA")
    consumo_bruto = total_columna(consumos, "Monto mensual con IVA")
    capital_recurrente_bruto = total_columna(bienes_capital, "Compra mensual con IVA")
    inversion_inicial_bruta = total_columna(inversiones, "Monto con IVA")
    filas_resultado: list[dict[str, Any]] = []
    filas_iva: list[dict[str, Any]] = []
    filas_flujo: list[dict[str, Any]] = []
    cantidades_por_mes: list[list[float]] = []

    for indice in range(horizonte):
        numero_mes = ((mes_inicio - 1 + indice) % 12) + 1
        if numero_mes in meses_buenos and numero_mes not in meses_malos:
            factor_estacional = 1.0 + aumento_bueno
            tipo_mes = "Bueno"
        elif numero_mes in meses_malos and numero_mes not in meses_buenos:
            factor_estacional = 1.0 - reduccion_malo
            tipo_mes = "Malo"
        else:
            factor_estacional = 1.0
            tipo_mes = "Normal"
        cantidades_mes = [
            float(producto["Cantidad mes 1"])
            * ((1.0 + crecimiento) ** indice)
            * factor_estacional
            for producto in productos_preparados
        ]
        cantidades_por_mes.append(cantidades_mes)

    ventas_brutas_lista: list[float] = []
    costo_vendido_bruto_lista: list[float] = []
    for cantidades_mes in cantidades_por_mes:
        ventas_brutas_lista.append(
            sum(
                cantidad * float(producto["Precio con IVA"])
                for cantidad, producto in zip(cantidades_mes, productos_preparados)
            )
        )
        costo_vendido_bruto_lista.append(
            sum(
                cantidad * float(producto["Costo unitario con IVA"])
                for cantidad, producto in zip(cantidades_mes, productos_preparados)
            )
        )

    inventario_inicial_bruto = sum(costo_vendido_bruto_lista[:meses_inventario])
    credito_iva_inicial = iva_incluido(inversion_inicial_bruta) + iva_incluido(
        inventario_inicial_bruto
    )
    desembolso_inicial = inversion_inicial_bruta + inventario_inicial_bruto
    if meses_inventario_solicitados > horizonte:
        advertencias.append(
            "Los meses de inventario inicial superan el horizonte; se limitaron al horizonte proyectado."
        )

    no_personal_neto = sin_iva(no_personal_bruto)
    consumo_neto = sin_iva(consumo_bruto)
    depreciaciones: list[float] = []
    resultados_operativos: list[float] = []
    for indice in range(horizonte):
        mes = indice + 1
        depreciacion = depreciacion_inicial_mensual(inversiones, mes)
        depreciacion += depreciacion_capital_recurrente(bienes_capital, mes)
        depreciaciones.append(depreciacion)
        resultados_operativos.append(
            sin_iva(ventas_brutas_lista[indice])
            - sin_iva(costo_vendido_bruto_lista[indice])
            - gasto_personal
            - no_personal_neto
            - consumo_neto
            - depreciacion
        )

    ire_por_mes, filas_ire_anual = calcular_ire_por_ejercicio(
        resultados_operativos, mes_inicio, tasa_ire
    )

    inventario_bruto = inventario_inicial_bruto
    saldo_iva = credito_iva_inicial
    flujos = [-desembolso_inicial]
    acumulado = -desembolso_inicial
    resultado_neto_acumulado = 0.0

    for indice in range(horizonte):
        mes = indice + 1
        numero_mes = ((mes_inicio - 1 + indice) % 12) + 1
        etiqueta_mes = nombre_mes(mes_inicio, indice)
        tipo_mes = "Normal"
        factor_estacional = 1.0
        if numero_mes in meses_buenos and numero_mes not in meses_malos:
            tipo_mes = "Bueno"
            factor_estacional = 1.0 + aumento_bueno
        elif numero_mes in meses_malos and numero_mes not in meses_buenos:
            tipo_mes = "Malo"
            factor_estacional = 1.0 - reduccion_malo

        ventas_brutas = ventas_brutas_lista[indice]
        iva_debito = iva_incluido(ventas_brutas)
        ventas_netas = ventas_brutas - iva_debito
        costo_vendido_bruto = costo_vendido_bruto_lista[indice]
        costo_vendido_neto = sin_iva(costo_vendido_bruto)

        compras_brutas = 0.0 if indice < meses_inventario else costo_vendido_bruto
        inventario_final_bruto = max(0.0, inventario_bruto + compras_brutas - costo_vendido_bruto)

        depreciacion = depreciaciones[indice]
        utilidad_bruta = ventas_netas - costo_vendido_neto
        resultado_operativo = resultados_operativos[indice]
        ire = ire_por_mes[indice]
        resultado_neto = resultado_operativo - ire
        resultado_neto_acumulado += resultado_neto

        iva_credito_compras = iva_incluido(compras_brutas)
        iva_credito_gastos = iva_incluido(no_personal_bruto + consumo_bruto)
        iva_credito_capital = iva_incluido(capital_recurrente_bruto)
        credito_mes = iva_credito_compras + iva_credito_gastos + iva_credito_capital
        saldo_disponible = saldo_iva + credito_mes
        iva_pagar = max(0.0, iva_debito - saldo_disponible)
        saldo_iva_final = max(0.0, saldo_disponible - iva_debito)

        recuperaciones = 0.0
        if mes == horizonte:
            recuperaciones = valor_residual

        flujo_operativo = (
            ventas_brutas
            - compras_brutas
            - gasto_personal
            - no_personal_bruto
            - consumo_bruto
            - capital_recurrente_bruto
            - iva_pagar
            - ire
        )
        flujo_neto = flujo_operativo + recuperaciones
        flujos.append(flujo_neto)
        acumulado += flujo_neto

        filas_resultado.append(
            {
                "Mes": mes,
                "Ejercicio fiscal": (mes_inicio - 1 + indice) // 12 + 1,
                "Calendario": etiqueta_mes,
                "Tipo": tipo_mes,
                "Factor estacional": factor_estacional,
                "Ingresos con IVA": ventas_brutas,
                "IVA débito": iva_debito,
                "Ventas netas": ventas_netas,
                "Costo mercadería sin IVA": costo_vendido_neto,
                "Utilidad bruta": utilidad_bruta,
                "Servicios personales": gasto_personal,
                "Servicios no personales": no_personal_neto,
                "Bienes de consumo": consumo_neto,
                "Depreciación": depreciacion,
                "Resultado operativo": resultado_operativo,
                "IRE": ire,
                "Resultado neto": resultado_neto,
            }
        )
        filas_iva.append(
            {
                "Mes": mes,
                "IVA débito": iva_debito,
                "IVA crédito compras": iva_credito_compras,
                "IVA crédito gastos": iva_credito_gastos,
                "IVA crédito capital": iva_credito_capital,
                "Saldo anterior": saldo_iva,
                "IVA a pagar": iva_pagar,
                "Saldo a favor": saldo_iva_final,
            }
        )
        filas_flujo.append(
            {
                "Mes": mes,
                "Ingresos cobrados con IVA": ventas_brutas,
                "Compras de mercadería con IVA": compras_brutas,
                "Gastos personales": gasto_personal,
                "Otros gastos con IVA": no_personal_bruto + consumo_bruto,
                "Bienes de capital con IVA": capital_recurrente_bruto,
                "IVA pagado": iva_pagar,
                "IRE provisionado": ire,
                "Recuperaciones finales": recuperaciones,
                "Flujo neto": flujo_neto,
                "Flujo acumulado": acumulado,
                "Inventario final con IVA": inventario_final_bruto,
            }
        )
        inventario_bruto = inventario_final_bruto
        saldo_iva = saldo_iva_final

    tir_mensual_valor: float | None = None
    if any(flujo < 0 for flujo in flujos) and any(flujo > 0 for flujo in flujos):
        try:
            candidata = float(npf.irr(flujos))
            if math.isfinite(candidata):
                tir_mensual_valor = candidata
        except (ValueError, OverflowError, ZeroDivisionError):
            tir_mensual_valor = None
    tir_anual = tir_anualizada(tir_mensual_valor)
    van = float(npf.npv(tasa_descuento_mensual, flujos))

    periodo_recuperacion: int | None = None
    acumulado_prueba = flujos[0]
    for mes, flujo_mes in enumerate(flujos[1:], start=1):
        acumulado_prueba += flujo_mes
        if acumulado_prueba >= 0:
            periodo_recuperacion = mes
            break

    ventas_netas_total = sum(fila["Ventas netas"] for fila in filas_resultado)
    resultado_operativo_total = sum(fila["Resultado operativo"] for fila in filas_resultado)
    resultado_neto_total = sum(fila["Resultado neto"] for fila in filas_resultado)
    utilidad_bruta_total = sum(fila["Utilidad bruta"] for fila in filas_resultado)
    cantidad_base = sum(
        float(producto["Cantidad mes 1"]) for producto in productos_preparados
    )
    contribucion_base = sum(
        float(producto["Cantidad mes 1"])
        * (
            float(producto["Precio sin IVA"])
            - float(producto["Costo unitario sin IVA"])
        )
        for producto in productos_preparados
    )
    contribucion_unitaria = contribucion_base / cantidad_base if cantidad_base else 0.0
    costos_fijos_base = 0.0
    if filas_resultado:
        primera = filas_resultado[0]
        costos_fijos_base = (
            primera["Servicios personales"]
            + primera["Servicios no personales"]
            + primera["Bienes de consumo"]
            + primera["Depreciación"]
        )
    punto_equilibrio_unidades = (
        costos_fijos_base / contribucion_unitaria if contribucion_unitaria > 0 else None
    )
    margen_contribucion = (
        contribucion_base
        / sum(
            float(producto["Cantidad mes 1"]) * float(producto["Precio sin IVA"])
            for producto in productos_preparados
        )
        if productos_preparados
        and sum(
            float(producto["Cantidad mes 1"]) * float(producto["Precio sin IVA"])
            for producto in productos_preparados
        )
        else 0.0
    )
    punto_equilibrio_neto = (
        costos_fijos_base / margen_contribucion if margen_contribucion > 0 else None
    )
    inversion_base = desembolso_inicial
    rendimiento_inversion = resultado_neto_total / inversion_base if inversion_base else None

    if tir_mensual_valor is None:
        advertencias.append(
            "La TIR no pudo calcularse: el flujo no presenta un cambio de signo válido o no tiene una solución financiera única utilizable."
        )
    if any(fila["Flujo acumulado"] < 0 for fila in filas_flujo):
        minimo = min(fila["Flujo acumulado"] for fila in filas_flujo)
        if abs(minimo) > desembolso_inicial:
            advertencias.append(
                "El saldo acumulado proyectado indica una necesidad de caja superior al desembolso inicial cargado."
            )

    tabla_productos = pd.DataFrame(productos_preparados)
    indicadores = {
        "escenario": parametros.get("escenario", "CDE"),
        "localidad_central": parametros.get("localidad_central", ""),
        "horizonte": horizonte,
        "inversion_inicial": desembolso_inicial,
        "inventario_inicial_con_iva": inventario_inicial_bruto,
        "meses_inventario_inicial": meses_inventario,
        "ventas_con_iva": sum(ventas_brutas_lista),
        "ventas_netas": ventas_netas_total,
        "utilidad_bruta": utilidad_bruta_total,
        "resultado_operativo": resultado_operativo_total,
        "resultado_neto": resultado_neto_total,
        "margen_bruto": utilidad_bruta_total / ventas_netas_total if ventas_netas_total else 0.0,
        "margen_operativo": resultado_operativo_total / ventas_netas_total if ventas_netas_total else 0.0,
        "margen_neto": resultado_neto_total / ventas_netas_total if ventas_netas_total else 0.0,
        "rendimiento_inversion": rendimiento_inversion,
        "van": van,
        "tir_mensual": tir_mensual_valor,
        "tir_anual": tir_anual,
        "periodo_recuperacion_meses": periodo_recuperacion,
        "punto_equilibrio_unidades": punto_equilibrio_unidades,
        "punto_equilibrio_neto": punto_equilibrio_neto,
        "punto_equilibrio_con_iva": con_iva(punto_equilibrio_neto or 0.0),
        "tasa_descuento_mensual": tasa_descuento_mensual,
        "credito_iva_inicial": credito_iva_inicial,
        "saldo_iva_final": saldo_iva,
        "inventario_final_con_iva": inventario_bruto,
        "flujo_minimo_acumulado": min(
            [flujos[0]]
            + [fila_flujo["Flujo acumulado"] for fila_flujo in filas_flujo]
        ),
    }
    indicadores["inversion_maxima_requerida"] = abs(min(0.0, indicadores["flujo_minimo_acumulado"]))
    return ResultadoModelo(
        productos=tabla_productos,
        resultados=pd.DataFrame(filas_resultado),
        iva=pd.DataFrame(filas_iva),
        ire_anual=pd.DataFrame(filas_ire_anual),
        flujo=pd.DataFrame(filas_flujo),
        indicadores=indicadores,
        advertencias=advertencias,
    )


def tabla_sensibilidad(
    parametros: dict[str, Any],
    productos: Iterable[dict[str, Any]],
    personal: Iterable[dict[str, Any]],
    no_personales: Iterable[dict[str, Any]],
    consumos: Iterable[dict[str, Any]],
    bienes_capital: Iterable[dict[str, Any]],
    inversiones: Iterable[dict[str, Any]],
    variaciones: Iterable[float] = (-0.20, -0.10, 0.0, 0.10, 0.20),
    metrica: str = "van",
) -> pd.DataFrame:
    variaciones = list(variaciones)
    productos_base, _ = preparar_productos(productos)
    precios_base = [
        float(producto["Precio sin IVA"]) for producto in productos_base
    ]
    filas: list[dict[str, Any]] = []
    for variacion_ventas in variaciones:
        fila: dict[str, Any] = {"Variación ventas": variacion_ventas}
        for variacion_costo in variaciones:
            resultado = ejecutar_modelo(
                parametros,
                productos,
                personal,
                no_personales,
                consumos,
                bienes_capital,
                inversiones,
                multiplicador_cantidad=1.0 + variacion_ventas,
                multiplicador_costo=1.0 + variacion_costo,
                precios_netos_fijos=precios_base,
            )
            valor = resultado.indicadores.get(metrica)
            fila[f"Costo {variacion_costo:+.0%}"] = valor
        filas.append(fila)
    return pd.DataFrame(filas)
