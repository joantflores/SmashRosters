# Optimizador de rosters de Super Smash Bros. Ultimate

Aplicación desarrollada en Python y Streamlit para recomendar un roster contra los rivales seleccionados por el usuario. El proyecto también incluye experimentos que comparan un algoritmo genético con una búsqueda exhaustiva.

## Requisitos

- Python
- Streamlit

Instala Streamlit desde PowerShell:

```powershell
python -m pip install streamlit
```

## Ejecutar la aplicación

Desde la carpeta del proyecto, ejecuta:

```powershell
python -m streamlit run app.py
```

En la página, selecciona los rivales y el tamaño del roster. La aplicación recomienda personajes distintos de los rivales seleccionados y muestra la aptitud del roster, el peor matchup cubierto, los counter-picks y el progreso del algoritmo genético.

## Función de aptitud

Para cada rival, se toma el mejor valor de matchup entre los personajes del roster. La aptitud total es la suma de esos valores:

\[
F(R,E)=\sum_{e \in E}\max_{c \in R} M(c,e)
\]

Donde:

- \(R\) es el roster recomendado.
- \(E\) es el conjunto de rivales seleccionados.
- \(M(c,e)\) es el valor del matchup entre el personaje \(c\) y el rival \(e\).

## Experimento reproducible

El archivo `experimentos.py` compara el algoritmo genético con la búsqueda exhaustiva en el caso base:

- 20 personajes candidatos.
- Roster de 4 personajes.
- 82 rivales completos.
- 4,845 combinaciones evaluadas exhaustivamente.
- Probabilidades de mutación de 0.1 y 0.2.
- 10 ejecuciones por probabilidad, con semillas de 40 a 49.

Ejecuta el experimento desde la carpeta del proyecto:

```powershell
python experimentos.py
```

Cuando se solicite, ingresa los 20 candidatos separados por comas.

## Archivos del proyecto

- `app.py`: interfaz Streamlit y recomendación de roster.
- `experimentos.py`: experimentos del algoritmo genético y búsqueda exhaustiva.
- `matchups.csv`: datos de matchups.
- `assets/characters/`: imágenes de los personajes.

## Alcance

Los resultados dependen de los valores incluidos en `matchups.csv`. La aptitud resume los valores de matchup disponibles; no predice directamente el resultado de partidas reales.
