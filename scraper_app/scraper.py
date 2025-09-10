import csv
import io
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re

def obtener_noticias_empresas(empresas, dias):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["empresa", "titulo", "descripcion", "link", "publicado", "fuente"])

    limite_tiempo = datetime.now() - timedelta(days=dias)

    for empresa in empresas:
        url = f"https://news.google.com/rss/search?q={empresa}&hl=es-419&gl=AR&ceid=AR:es-419"
        feed = feedparser.parse(url)

        if not feed.entries:
            continue

        for entry in feed.entries:
            print(f"Noticias encontradas para: {empresa}, total: {len(feed.entries)}")

            fecha_pub = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                fecha_pub = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            
            if fecha_pub and fecha_pub > limite_tiempo:
                
                titulo = entry.title if hasattr(entry, 'title') else "Sin título"
                
                
                descripcion = ""
                if hasattr(entry, 'description'):
                    soup = BeautifulSoup(entry.description, 'html.parser')
                    
                    for tag in soup.find_all(['font', 'small', 'b']):
                        tag.decompose()
                    descripcion = soup.get_text(separator=' ', strip=True)
                    
                    lineas_validas = [
                        line for line in descripcion.split('\n') 
                        if not re.search(r'hace \d+|Fuente:|Publicado', line)
                    ]
                    descripcion = ' '.join(lineas_validas).strip()

                    
                    descripcion = '\n'.join(
                        line for line in descripcion.split('\n') 
                        if not re.search(r'hace \d+ (horas|días)', line)
                    )
                
                
                if not descripcion or descripcion == titulo:
                    if hasattr(entry, 'content') and entry.content:
                        descripcion = ' '.join([c.value for c in entry.content if hasattr(c, 'value')])
                    elif hasattr(entry, 'description'):
                        descripcion = entry.description
                
                
                descripcion = descripcion if descripcion and descripcion != titulo else "Sin descripción"
                
                
                link = entry.link
                publicado = fecha_pub.strftime("%Y-%m-%d")
                fuente = entry.source.title if hasattr(entry, 'source') and hasattr(entry.source, 'title') else "Desconocida"

                writer.writerow([empresa, titulo, descripcion, link, publicado, fuente])

    return output.getvalue()