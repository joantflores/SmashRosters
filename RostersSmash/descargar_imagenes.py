from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

CARPETA = Path(__file__).parent / "assets" / "characters"
BASE_URL = "https://www.smashbros.com/assets_v2/img/fighter"

PERSONAJES = [
    "steve", "sonic", "rob", "snake", "mr game & watch",
    "pyra & mythra", "diddy kong", "fox", "cloud", "palutena",
    "kazuya", "samus/dark samus", "joker", "min min", "wario",
    "roy", "bayonetta", "luigi", "wolf", "mario", "olimar", "yoshi",
    "peach/daisy", "ryu", "falco", "pac-man", "corrin", "ness",
    "rosalina & luma", "shulk", "pokemon trainer", "mega man",
    "captain falcon", "sora", "lucina", "young link", "greninja",
    "sephiroth", "ken", "terry", "hero", "ice climbers", "byleth",
    "pikachu", "sheik", "zero suit samus", "toon link", "donkey kong",
    "bowser", "inkling", "incineroar", "meta knight", "wii fit trainer",
    "mii brawler", "ike", "pit/dark pit", "pichu", "duck hunt",
    "belmonts", "ridley", "robin", "banjo & kazooie", "lucas", "link",
    "jigglypuff", "zelda", "bowser jr", "dr mario", "chrom", "lucario",
    "king dedede", "villager", "isabelle", "king k rool", "kirby",
    "little mac", "mii swordfighter", "piranha plant", "mewtwo",
    "ganondorf",
]

# Nombres de carpeta usados por el link de los personajes.
SLUGS_OFICIALES = {
    "pyra & mythra": "homura",
    "pac-man": "pac_man",
    "incineroar": "gaogaen",
    "isabelle": "shizue",
    "piranha plant": "packun_flower",
    "hero": "dq_hero",
    "belmonts": "simon",
    "peach/daisy": "peach",
    "samus/dark samus": "samus",
    "pit/dark pit": "pit",
    "mii brawler": "mii_fighter",
    "mii swordfighter": "mii_fighter",
}

def nombre_archivo(nombre):
    return (
        nombre.lower()
        .replace("&", "and")
        .replace("/", "_")
        .replace(" ", "_")
        + ".png"
    )

CARPETA.mkdir(parents=True, exist_ok=True)

descargadas = 0
existentes = 0
fallidas = []

for personaje in PERSONAJES:
    destino = CARPETA / nombre_archivo(personaje)

    # Conserva los PNG que ya estan guardados.
    if destino.exists():
        existentes += 1
        continue

    slug = SLUGS_OFICIALES.get(
        personaje,
        personaje.lower().replace(" ", "_").replace("-", "_")
    )
    url = f"{BASE_URL}/{slug}/main.png"
    solicitud = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urlopen(solicitud, timeout=20) as respuesta:
            datos = respuesta.read()

        # Evita guardar una pagina de error como si fuera una imagen.
        if not datos.startswith(b"\x89PNG\r\n\x1a\n"):
            fallidas.append(personaje)
            continue

        destino.write_bytes(datos)
        descargadas += 1
        print(f"Descargada: {destino.name}")

    except (HTTPError, URLError, TimeoutError, OSError) as error:
        fallidas.append(personaje)
        print(f"No se pudo descargar {personaje}: {error}")

print(f"\nNuevas imágenes: {descargadas}")
print(f"Ya existentes: {existentes}")
print(f"Sin imagen descargada: {', '.join(fallidas) if fallidas else 'ninguno'}")