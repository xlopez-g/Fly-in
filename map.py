import re
import matplotlib.pyplot as plt
import networkx as nx
import sys

def parse_and_draw(map_data: str) -> None:
    # 1. Estructuras para almacenar los datos
    nodes = {}        # nombre -> {pos: (x, y), color: str, type: str}
    edges = []        # lista de tuplas (origen, destino, metadata_dict)
    
    # 2. Expresiones regulares para parsear
    # Match para nodos: tipo_hub: nombre x y [metadata opcional]
    node_pattern = re.compile(
        r"^(start_hub|end_hub|hub):\s*([^\s]+)\s+(-?\d+)\s+(-?\d+)(?:\s*\[(.*?)\])?"
    )
    # Match para conexiones: connection: hubA-hubB [metadata opcional]
    edge_pattern = re.compile(
        r"^connection:\s*([^\s-]+)-([^\s-]+)(?:\s*\[(.*?)\])?"
    )

    # 3. Lectura línea por línea
    for line in map_data.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("nb_drones"):
            continue

        node_match = node_pattern.match(line)
        if node_match:
            node_type, name, x, y, metadata_raw = node_match.groups()
            
            # Color por defecto según el tipo de nodo
            node_color = "skyblue"
            if node_type == "start_hub":
                node_color = "lightgreen"
            elif node_type == "end_hub":
                node_color = "gold"

            # Parsear metadatos opcionales [color=..., zone=...]
            if metadata_raw:
                for meta in metadata_raw.split():
                    if meta.startswith("color="):
                        node_color = meta.split("=")[1]

            nodes[name] = {
                "pos": (int(x), int(y)),
                "color": node_color,
                "type": node_type
            }
            continue

        edge_match = edge_pattern.match(line)
        if edge_match:
            u, v, _ = edge_match.groups()
            edges.append((u, v))

    # 4. Construcción del grafo con NetworkX
    G = nx.Graph()
    
    pos = {}
    color_map = []

    for name, data in nodes.items():
        G.add_node(name)
        pos[name] = data["pos"]
        color_map.append(data["color"])

    for u, v in edges:
        if u in nodes and v in nodes:
            G.add_edge(u, v)

    # 5. Renderizado del dibujo
    plt.figure(figsize=(10, 8))
    plt.title("Visualización de la Escena del Mapa", fontsize=14, fontweight="bold")

    # Dibujar aristas/conexiones
    nx.draw_networkx_edges(G, pos, width=2, edge_color="gray", style="solid")

    # Dibujar nodos con sus colores
    nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=1200, edgecolors="black", linewidths=1.5)

    # Etiquetas con los nombres de los nodos
    labels = {name: f"{name}\n({coords[0]},{coords[1]})" for name, coords in pos.items()}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=9, font_weight="bold", font_family="sans-serif")

    plt.grid(True, linestyle="--", alpha=0.5)
    plt.axis("on")  # Mostrar los ejes para ver las coordenadas X e Y reales
    plt.xlabel("Coordenada X")
    plt.ylabel("Coordenada Y")
    
    # Ajustar márgenes para que no se corten las etiquetas
    plt.tight_layout()
    plt.show()

# --- EJEMPLO DE USO ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error, not right argument")
        sys.exit(1)
    
    example_input = sys.argv[1]

    with open(example_input, "r") as file:
        map_data = file.read()

    parse_and_draw(map_data)
