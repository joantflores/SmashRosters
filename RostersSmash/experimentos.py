import csv
import random
from itertools import combinations
from pathlib import Path

RUTA_CSV = Path(__file__).with_name("matchups.csv")

N = 4
TAMANO_POBLACION = 20
GENERACIONES = 50
SEMILLAS = range(40, 50)
PROBABILIDADES_MUTACION = (0.1, 0.2)
PERSONAJES_EXCLUIDOS = {"mii gunner", "marth"}

def cargar_datos(ruta):
    """Lee el CSV y devuelve la matriz y las columnas de rivales."""
    with open(ruta, newline="", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)

        if not lector.fieldnames or len(lector.fieldnames) < 2:
            raise ValueError("El CSV no tiene los encabezados esperados.")

        columna_personaje = lector.fieldnames[0]
        columnas_rivales = [
            columna
            for columna in lector.fieldnames[1:]
            if columna and columna.strip()
        ]
        rivales = [columna.strip().lower() for columna in columnas_rivales]

        matriz = {}

        for fila in lector:
            personaje = (fila.get(columna_personaje) or "").strip().lower()

            if not personaje:
                continue

            matriz[personaje] = {}

            for columna, rival in zip(columnas_rivales, rivales):
                valor = (fila.get(columna) or "").strip()

                if valor in {"", "-", "–", "—"}:
                    matriz[personaje][rival] = None
                else:
                    matriz[personaje][rival] = float(valor)

    return matriz, rivales

def pedir_candidatos(personajes_elegibles):
    """Solicita al usuario exactamente 20 candidatos por consola."""
    print("Personajes elegibles:")
    print(", ".join(personajes_elegibles))

    while True:
        entrada = input(
            "\nEscribe 20 candidatos separados por comas:\n> "
        )

        candidatos = [
            nombre.strip().lower()
            for nombre in entrada.split(",")
            if nombre.strip()
        ]

        if len(candidatos) != 20:
            print(f"Seleccionaste {len(candidatos)}. Deben ser exactamente 20.")
            continue

        if len(set(candidatos)) != 20:
            print("Hay personajes repetidos. Inténtalo de nuevo.")
            continue

        desconocidos = [
            personaje
            for personaje in candidatos
            if personaje not in personajes_elegibles
        ]

        if desconocidos:
            print(
                "Estos nombres no son elegibles o no coinciden con el CSV: "
                + ", ".join(desconocidos)
            )
            continue

        return candidatos

def calcular_fitness(roster, matriz, rivales):
    """Suma el mejor matchup del roster contra cada rival."""
    return sum(
        max(matriz[personaje][rival] for personaje in roster)
        for rival in rivales
    )


def buscar_optimo_exhaustivo(candidatos, matriz, rivales):
    """Evalua todas las combinaciones posibles de cuatro candidatos."""
    mejor_roster = None
    mejor_fitness = float("-inf")

    for roster in combinations(candidatos, N):
        fitness = calcular_fitness(roster, matriz, rivales)

        if fitness > mejor_fitness:
            mejor_roster = roster
            mejor_fitness = fitness

    return list(mejor_roster), mejor_fitness

def crear_individuo(candidatos, rng):
    return rng.sample(candidatos, N)

def seleccionar_torneo(poblacion, fitness, rng, tamano_torneo=3):
    participantes = rng.sample(poblacion, tamano_torneo)
    return max(participantes, key=fitness)

