from django.shortcuts import render , redirect
from django.urls import reverse
from .forms import EmpresaForm , Analitica
import time
import io
import json
import logging
from .scraper import obtener_noticias_empresas
from openpyxl import Workbook
from django.http import HttpResponse
import csv
from django.contrib import messages
from .feedrss import get_news_feed1 , request_scraper
from urllib.parse import urlparse
import pandas as pd
import re
from io import BytesIO
from .analiticas import google_autocomplete

def home(request):
    
    return render(request, 'home.html', {})

def buscar_empresa(request):    
    session_keys = ['buscar_empresas', 'dias', 'csv_data']
    for key in session_keys:
        if key in request.session:
            del request.session[key]
    
    if not request.session.get('search_id'):
        request.session['search_id'] = f"search-{request.user.id}-{time.time()}"
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES)
        if form.is_valid():
            empresas = []

            if form.cleaned_data['empresas_manual']:
                import re
                texto = form.cleaned_data['empresas_manual']

                
                texto = re.sub(r'[,\s;]+', '\n', texto)

             
                empresas = [e.strip() for e in texto.split('\n') if e.strip()]
            
            if not empresas:
                form.add_error('empresas_manual', 'Debe ingresar al menos una empresa')
                return render(request,"error.html", {'form': form})
            
            diferencia_dias = form.cleaned_data['dias']
            
            request.session['dias'] = diferencia_dias
            request.session['buscar_empresas'] = empresas[:100]  
            request.session.modified = True 
            request.session['search_params'] = {
                'user_id': request.user.id,
                'timestamp': time.time()
            }
            
            return redirect(f"{reverse('resultados')}?search_id={request.session['search_id']}")
    else:
        form = EmpresaForm()
    
    return render(request, 'buscar_empresas.html', {'form': form})



