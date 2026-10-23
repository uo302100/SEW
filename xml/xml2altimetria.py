import xml.etree.ElementTree as ET

class SvgGenerator:
    """
    Clase que procesa un archivo XML mediante XPath con namespaces
    y genera un gráfico vectorial SVG con el perfil de altimetría de la etapa.
    """

    def __init__(self, xml_filename, svg_filename):
        self.xml_filename = xml_filename
        self.svg_filename = svg_filename
        # Namespace obligatorio según el esquema etapa.xsd
        self.namespaces = {'ns': 'http://www.uniovi.es'}

    def cargar_xml(self):
        """Carga el documento XML y devuelve el nodo raíz."""
        tree = ET.parse(self.xml_filename)
        return tree.getroot()

    def obtener_datos_punto(self, elem):
        """Extrae altitud y distancia desde la salida de un elemento XML usando XPath."""
        alt_text = elem.find('ns:altitud_geo', self.namespaces).text.strip()
        dist_elem = elem.find('ns:distancia_salida', self.namespaces)
        dist_text = dist_elem.text.strip() if dist_elem is not None else "0.0"
        return float(alt_text), float(dist_text)

    def x_svg(self, dist):
        """Escala una distancia (km) a la coordenada X del lienzo SVG."""
        return self.margen_izq + (dist / self.longitud_total) * self.ancho_util

    def y_svg(self, alt):
        """Escala una altitud (m) a la coordenada Y del lienzo SVG."""
        return self.alto_svg - self.margen_inf - (alt / self.max_alt) * self.alto_util

    def generar_svg(self):
        root = self.cargar_xml()

        # Extraer la longitud total de la etapa mediante XPath
        longitud_total = float(root.find('ns:longitud', self.namespaces).text.strip())

        # Extraer Salida y Llegada
        salida = root.find('ns:coordenadas_salida', self.namespaces)
        alt_salida, _ = self.obtener_datos_punto(salida)
        lugar_salida = root.find('ns:lugar_salida', self.namespaces).text.strip()

        llegada = root.find('ns:coordenadas_llegada', self.namespaces)
        alt_llegada, _ = self.obtener_datos_punto(llegada)
        lugar_llegada = root.find('ns:lugar_llegada', self.namespaces).text.strip()

        # Extraer Hitos y Puntos Anónimos mediante expresiones XPath
        hitos = root.findall('.//ns:hito', self.namespaces)
        puntos_anonimos = root.findall('.//ns:punto_anonimo', self.namespaces)

        # Recopilar todos los puntos del perfil
        puntos = [{'dist': 0.0, 'alt': alt_salida, 'nombre': f"Salida: {lugar_salida}", 'tipo': 'salida'}]

        for h in hitos:
            alt, dist = self.obtener_datos_punto(h)
            nombre = h.find('ns:nombre_hito', self.namespaces).text.strip()
            tipo = h.find('ns:tipo_hito', self.namespaces).text.strip()
            puntos.append({'dist': dist, 'alt': alt, 'nombre': f"{nombre} ({tipo})", 'tipo': tipo})

        for p in puntos_anonimos:
            alt, dist = self.obtener_datos_punto(p)
            puntos.append({'dist': dist, 'alt': alt, 'nombre': '', 'tipo': 'anonimo'})

        puntos.append({'dist': longitud_total, 'alt': alt_llegada, 'nombre': f"Meta: {lugar_llegada}", 'tipo': 'llegada'})

        # Ordenar cronológicamente por distancia recorrida
        puntos.sort(key=lambda x: x['dist'])

        # Parámetros de dimensionamiento del lienzo SVG
        ancho_svg = 1200
        alto_svg = 500
        margen_izq = 80
        margen_der = 40
        margen_sup = 180
        margen_inf = 60

        ancho_util = ancho_svg - margen_izq - margen_der
        alto_util = alto_svg - margen_sup - margen_inf

        max_alt = max(p['alt'] for p in puntos) + 100

        # Parámetros que usan los métodos de escalado x_svg() e y_svg()
        self.longitud_total = longitud_total
        self.alto_svg = alto_svg
        self.margen_izq = margen_izq
        self.margen_inf = margen_inf
        self.ancho_util = ancho_util
        self.alto_util = alto_util
        self.max_alt = max_alt

        # Construcción de las listas de puntos para las etiquetas SVG polyline y polygon
        puntos_linea = []
        puntos_poligono = [f"{self.x_svg(0):.1f},{alto_svg - margen_inf}"]

        for p in puntos:
            x = self.x_svg(p['dist'])
            y = self.y_svg(p['alt'])
            puntos_linea.append(f"{x:.1f},{y:.1f}")
            puntos_poligono.append(f"{x:.1f},{y:.1f}")

        puntos_poligono.append(f"{self.x_svg(longitud_total):.1f},{alto_svg - margen_inf}")

        # Escritura del archivo vectorial SVG
        with open(self.svg_filename, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{ancho_svg}" height="{alto_svg}">\n')

            # Estilos CSS
            f.write('  <style>\n')
            f.write('    .perfil-relleno { fill: #ffcccc; fill-opacity: 0.6; }\n')
            f.write('    .perfil-linea { fill: none; stroke: #cc0000; stroke-width: 3; }\n')
            f.write('    .eje { stroke: #000000; stroke-width: 2; }\n')
            f.write('    .grid { stroke: #e0e0e0; stroke-dasharray: 4,4; stroke-width: 1; }\n')
            f.write('    .texto-eje { font-family: sans-serif; font-size: 12px; fill: #000; }\n')
            f.write('    .texto-marcador { font-family: sans-serif; font-size: 11px; font-weight: bold; fill: #111; }\n')
            f.write('    .linea-marcador { stroke: #666666; stroke-dasharray: 2,2; stroke-width: 1; }\n')
            f.write('  </style>\n')

            # Fondo blanco
            f.write('  <rect width="100%" height="100%" fill="#ffffff" />\n')

            # Grilla horizontal de altitud
            for alt_grid in range(0, int(max_alt), 100):
                y_grid = self.y_svg(alt_grid)
                f.write(f'  <line x1="{margen_izq}" y1="{y_grid:.1f}" x2="{ancho_svg - margen_der}" y2="{y_grid:.1f}" class="grid" />\n')
                f.write(f'  <text x="{margen_izq - 10}" y="{y_grid + 4:.1f}" class="texto-eje" text-anchor="end">{alt_grid} m</text>\n')

            # Dibuja el polígono de sombra y la polilínea del perfil altimétrico
            f.write(f'  <polygon points="{" ".join(puntos_poligono)}" class="perfil-relleno" />\n')
            f.write(f'  <polyline points="{" ".join(puntos_linea)}" class="perfil-linea" />\n')

            # Ejes X e Y
            f.write(f'  <line x1="{margen_izq}" y1="{alto_svg - margen_inf}" x2="{ancho_svg - margen_der}" y2="{alto_svg - margen_inf}" class="eje" />\n')
            f.write(f'  <line x1="{margen_izq}" y1="{margen_sup - 20}" x2="{margen_izq}" y2="{alto_svg - margen_inf}" class="eje" />\n')

            # Etiquetas del eje de distancias (X)
            for dist_grid in range(0, int(longitud_total) + 1, 20):
                x_grid = self.x_svg(dist_grid)
                f.write(f'  <line x1="{x_grid:.1f}" y1="{alto_svg - margen_inf}" x2="{x_grid:.1f}" y2="{alto_svg - margen_inf + 5}" class="eje" />\n')
                f.write(f'  <text x="{x_grid:.1f}" y="{alto_svg - margen_inf + 20}" class="texto-eje" text-anchor="middle">{dist_grid} km</text>\n')

            # Rotular marcadores destacados (Salida, Hitos y Llegada) con rotación a -90°
            for p in puntos:
                if p['nombre']:
                    x = self.x_svg(p['dist'])
                    y = self.y_svg(p['alt'])

                    # Línea vertical punteada hasta la cumbre/punto
                    f.write(f'  <line x1="{x:.1f}" y1="{alto_svg - margen_inf}" x2="{x:.1f}" y2="{y:.1f}" class="linea-marcador" />\n')
                    
                    # Círculo en la cota exacta
                    color_punto = "#009900" if "Puerto" in p['tipo'] else ("#0000cc" if "Sprint" in p['tipo'] else "#cc0000")
                    f.write(f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color_punto}" />\n')

                    # Texto rotado -90 grados para lectura vertical clara (estándar de altimetrías)
                    texto_completo = f"{p['nombre']} - {int(p['alt'])} m ({p['dist']} km)"
                    f.write(f'  <text x="{x + 4:.1f}" y="{y - 10:.1f}" class="texto-marcador" transform="rotate(-90 {x:.1f} {y - 10:.1f})">{texto_completo}</text>\n')

            f.write('</svg>\n')

        print("Archivo 'altimetria.svg' generado con éxito respetando las especificaciones.")

if __name__ == '__main__':
    generador = SvgGenerator('etapaEsquema.xml', 'altimetria.svg')
    generador.generar_svg()