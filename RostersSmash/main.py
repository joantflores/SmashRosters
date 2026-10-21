import csv
import random
from itertools import combinations
from math import comb

# Parámetros del experimento
PERSONAJES_CANDIDATOS = [
    "mario", "cloud", "pikachu", "luigi", "sonic",
    "steve", "rob", "snake", "joker", "palutena",
    "wario", "roy", "bayonetta", "wolf", "olimar",
    "yoshi", "ryu", "falco", "pacman", "corrin"
]

N = 4
TAMANO_POBLACION = 20
GENERACIONES = 50
PROB_MUTACION = 0.1
SEMILLA = 44

# Cargar la matriz de matchups desde el CSV
with open("matchups.csv", newline="", encoding="utf-8") as archivo:
    lector = csv.DictReader(archivo)

    if not lector.fieldnames:
        raise ValueError("El CSV no tiene encabezados.")

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

        # Ignorar filas vacías.
        if not personaje:
            continue

        matriz[personaje] = {}

        for columna, rival in zip(columnas_rivales, rivales):
            valor = (fila.get(columna) or "").strip()

            if valor in {"", "-", "–", "—"}:
                matriz[personaje][rival] = None
            else:
                matriz[personaje][rival] = float(valor)

# Confirmar que todos los candidatos existen en la matriz.
candidatos_faltantes = [
    personaje
    for personaje in PERSONAJES_CANDIDATOS
    if personaje not in matriz
]

if candidatos_faltantes:
    raise ValueError(
        "No se encontraron estos personajes en el CSV: "
        + ", ".join(candidatos_faltantes)
    )

if N > len(PERSONAJES_CANDIDATOS):
    raise ValueError("N no puede ser mayor que la cantidad de candidatos.")

# Usar solo rivales con matchup conocido contra todos los candidatos.
rivales_completos = [
    rival
    for rival in rivales
    if all(
        matriz[personaje][rival] is not None
        for personaje in PERSONAJES_CANDIDATOS
    )
]

def calcular_fitness(roster):
    """Suma el mejor counter-pick del roster para cada rival."""
    return sum(
        max(matriz[personaje][rival] for personaje in roster)
        for rival in rivales_completos
    )

def crear_individuo():
    """Crea un roster de N personajes distintos."""
    return random.sample(PERSONAJES_CANDIDATOS, N)

def seleccionar_torneo(poblacion, k=3):
    """Elige el mejor individuo de k participantes al azar."""
    participantes = random.sample(poblacion, k)
    return max(participantes, key=calcular_fitness)

def cruzar(padre1, padre2):
    """Combina dos padres y conserva exactamente N personajes distintos."""
    hijo = random.sample(padre1, N // 2)

    for personaje in padre2:
        if personaje not in hijo and len(hijo) < N:
            hijo.append(personaje)

    while len(hijo) < N:
        personaje = random.choice(PERSONAJES_CANDIDATOS)
        if personaje not in hijo:
            hijo.append(personaje)

    return hijo

def mutar(individuo, probabilidad=PROB_MUTACION):
    """Sustituye un personaje con la probabilidad indicada."""
    mutado = individuo.copy()

    if random.random() < probabilidad:
        disponibles = [
            personaje
            for personaje in PERSONAJES_CANDIDATOS
            if personaje not in mutado
        ]

        if disponibles:
            indice = random.randrange(N)
            mutado[indice] = random.choice(disponibles)

    return mutado

def crear_siguiente_generacion(poblacion):
    """Aplica elitismo, selección por torneo, cruce y mutación."""
    mejor = max(poblacion, key=calcular_fitness)
    nueva_generacion = [mejor.copy()]

    while len(nueva_generacion) < len(poblacion):
        padre1 = seleccionar_torneo(poblacion)
        padre2 = seleccionar_torneo(poblacion)

        hijo = cruzar(padre1, padre2)
        hijo = mutar(hijo)
        nueva_generacion.append(hijo)

    return nueva_generacion

# Mostrar el tamaño del problema evaluado.
print("Candidatos:", len(PERSONAJES_CANDIDATOS))
print("Tamaño del roster N:", N)
print("Rivales completos:", len(rivales_completos))
print("Combinaciones posibles:", comb(len(PERSONAJES_CANDIDATOS), N))

if not rivales_completos:
    print("No hay rivales con datos completos para estos candidatos.")
else:
    # Búsqueda exhaustiva: calcular el óptimo exacto una sola vez.
    resultados = [
        (roster, calcular_fitness(roster))
        for roster in combinations(PERSONAJES_CANDIDATOS, N)
    ]
    resultados.sort(key=lambda resultado: resultado[1], reverse=True)

    roster_optimo, fitness_optimo = resultados[0]

    print("\nÓptimo exacto:", roster_optimo, fitness_optimo)
    print("\nEjecuciones del algoritmo genético:")

    resultados_genetico = []

    # Probar 10 semillas, de la 40 a la 49.
    for semilla in range(40, 50):
        random.seed(semilla)

        poblacion = [
            crear_individuo()
            for _ in range(TAMANO_POBLACION)
        ]

        mejor_global = max(poblacion, key=calcular_fitness)
        generacion_optimo = (
            0 if calcular_fitness(mejor_global) == fitness_optimo else None
        )

        for generacion in range(1, GENERACIONES + 1):
            poblacion = crear_siguiente_generacion(poblacion)
            mejor_generacion = max(poblacion, key=calcular_fitness)

            if calcular_fitness(mejor_generacion) > calcular_fitness(mejor_global):
                mejor_global = mejor_generacion.copy()

            if (
                generacion_optimo is None
                and calcular_fitness(mejor_global) == fitness_optimo
            ):
                generacion_optimo = generacion

        fitness_final = calcular_fitness(mejor_global)
        resultados_genetico.append(fitness_final)

        if generacion_optimo is None:
            estado = "no encontró el óptimo"
        else:
            estado = f"encontró el óptimo en generación {generacion_optimo}"

        print(
            f"Semilla {semilla}: fitness {fitness_final} — "
            f"{estado} — roster {mejor_global}"
        )

    aciertos = sum(
        fitness == fitness_optimo
        for fitness in resultados_genetico
    )
    promedio = sum(resultados_genetico) / len(resultados_genetico)

    print("\nResumen de las 10 ejecuciones:")
    print(f"Encontró el óptimo: {aciertos}/10 veces")
    print(f"Fitness promedio: {promedio:.2f}")
    print(f"Mejor fitness obtenido: {max(resultados_genetico):.1f}")