def resultados(request):
    
    logger = logging.getLogger(__name__)
    
    empresas = request.session.get('buscar_empresas', [])
    dias = request.session.get('dias', 0)
    if not empresas:
        return redirect('buscar_empresa')

    search_id = request.GET.get('search_id') or request.session.get('search_id')
    if not search_id or not str(search_id).startswith(f"search-{request.user.id}-"):
        messages.error(request, "Búsqueda no válida o sesión expirada")
        return redirect('busqueda_avanzada')
    
    request.session['search_id'] = search_id
    logger.info(f"Procesando request para search_id: {search_id}")
    logger.info(f"GET parameters: {dict(request.GET)}")
            
    if 'descargar' in request.GET:
        csv_data = request.session.get('csv_data')
        if csv_data:
            wb = Workbook()
            ws = wb.active
            
            
            reader = csv.reader(io.StringIO(csv_data))
            for row in reader:
                ws.append(row)
            
            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            
            response = HttpResponse(buffer.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="noticias_empresas.xlsx"'
            return response
        else:
            return redirect(f"{reverse('resultados')}?search_id={request.session['search_id']}")
    
    try:
       
        csv_data = obtener_noticias_empresas(empresas, dias)
        request.session['csv_data'] = csv_data  
        
        
        
        csv_buffer = io.StringIO(csv_data)
        reader = csv.DictReader(csv_buffer)
        noticias = list(reader)
        
        return render(request, 'resultados.html', {
            'noticias': noticias,
            'empresas_buscadas': empresas,
            'total_resultados': len(noticias),
            'search_id': search_id,
            'error': None,
        })
    
    except Exception as e:
        logger.error(f"Error al obtener noticias: {str(e)}")
        return render(request, 'error.html', {
            'error': f'Error al obtener noticias: {str(e)}'
        })







def rss_scraper_view(request):
    
    return redirect('resultados_rss')

def active_rss(request):
    
    if 'descargar' in request.GET:
        return descargar_excel(request)
    
    try:
        urls = [
          
            "https://news.google.com/rss?hl=es-419&gl=US&ceid=US:es-419",
            "https://news.google.com/rss?hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=tecnología&hl=es-419&gl=US&ceid=US:es-419",
            "https://news.google.com/rss/search?q=deportes&hl=es-419&gl=US&ceid=US:es-419",
            "https://news.google.com/rss/search?q=economía&hl=es-419&gl=US&ceid=US:es-419",
            "https://news.google.com/rss/search?q=ciencia&hl=es-419&gl=US&ceid=US:es-419",
            "https://news.google.com/rss/search?q=salud&hl=es-419&gl=US&ceid=US:es-419",
            "https://news.google.com/rss/search?q=política&hl=es-419&gl=US&ceid=US:es-419",

            # 🌍 GOOGLE NEWS - REGIONES
            "https://news.google.com/rss?hl=es-419&gl=AR&ceid=AR:es-419",  # Argentina
            "https://news.google.com/rss?hl=es&gl=ES&ceid=ES:es",          # España
            "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419",   # Brasil
            "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr",          # Francia
            "https://news.google.com/rss?hl=de&gl=DE&ceid=DE:de",          # Alemania

            # 📰 INTERNACIONALES
            "http://feeds.bbci.co.uk/news/world/rss.xml",                  # BBC Mundo
            "https://elpais.com/rss/elpais/portada.xml",                   # El País (España)
            "https://www.theguardian.com/world/rss",                       # The Guardian
            "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",      # New York Times - Mundo
            "https://feeds.a.dj.com/rss/RSSWorldNews.xml",                 # Wall Street Journal - World
            "https://www.aljazeera.com/xml/rss/all.xml",                   # Al Jazeera
            "https://www.reutersagency.com/feed/?best-topics=world&post_type=best", # Reuters Mundo

            # 🇦🇷 ARGENTINA
            "https://www.clarin.com/rss.html",                             # Clarín
            "https://www.lanacion.com.ar/rss/",                            # La Nación
            "https://www.infobae.com/argentina-rss.xml",                   # Infobae
            "https://www.pagina12.com.ar/rss/portada",                     # Página 12
            "https://www.cronista.com/files/rss/portada.xml",              # El Cronista
            "https://www.ambito.com/rss/ultimas-noticias.xml",             # Ámbito Financiero
            "https://tn.com.ar/rss.xml"                                    # TN Noticias
        ]
        
        all_news = []
        seen_links = set()
        
        for url in urls:
            try:
               
                raw_news_data = get_news_feed1(url, limit=2000)
                
                news_from_source = json.loads(raw_news_data)
                
                for news in news_from_source:
                  
                    link = news.get('link')
                    if link and link not in seen_links:
                        seen_links.add(link)
                        
                     
                        parsed_url = urlparse(link)
                        dominio = parsed_url.netloc.replace('www.', '')
                        
                        all_news.append({
                            'empresa': dominio.split('.')[0].title() if dominio else 'Unknown',
                            'titulo': news.get('title', 'Sin título'),
                            'descripcion': news.get('description', 'Sin descripción'),
                            'publicado': news.get('fecha', 'Sin fecha'),
                            'fuente': news.get('site_icon', ''),
                            'link': link
                        })
                        
            except Exception as e:
              
                print(f"Error procesando {url}: {str(e)}")
                continue
        
       
        request.session['noticias_data'] = all_news[:2000]
        
        context = {"noticias": all_news[:2000]}
        messages.success(request, f'Se encontraron {len(all_news[:2000])} noticias')
        
    except Exception as e:
        context = {"noticias": [], "error": f"Error al obtener noticias: {str(e)}"}
        messages.error(request, f'Error al obtener noticias: {str(e)}')
    
    return render(request, 'resultados_rss.html', context)

def descargar_excel(request):
    try:
        noticias = request.session.get('noticias_data', [])
        
        if not noticias:
            messages.error(request, "No hay datos para descargar")
            return render(request, 'resultados_rss.html', {"noticias": []})
        
        df = pd.DataFrame(noticias)
        df.columns = ['Empresa', 'Título', 'Descripción', 'Fecha', 'Fuente', 'Enlace']
        
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Noticias', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=noticias.xlsx'
        return response
        
    except Exception as e:
        messages.error(request, f"Error al generar archivo: {str(e)}")
        return render(request, 'resultados_rss.html', {"noticias": noticias})

def rssscraper(request):


    return render(request, 'rssscraper.html')

def search_type(request):

    return render(request, 'search_type.html')

def analitics(request):
    form = Analitica(request.POST or None)
    keyword = None
    tendencia = None 
    show_widget = False

    if request.method == 'POST' and form.is_valid():
        keyword = form.cleaned_data['Analiticas'].strip()
        if keyword:
            show_widget = True
            try:
                tendencia = google_autocomplete(keyword)
            except Exception as e:
                print("Error al obtener autocomplete:", e)
                
                form.add_error('Analiticas', f'Error al obtener datos: {str(e)}')
        else:
            form.add_error('Analiticas', 'Debe ingresar un término de búsqueda')

    
    
    context = {
        'form': form,
        'keyword': keyword,
        'tendencias': tendencia,  
        'show_widget': show_widget,
    }
    
    return render(request, 'analiticas.html', context)