import csv
import random
from itertools import combinations
from math import comb
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Optimizador de Smash")
st.title("Optimizador de rosters de Smash Ultimate")

st.write(
    "Selecciona los rivales y el tamaño del roster. "
    "El algoritmo recomendará personajes para cubrir esos matchups."
)

# Carga y preparación de los datos
RUTA_CSV = Path(__file__).with_name("matchups.csv")

# Estos personajes tienen datos faltantes en la matriz y no se ofrecen
# como candidatos. Los matchups contra ellos pueden seguir siendo rivales.
PERSONAJES_EXCLUIDOS = {"mii gunner", "marth"}

@st.cache_data
def cargar_datos(ruta):
    """Carga el CSV y devuelve la matriz de matchups y los nombres de rivales."""
    with open(ruta, newline="", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)

        if not lector.fieldnames or len(lector.fieldnames) < 2:
            raise ValueError(
                "El CSV debe tener una columna de personajes "
                "y al menos una columna de rivales."
            )

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


if not RUTA_CSV.exists():
    st.error("No encuentro matchups.csv junto a app.py.")
    st.stop()

try:
    matriz, todos_los_rivales = cargar_datos(str(RUTA_CSV))
except (OSError, ValueError) as error:
    st.error(f"No se pudieron cargar los datos: {error}")
    st.stop()


# Los personajes candidatos se obtienen del CSV, no de una lista fija.
PERSONAJES_ELEGIBLES = [
    personaje
    for personaje in matriz
    if personaje not in PERSONAJES_EXCLUIDOS
]

if not PERSONAJES_ELEGIBLES:
    st.error("No hay personajes candidatos disponibles en el CSV.")
    st.stop()


# Se conservan únicamente los rivales con datos completos para todos
# los candidatos que pueden seleccionarse.
RIVALES_DISPONIBLES = [
    rival
    for rival in todos_los_rivales
    if all(
        matriz[personaje].get(rival) is not None
        for personaje in PERSONAJES_ELEGIBLES
    )
]

if not RIVALES_DISPONIBLES:
    st.error("No hay rivales con datos completos.")
    st.stop()


# -------------------------------------------------------------------
# Función de aptitud y algoritmos
# -------------------------------------------------------------------

def calcular_fitness(roster, rivales_evaluacion):
    """
    Suma, para cada rival, el mejor matchup que ofrece el roster.
    """
    if not roster:
        raise ValueError("El roster no puede estar vacío.")

    return sum(
        max(matriz[personaje][rival] for personaje in roster)
        for rival in rivales_evaluacion
    )


def obtener_mejores_respuestas(roster, rivales_evaluacion):
    """Devuelve el mejor counter-pick del roster contra cada rival."""
    resultados = []

    for rival in rivales_evaluacion:
        personaje_recomendado = max(
            roster,
            key=lambda personaje: matriz[personaje][rival]
        )

        resultados.append({
            "Rival": rival.title(),
            "Personaje recomendado": personaje_recomendado.title(),
            "Valor del matchup": matriz[personaje_recomendado][rival]
        })

    return resultados


def calcular_peor_matchup(roster, rivales_evaluacion):
    """Devuelve el rival más difícil de cubrir y el valor de matchup."""
    mejores_valores = {
        rival: max(matriz[personaje][rival] for personaje in roster)
        for rival in rivales_evaluacion
    }

    rival_mas_dificil = min(mejores_valores, key=mejores_valores.get)

    return rival_mas_dificil, mejores_valores[rival_mas_dificil]


def crear_individuo(n, rng, personajes_pool):
    """Crea un roster de n personajes distintos."""
    return rng.sample(personajes_pool, n)


def seleccionar_torneo(
    poblacion,
    funcion_fitness,
    rng,
    tamano_torneo=3
):
    """Selecciona el mejor individuo de un torneo aleatorio."""
    participantes = rng.sample(poblacion, tamano_torneo)
    return max(participantes, key=funcion_fitness)