def cruzar(padre1, padre2, candidatos, rng):
    hijo = rng.sample(padre1, N // 2)

    for personaje in padre2:
        if personaje not in hijo and len(hijo) < N:
            hijo.append(personaje)

    disponibles = [
        personaje
        for personaje in candidatos
        if personaje not in hijo
    ]

    while len(hijo) < N:
        personaje = rng.choice(disponibles)
        hijo.append(personaje)
        disponibles.remove(personaje)

    return hijo

def mutar(individuo, candidatos, probabilidad, rng):
    mutado = individuo.copy()

    if rng.random() < probabilidad:
        disponibles = [
            personaje
            for personaje in candidatos
            if personaje not in mutado
        ]

        if disponibles:
            indice = rng.randrange(len(mutado))
            mutado[indice] = rng.choice(disponibles)

    return mutado

def ejecutar_genetico(candidatos, matriz, rivales, prob_mutacion, semilla):
    rng = random.Random(semilla)

    def fitness(roster):
        return calcular_fitness(roster, matriz, rivales)

    poblacion = [
        crear_individuo(candidatos, rng)
        for _ in range(TAMANO_POBLACION)
    ]

    mejor_global = max(poblacion, key=fitness).copy()
    historial = [fitness(mejor_global)]

    for _ in range(GENERACIONES):
        mejor_actual = max(poblacion, key=fitness)
        nueva_poblacion = [mejor_actual.copy()]  # Elitismo

        while len(nueva_poblacion) < TAMANO_POBLACION:
            padre1 = seleccionar_torneo(poblacion, fitness, rng)
            padre2 = seleccionar_torneo(poblacion, fitness, rng)

            hijo = cruzar(padre1, padre2, candidatos, rng)
            hijo = mutar(hijo, candidatos, prob_mutacion, rng)
            nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion
        mejor_actual = max(poblacion, key=fitness)

        if fitness(mejor_actual) > fitness(mejor_global):
            mejor_global = mejor_actual.copy()

        historial.append(fitness(mejor_global))

    return mejor_global, historial

def main():
    if not RUTA_CSV.exists():
        raise FileNotFoundError(
            "No encuentro matchups.csv junto a experimentos.py."
        )

    matriz, todos_los_rivales = cargar_datos(RUTA_CSV)

    personajes_elegibles = [
        personaje
        for personaje in matriz
        if personaje not in PERSONAJES_EXCLUIDOS
    ]

    candidatos = pedir_candidatos(personajes_elegibles)

    rivales_completos = [
        rival
        for rival in todos_los_rivales
        if all(
            matriz[personaje].get(rival) is not None
            for personaje in candidatos
        )
    ]

    if len(rivales_completos) != 82:
        raise ValueError(
            f"Se esperaban 82 rivales completos, pero hay "
            f"{len(rivales_completos)} para estos candidatos."
        )

    combinaciones = list(combinations(candidatos, N))
    print(f"\nCandidatos: {len(candidatos)}")
    print(f"Tamaño del roster: {N}")
    print(f"Rivales completos: {len(rivales_completos)}")
    print(f"Combinaciones posibles: {len(combinaciones)}")

    roster_exacto, fitness_exacto = buscar_optimo_exhaustivo(
        candidatos,
        matriz,
        rivales_completos
    )

    print("\nÓptimo exacto:", roster_exacto, fitness_exacto)
    print("\nEjecuciones del algoritmo genético:")

    resumen = []

    for prob_mutacion in PROBABILIDADES_MUTACION:
        fitnesses = []
        generaciones_al_optimo = []

        for semilla in SEMILLAS:
            roster, historial = ejecutar_genetico(
                candidatos,
                matriz,
                rivales_completos,
                prob_mutacion,
                semilla
            )

            fitness_final = calcular_fitness(
                roster,
                matriz,
                rivales_completos
            )

            generacion_optimo = next(
                (
                    generacion
                    for generacion, fitness in enumerate(historial)
                    if fitness == fitness_exacto
                ),
                None
            )

            encontro_optimo = fitness_final == fitness_exacto
            fitnesses.append(fitness_final)

            if generacion_optimo is not None:
                generaciones_al_optimo.append(generacion_optimo)

            if generacion_optimo is None:
                estado = "no encontró el óptimo"
            else:
                estado = (
                    f"encontró el óptimo en generación "
                    f"{generacion_optimo}"
                )

            print(
                f"Mutación {prob_mutacion} | Semilla {semilla} | "
                f"Fitness {fitness_final} | {estado} | Roster {roster}"
            )

        resumen.append({
            "Probabilidad de mutación": prob_mutacion,
            "Óptimos encontrados": (
                f"{len(generaciones_al_optimo)}/{len(list(SEMILLAS))}"
            ),
            "Fitness promedio": sum(fitnesses) / len(fitnesses),
            "Generación promedio al óptimo": (
                sum(generaciones_al_optimo) / len(generaciones_al_optimo)
                if generaciones_al_optimo
                else None
            )
        })

    print("\nResumen:")
    for fila in resumen:
        print(fila)

if __name__ == "__main__":
    main()