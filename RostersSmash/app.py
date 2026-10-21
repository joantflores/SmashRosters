import csv
import random
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Optimizador de Smash")
st.title("Optimizador de rosters de Smash Ultimate")

PERSONAJES_CANDIDATOS = [
    "mario", "cloud", "pikachu", "luigi", "sonic",
    "steve", "rob", "snake", "joker", "palutena",
    "wario", "roy", "bayonetta", "wolf", "olimar",
    "yoshi", "ryu", "falco", "pacman", "corrin"
]

ruta_csv = Path(__file__).with_name("matchups.csv")

@st.cache_data
def cargar_datos(ruta):
    with open(ruta, newline="", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        columna_personaje = lector.fieldnames[0]
        columnas = [
            columna for columna in lector.fieldnames[1:]
            if columna and columna.strip()
        ]
        rivales = [columna.strip().lower() for columna in columnas]
        matriz = {}

        for fila in lector:
            personaje = (fila.get(columna_personaje) or "").strip().lower()
            if not personaje:
                continue

            matriz[personaje] = {}
            for columna, rival in zip(columnas, rivales):
                valor = (fila.get(columna) or "").strip()
                matriz[personaje][rival] = (
                    None if valor in {"", "-", "–", "—"} else float(valor)
                )

    return matriz, rivales

if not ruta_csv.exists():
    st.error("No encuentro matchups.csv junto a app.py.")
    st.stop()

matriz, rivales = cargar_datos(str(ruta_csv))

faltantes = [
    personaje for personaje in PERSONAJES_CANDIDATOS
    if personaje not in matriz
]

if faltantes:
    st.error("Faltan personajes en el CSV: " + ", ".join(faltantes))
    st.stop()

rivales_completos = [
    rival for rival in rivales
    if all(matriz[personaje].get(rival) is not None
           for personaje in PERSONAJES_CANDIDATOS)
]

def calcular_fitness(roster):
    return sum(
        max(matriz[personaje][rival] for personaje in roster)
        for rival in rivales_completos
    )

def crear_individuo(n, rng):
    return rng.sample(PERSONAJES_CANDIDATOS, n)

def seleccionar_torneo(poblacion, rng, k=3):
    participantes = rng.sample(poblacion, k)
    return max(participantes, key=calcular_fitness)

def cruzar(padre1, padre2, n, rng):
    hijo = rng.sample(padre1, n // 2)

    for personaje in padre2:
        if personaje not in hijo and len(hijo) < n:
            hijo.append(personaje)

    disponibles = [
        personaje for personaje in PERSONAJES_CANDIDATOS
        if personaje not in hijo
    ]

    while len(hijo) < n:
        personaje = rng.choice(disponibles)
        hijo.append(personaje)
        disponibles.remove(personaje)

    return hijo

def mutar(individuo, probabilidad, rng):
    mutado = individuo.copy()

    if rng.random() < probabilidad:
        disponibles = [
            personaje for personaje in PERSONAJES_CANDIDATOS
            if personaje not in mutado
        ]

        if disponibles:
            indice = rng.randrange(len(mutado))
            mutado[indice] = rng.choice(disponibles)

    return mutado

def ejecutar_genetico(n, prob_mutacion, generaciones):
    rng = random.Random(44)
    tamano_poblacion = 20

    poblacion = [
        crear_individuo(n, rng)
        for _ in range(tamano_poblacion)
    ]

    mejor_global = max(poblacion, key=calcular_fitness).copy()
    historial = [calcular_fitness(mejor_global)]

    for _ in range(generaciones):
        mejor_actual = max(poblacion, key=calcular_fitness)
        nueva_poblacion = [mejor_actual.copy()]

        while len(nueva_poblacion) < tamano_poblacion:
            padre1 = seleccionar_torneo(poblacion, rng)
            padre2 = seleccionar_torneo(poblacion, rng)

            hijo = cruzar(padre1, padre2, n, rng)
            hijo = mutar(hijo, prob_mutacion, rng)
            nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion
        mejor_actual = max(poblacion, key=calcular_fitness)

        if calcular_fitness(mejor_actual) > calcular_fitness(mejor_global):
            mejor_global = mejor_actual.copy()

        historial.append(calcular_fitness(mejor_global))

    return mejor_global, historial

st.write("Configura los parámetros del algoritmo genético.")

n = st.sidebar.slider("Tamaño del roster", 1, 20, 4)
prob_mutacion = st.sidebar.slider(
    "Probabilidad de mutación", 0.0, 0.5, 0.2, 0.05
)
generaciones = st.sidebar.slider("Generaciones", 10, 200, 50, 10)

col1, col2 = st.columns(2)
col1.metric("Personajes candidatos", len(PERSONAJES_CANDIDATOS))
col2.metric("Rivales completos", len(rivales_completos))

if st.button("Optimizar roster"):
    mejor_roster, historial = ejecutar_genetico(
        n,
        prob_mutacion,
        generaciones
    )

    fitness_final = calcular_fitness(mejor_roster)

    st.success("Optimización terminada")
    st.write("Mejor roster:", mejor_roster)
    st.metric("Fitness", fitness_final)

    detalles_counterpick = []

    for rival in rivales_completos:
        counter = max(
            mejor_roster,
            key=lambda personaje: matriz[personaje][rival]
        )

        detalles_counterpick.append({
            "Rival": rival.title(),
            "Personaje recomendado": counter.title(),
            "Valor del matchup": matriz[counter][rival]
        })

    st.subheader("Counter-pick recomendado por rival")
    st.dataframe(detalles_counterpick, use_container_width=True)
    
    st.line_chart(historial)