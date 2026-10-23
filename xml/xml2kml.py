import xml.etree.ElementTree as ET

class KmlGenerator:
    """Clase encargada de leer el archivo XML mediante XPath y generar la planimetría KML."""

    def __init__(self, xml_filename, kml_filename):
        self.xml_filename = xml_filename
        self.kml_filename = kml_filename
        self.namespaces = {'ns': 'http://www.uniovi.es'}

    def cargar_xml(self):
        tree = ET.parse(self.xml_filename)
        return tree.getroot()

    def obtener_estilos_kml(self):
        return """
    <Style id="estiloRojo">
      <IconStyle>
        <color>ff0000ff</color>
        <scale>1.2</scale>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href>
        </Icon>
      </IconStyle>
    </Style>
    <Style id="estiloVerde">
      <IconStyle>
        <color>ff00ff00</color>
        <scale>1.1</scale>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/pushpin/grn-pushpin.png</href>
        </Icon>
      </IconStyle>
    </Style>
    <Style id="estiloAzul">
      <IconStyle>
        <color>ffff0000</color>
        <scale>1.1</scale>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/pushpin/blue-pushpin.png</href>
        </Icon>
      </IconStyle>
    </Style>
    <Style id="estiloAmarillo">
      <IconStyle>
        <color>ff00ffff</color>
        <scale>0.8</scale>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
        </Icon>
      </IconStyle>
    </Style>
    <Style id="estiloLinea">
      <LineStyle>
        <color>ff0000ff</color>
        <width>4</width>
      </LineStyle>
    </Style>
"""

    def obtener_coordenadas_elemento(self, elem):
        """Extrae la tupla (longitud, latitud, altitud, distancia) de un elemento XML."""
        lon = elem.find('ns:longitud_geo', self.namespaces).text.strip()
        lat = elem.find('ns:latitud_geo', self.namespaces).text.strip()
        alt = elem.find('ns:altitud_geo', self.namespaces).text.strip()
        
        dist_elem = elem.find('ns:distancia_salida', self.namespaces)
        dist = float(dist_elem.text.strip()) if dist_elem is not None else 0.0
        
        return lon, lat, alt, dist

    def generar_kml(self):
        root = self.cargar_xml()

        # Coordenadas de Salida
        salida = root.find('ns:coordenadas_salida', self.namespaces)
        l_salida, lat_salida, alt_salida, _ = self.obtener_coordenadas_elemento(salida)
        lugar_salida = root.find('ns:lugar_salida', self.namespaces).text.strip()

        # Coordenadas de Llegada
        llegada = root.find('ns:coordenadas_llegada', self.namespaces)
        l_llegada, lat_llegada, alt_llegada, _ = self.obtener_coordenadas_elemento(llegada)
        lugar_llegada = root.find('ns:lugar_llegada', self.namespaces).text.strip()

        # Extraer Hitos y Puntos Anónimos mediante XPath
        hitos = root.findall('.//ns:hito', self.namespaces)
        puntos_anonimos = root.findall('.//ns:punto_anonimo', self.namespaces)

        # Crear una lista unificada de todos los puntos intermedios para ordenarlos por distancia
        lista_puntos = []

        for h in hitos:
            lon, lat, alt, dist = self.obtener_coordenadas_elemento(h)
            nombre = h.find('ns:nombre_hito', self.namespaces).text.strip()
            tipo = h.find('ns:tipo_hito', self.namespaces).text.strip()
            lista_puntos.append({
                'tipo_nodo': 'hito',
                'nombre': f"{nombre} ({tipo})",
                'tipo': tipo,
                'lon': lon, 'lat': lat, 'alt': alt, 'dist': dist
            })

        for i, p in enumerate(puntos_anonimos, 1):
            lon, lat, alt, dist = self.obtener_coordenadas_elemento(p)
            lista_puntos.append({
                'tipo_nodo': 'anonimo',
                'nombre': f"Punto intermedio {i}",
                'lon': lon, 'lat': lat, 'alt': alt, 'dist': dist
            })

        # ORDENAR TODOS LOS PUNTOS POR SU DISTANCIA DESDE LA SALIDA
        lista_puntos.sort(key=lambda x: x['dist'])

        with open(self.kml_filename, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            f.write('  <Document>\n')
            f.write('    <name>Planimetría Etapa 16</name>\n')
            f.write(self.obtener_estilos_kml())

            # Marcador de Salida (Rojo)
            f.write('    <Placemark>\n')
            f.write(f'      <name>Salida: {lugar_salida}</name>\n')
            f.write('      <styleUrl>#estiloRojo</styleUrl>\n')
            f.write('      <Point>\n')
            f.write(f'        <coordinates>{l_salida},{lat_salida},{alt_salida}</coordinates>\n')
            f.write('      </Point>\n')
            f.write('    </Placemark>\n')

            # Inicializar la secuencia de coordenadas para la línea
            coordenadas_linea = [f"{l_salida},{lat_salida},{alt_salida}"]

            # Escribir Marcadores Intermedios (Hitos y Puntos Anónimos)
            for punto in lista_puntos:
                if punto['tipo_nodo'] == 'hito':
                    estilo = "#estiloVerde" if "Puerto" in punto['tipo'] else "#estiloAzul"
                else:
                    estilo = "#estiloAmarillo"

                f.write('    <Placemark>\n')
                f.write(f'      <name>{punto["nombre"]}</name>\n')
                f.write(f'      <styleUrl>{estilo}</styleUrl>\n')
                f.write('      <Point>\n')
                f.write(f'        <coordinates>{punto["lon"]},{punto["lat"]},{punto["alt"]}</coordinates>\n')
                f.write('      </Point>\n')
                f.write('    </Placemark>\n')

                coordenadas_linea.append(f"{punto['lon']},{punto['lat']},{punto['alt']}")

            # Marcador de Llegada (Rojo)
            f.write('    <Placemark>\n')
            f.write(f'      <name>Llegada: {lugar_llegada}</name>\n')
            f.write('      <styleUrl>#estiloRojo</styleUrl>\n')
            f.write('      <Point>\n')
            f.write(f'        <coordinates>{l_llegada},{lat_llegada},{alt_llegada}</coordinates>\n')
            f.write('      </Point>\n')
            f.write('    </Placemark>\n')

            coordenadas_linea.append(f"{l_llegada},{lat_llegada},{alt_llegada}")

            # Línea continua trazada
            f.write('    <Placemark>\n')
            f.write('      <name>Recorrido Etapa 16</name>\n')
            f.write('      <styleUrl>#estiloLinea</styleUrl>\n')
            f.write('      <LineString>\n')
            f.write('        <extrude>1</extrude>\n')
            f.write('        <tessellate>1</tessellate>\n')
            f.write('        <coordinates>\n')
            for coord in coordenadas_linea:
                f.write(f'          {coord}\n')
            f.write('        </coordinates>\n')
            f.write('      </LineString>\n')
            f.write('    </Placemark>\n')

            f.write('  </Document>\n')
            f.write('</kml>\n')

        print("Archivo 'etapa.kml' generado con éxito y ordenado secuencialmente.")

if __name__ == '__main__':
    generador = KmlGenerator('etapaEsquema.xml', 'etapa.kml')
    generador.generar_kml()