def cruzar(padre1, padre2, n, rng, personajes_pool):
    """Combina dos padres y devuelve n personajes sin repetidos."""
    hijo = rng.sample(padre1, n // 2)

    for personaje in padre2:
        if personaje not in hijo and len(hijo) < n:
            hijo.append(personaje)

    disponibles = [
        personaje
        for personaje in personajes_pool
        if personaje not in hijo
    ]

    while len(hijo) < n:
        personaje = rng.choice(disponibles)
        hijo.append(personaje)
        disponibles.remove(personaje)

    return hijo


def mutar(individuo, probabilidad, rng, personajes_pool):
    """Reemplaza un personaje con la probabilidad indicada."""
    mutado = individuo.copy()

    if rng.random() < probabilidad:
        disponibles = [
            personaje
            for personaje in personajes_pool
            if personaje not in mutado
        ]

        if disponibles:
            indice = rng.randrange(len(mutado))
            mutado[indice] = rng.choice(disponibles)

    return mutado


def ejecutar_genetico(
    n,
    prob_mutacion,
    generaciones,
    personajes_pool,
    rivales_evaluacion,
    semilla=44,
    tamano_poblacion=20
):
    """Ejecuta el algoritmo genético y devuelve el mejor roster e historial."""
    if n < 1 or n > len(personajes_pool):
        raise ValueError(
            "El tamaño del roster debe estar entre 1 "
            "y el número de candidatos seleccionados."
        )

    rng = random.Random(semilla)

    def fitness(roster):
        return calcular_fitness(roster, rivales_evaluacion)

    poblacion = [
        crear_individuo(n, rng, personajes_pool)
        for _ in range(tamano_poblacion)
    ]

    mejor_global = max(poblacion, key=fitness).copy()
    historial = [fitness(mejor_global)]

    for _ in range(generaciones):
        # Elitismo: se conserva el mejor individuo de la generación.
        mejor_actual = max(poblacion, key=fitness)
        nueva_poblacion = [mejor_actual.copy()]

        while len(nueva_poblacion) < tamano_poblacion:
            padre1 = seleccionar_torneo(poblacion, fitness, rng)
            padre2 = seleccionar_torneo(poblacion, fitness, rng)

            hijo = cruzar(
                padre1,
                padre2,
                n,
                rng,
                personajes_pool
            )
            hijo = mutar(
                hijo,
                prob_mutacion,
                rng,
                personajes_pool
            )
            nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion
        mejor_actual = max(poblacion, key=fitness)

        if fitness(mejor_actual) > fitness(mejor_global):
            mejor_global = mejor_actual.copy()

        historial.append(fitness(mejor_global))

    return mejor_global, historial


def buscar_optimo_exhaustivo(n, personajes_pool, rivales_evaluacion):
    """Evalúa todas las combinaciones posibles de n candidatos."""
    if n < 1 or n > len(personajes_pool):
        raise ValueError("El tamaño del roster no es válido.")

    mejor_roster = None
    mejor_fitness = float("-inf")

    for roster in combinations(personajes_pool, n):
        fitness = calcular_fitness(roster, rivales_evaluacion)

        if fitness > mejor_fitness:
            mejor_roster = roster
            mejor_fitness = fitness

    return list(mejor_roster), mejor_fitness


def ejecutar_experimentos_mutacion(
    personajes_pool,
    rivales_evaluacion,
    n=4,
    generaciones=50,
    semillas=range(40, 50)
):
    """
    Compara las mutaciones 0.1 y 0.2 usando las mismas semillas
    y el mismo conjunto elegido de candidatos.
    """
    semillas = list(semillas)

    roster_exacto, fitness_exacto = buscar_optimo_exhaustivo(
        n,
        personajes_pool,
        rivales_evaluacion
    )

    resumen = []
    detalle = []

    for prob_mutacion in (0.1, 0.2):
        fitnesses = []
        generaciones_al_optimo = []

        for semilla in semillas:
            roster, historial = ejecutar_genetico(
                n=n,
                prob_mutacion=prob_mutacion,
                generaciones=generaciones,
                personajes_pool=personajes_pool,
                rivales_evaluacion=rivales_evaluacion,
                semilla=semilla
            )

            fitness_final = calcular_fitness(roster, rivales_evaluacion)

            generacion_optimo = next(
                (
                    generacion
                    for generacion, mejor_fitness in enumerate(historial)
                    if mejor_fitness == fitness_exacto
                ),
                None
            )

            encontro_optimo = fitness_final == fitness_exacto
            fitnesses.append(fitness_final)

            if generacion_optimo is not None:
                generaciones_al_optimo.append(generacion_optimo)

            detalle.append({
                "Mutación": prob_mutacion,
                "Semilla": semilla,
                "Roster": ", ".join(roster),
                "Fitness": fitness_final,
                "Encontró óptimo": encontro_optimo,
                "Generación del óptimo": generacion_optimo
            })

        resumen.append({
            "Probabilidad de mutación": prob_mutacion,
            "Óptimos encontrados": (
                f"{len(generaciones_al_optimo)}/{len(semillas)}"
            ),
            "Fitness promedio": sum(fitnesses) / len(fitnesses),
            "Generación promedio al óptimo": (
                sum(generaciones_al_optimo) / len(generaciones_al_optimo)
                if generaciones_al_optimo
                else None
            )
        })

    return roster_exacto, fitness_exacto, resumen, detalle


# -------------------------------------------------------------------
# Interfaz: el usuario elige el conjunto candidato
# -------------------------------------------------------------------

st.sidebar.header("Parámetros")

rivales_usuario = st.sidebar.multiselect(
    "Selecciona los rivales",
    options=RIVALES_DISPONIBLES,
    default=[],
    format_func=str.title
)

personajes_pool = [
    personaje
    for personaje in PERSONAJES_ELEGIBLES
    if personaje not in rivales_usuario
]
tamano_pool = len(personajes_pool)

if not rivales_usuario:
    st.sidebar.info(
        "Selecciona rivales para optimizar. "
        "El experimento de referencia puede ejecutarse aparte."
    )

if not personajes_pool:
    st.sidebar.warning("No quedan personajes disponibles para el roster.")
    n = None
else:
    n = st.sidebar.slider(
        "Cantidad de personajes del roster",
        min_value=1,
        max_value=tamano_pool,
        value=min(4, tamano_pool)
    )

prob_mutacion = st.sidebar.slider(
    "Probabilidad de mutación",
    min_value=0.0,
    max_value=0.5,
    value=0.2,
    step=0.05
)

generaciones = st.sidebar.slider(
    "Generaciones",
    min_value=10,
    max_value=200,
    value=50,
    step=10
)

semilla = st.sidebar.number_input(
    "Semilla",
    min_value=0,
    max_value=1_000_000,
    value=44,
    step=1
)

col1, col2 = st.columns(2)
col1.metric("Candidatos para el roster", tamano_pool)
col2.metric("Rivales seleccionados", len(rivales_usuario))

st.caption(
    "Los rivales se mantienen fijos en el conjunto de matchups completos; "
    "el conjunto de candidatos sí lo selecciona el usuario."
)

# Optimizacion principal
if st.button( "Optimizar roster", disabled=not rivales_usuario or not personajes_pool):
    mejor_roster, historial = ejecutar_genetico(
        n=n,
        prob_mutacion=prob_mutacion,
        generaciones=generaciones,
        personajes_pool=personajes_pool,
        rivales_evaluacion=rivales_usuario,
        semilla=int(semilla)
    )

    fitness_final = calcular_fitness(
        mejor_roster,
        rivales_usuario
    )

    st.success("Optimización terminada")
    st.subheader("Roster recomendado")
    st.write(", ".join(personaje.title() for personaje in mejor_roster))
    st.metric("Fitness contra los rivales seleccionados", fitness_final)

    if len(personajes_pool) == 20 and n == 4:
        roster_exacto, fitness_exacto = buscar_optimo_exhaustivo(
            n,
            personajes_pool,
            rivales_usuario
        )

        st.subheader("Comparación con búsqueda exhaustiva")
        st.write(
            "Roster óptimo exacto:",
            ", ".join(personaje.title() for personaje in roster_exacto)
        )
        st.metric("Fitness óptimo exacto", fitness_exacto)
        st.metric(
            "Brecha del algoritmo genético",
            fitness_exacto - fitness_final
        )

    rival_peor, valor_peor = calcular_peor_matchup(
        mejor_roster,
        rivales_usuario
    )
    st.metric("Peor matchup cubierto", valor_peor)
    st.caption(f"Rival más difícil de cubrir: {rival_peor.title()}")

    st.subheader("Counter-pick recomendado por rival")
    st.dataframe(
        obtener_mejores_respuestas(mejor_roster, rivales_usuario),
        use_container_width=True
    )

    st.subheader("Progreso del algoritmo genético")
    st.line_chart(historial)

personajes_experimento = st.multiselect(
    "Candidatos para el experimento de referencia (selecciona 20)",
    options=PERSONAJES_ELEGIBLES,
    default=[],
    format_func=str.title
)

# Comparación experimental de las probabilidades de mutación

if st.button("Ejecutar comparación experimental"):
    if len(personajes_experimento) != 20:
        st.warning(
            "Selecciona exactamente 20 candidatos para el experimento."
        )
    else:
        with st.spinner(
            "Ejecutando 20 pruebas con las semillas 40–49..."
        ):
            (
                roster_exacto,
                fitness_exacto,
                resumen,
                detalle
            ) = ejecutar_experimentos_mutacion(
                personajes_pool=personajes_experimento,
                rivales_evaluacion=RIVALES_DISPONIBLES,
                n=4,
                generaciones=50,
                semillas=range(40, 50)
            )

        st.caption(
            "Experimento de referencia: 20 candidatos elegidos, "
            "82 rivales completos, roster de 4, 50 generaciones "
            "y semillas 40–49."
        )

        st.subheader("Óptimo exacto")
        st.write(
            "Roster:",
            ", ".join(personaje.title() for personaje in roster_exacto)
        )
        st.metric("Fitness óptimo exacto", fitness_exacto)

        st.subheader("Resumen por probabilidad de mutación")
        st.dataframe(resumen, use_container_width=True)

        st.caption(
            "El promedio de generaciones al óptimo considera solo "
            "las ejecuciones exitosas."
        )

        st.subheader("Resultados de las 20 ejecuciones")
        st.dataframe(detalle, use_container_width=True)