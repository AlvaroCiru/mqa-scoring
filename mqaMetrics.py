'''
YODA (Your Open DAta)
EU CEF Action 2019-ES-IA-0121
University of Cantabria
Developer: Johnny Choque (jchoque@tlmat.unican.es)
'''
from wordhoard import Synonyms, Hypernyms, Hyponyms
import re
import nltk
import requests
import re
from rdflib import Graph, URIRef
import urllib.request
from openai import OpenAI
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn
from nltk.corpus.reader import NOUN
from nltk.tag import pos_tag
from datetime import datetime, timedelta, date
import pytz

#Funciones auxiliares 


def tiene_relacion_chatgpt_keywords(keywords, description):
  client = OpenAI()
  entrada = "Keywords: " + ". " .join(keywords) + "\nText: " + ". ".join(description)
  print(f'Esta es la entrada a chatgpt ----------{entrada}')
  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "Eres un asistente para publicadores de datasets en portales de datos abiertos.Vas a recibir dos inputs de texto. Un array de palabras clave keywords describiendo el dataset, y un pequeño texto description, incluido en varios idiomas, en el que se describe la información del dataset.Tu misión es determinar si el conjunto de keywords está bien escogido, basado en si la mayoria de keywords tienen relación con la descripción del dataset, basandote en el significado de las palabras y su contexto.Tu respuesta será en inglés.Tu misión también será proporcionar palabras clave que podrían ser útiles para describir el dataset.Tu respuesta será del tipo: Yes/no, the keywords are/are not related with the description given because... y despues sugerir palabras clave que describan mejor el dataset. La decisión de responder Yes se basará en si las keywords tienen relación con la descripción"},
      {"role": "user", "content": entrada}
    ]
  )
  result = False  
  print(completion.choices[0].message.content)

  mi_string = completion.choices[0].message.content

# Expresión regular para verificar si comienza con "yes" o "no"
  expresion_regular = re.compile(r'^(yes|no)', re.IGNORECASE)

# Comprobación
  resultado = expresion_regular.match(mi_string)
  if resultado:
    result = resultado.group(1).lower() == "yes"
  else:
    result = False
  return result

def tiene_relacion_chatgpt_theme(theme, description):
  client = OpenAI()
  entrada = "Tema: " + ". " .join(theme) + "\nText: " + ". ".join(description)
  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "Vas a recibir una lista de una o varias URI del portal de datos abiertos europeo que especifica el tema de un dataset, además de una lista de descripciones que explican en un pequeño texto el dataset. Tu misión es determinar si la URI o URIS escogidas tienen relación en significado con la descripcion del dataset. Tu respuesta será del tipo: Yes/No, the theme or themes used to describe the dataset do not fit well in the description. Si la lista de temas que recibes no contiene URI, devuelve: No. Si encuentras otro tema establecido como estándar en el portal de datos abiertos europeo que tiene mejor relación con la descripcion responde: No, The theme chosen is not related with the dataset, the theme (theme) would be a better one. Si no encuentras uno en en estándar, sugiere una categoría que describiría mejor al conjunto de datos"},
      {"role": "user", "content": entrada}
    ]
  )
  result = False  
  print(completion.choices[0].message.content)

  mi_string = completion.choices[0].message.content

# Expresión regular para verificar si comienza con "yes" o "no"
  expresion_regular = re.compile(r'^(yes|no)', re.IGNORECASE)

# Comprobación
  resultado = expresion_regular.match(mi_string)
  if resultado:
    result = resultado.group(1).lower() == "yes"
  else:
    result = False
  return result

#Comprobación de que la fecha corresponde al estándar dateTime
def es_formato_datetime(cadena):
  checked = True
  print(f'Esta es la cadena {type(cadena)}')
  # Expresión regular para verificar el formato dateTime    
  patron = r'^-?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|([-+]\d{2}:\d{2}))?$'
  print(f'La cadena coincide con el estandar ----------->{bool(re.match(patron, cadena))}')
  if bool(re.match(patron, cadena)):
    checked = checked and True
  else:
    checked = checked and False

  # Validación de años, meses y días
  try:
      year, month, day = map(int, cadena[:10].split('-'))
      if year < 1 or month < 1 or month > 12 or day < 1 or day > 31:
          checked = checked and False
  except ValueError:
      checked = checked and False
  print(f'En la primera ---------->{checked}')

  # Validación de la hora
  try:
      hour, minute, second = map(int, cadena[11:19].split(':'))
      if hour < 0 or hour > 23 or minute < 0 or minute > 59 or second < 0 or second > 59:
          checked = checked and False
  except ValueError:
      checked = checked and False
  print(f'En la segunda ---------->{checked}')


  return checked

def flatten_list(input_list):
  result = []
  for item in input_list:
      if isinstance(item, list):
          result.extend(flatten_list(item))  # Llamada recursiva si el item es una lista
      else:
          result.append(item)
  return result   
#Comprobación de que un String es una palabra con sentido
def is_word(word):
  synsets = wn.synsets(word) 
  return  len(synsets)>0

#Comprobación de que un string es un sustantivo váido mediante tokenizacion por nltk
def is_valuable_word(word):  
  result = False  
  tagged_word = pos_tag(word_tokenize(word))    
  for word, tag in tagged_word:
    if tag == 'NN' or tag == 'VB' or tag == 'JJ':
      result = True     
  return result

#Comprobación de que una lista de strings tienen alguna relación de significado entre ellos (utilizando nltk wordnet)


def relacion_keywords(keywords):  

  result = True
  keywords_related = []

  keywords_shh = set()
  keywords_shh_duplicated = set()

  for keyword in keywords:
    synonym = Synonyms(search_string=keyword)
    hypernym = Hypernyms(search_string=keyword)
    hyponym = Hyponyms(search_string=keyword)   
    try:
      keywords_related.extend(synonym.find_synonyms())
      keywords_related.extend(hypernym.find_hypernyms())
      keywords_related.extend(hyponym.find_hyponyms())
    except Exception as e:
      print("Se ha producido una excepción del tipo:", type(e),__name__)
      continue
  
  
  
  
  for shh_word in keywords_related:
    if shh_word in keywords_shh:
      keywords_shh_duplicated.add(shh_word)
    else:
      keywords_shh.add(shh_word)

  palabras_comun = keywords_shh_duplicated
  if len(palabras_comun) > 0:
    result = result and True
  else:
    result = result and False
  return result

def recent_date(issued):
    # Verificar si el objeto es datetime.date pero no datetime.datetime
    if isinstance(issued, date) and not isinstance(issued, datetime):
        # Convertir date a datetime en UTC
        issued = datetime(issued.year, issued.month, issued.day, tzinfo=pytz.utc)
    elif issued.tzinfo is None:
        # Si es datetime pero sin tzinfo, asignar UTC
        issued = issued.replace(tzinfo=pytz.utc)
    else:
        # Convertir a UTC si tiene tzinfo
        issued = issued.astimezone(pytz.utc)

    # Obtener la fecha y hora actual en UTC
    fecha_actual = datetime.now(pytz.utc)
  
    # Calcular la fecha límite (hace 5 años desde la fecha actual)
    fecha_limite = fecha_actual - timedelta(days=5*365)
  
    # Comparar la fecha de publicación con la fecha límite
    return issued >= fecha_limite

#Comprobaciones mqa-scoring

def accessURL(urls, weight, mqa_access, timeout=5):
  checked = True
  for url in urls:
    try:
      request = urllib.request.Request(url, method='HEAD')
      response = urllib.request.urlopen(request, timeout=timeout)
      res = response.getcode()
      if res in range(200, 399):
        checked = checked and True
      else:
        checked = checked and False
    except urllib.error.HTTPError as e:
      print(f"HTTPError: {e.code} - {e.reason} for URL: {url}")
      checked = False
    except urllib.error.URLError as e:
      print(f"URLError: {e.reason} for URL: {url}")
      checked = False
    except Exception as e:
      print(f"Error: {e} for URL: {url}")
      checked = False

  if checked:
    weight += 50
    mqa_access += 50
    print('   Result: OK. Weight assigned 50')
  else:
    print('   Result: ERROR - One or more URLs responded with a status code outside the 200-399 range or failed to respond')
  return weight, mqa_access


def downloadURL(urls, weight, mqa_download, mqa_download_access):
  checked = True
  print('   Result: OK. The property is set. Weight assigned 20')
  weight = weight + 20
  mqa_download = mqa_download + 20
  for url in urls:
    try:
      response = urllib.request.urlopen(url)
      res = response.getcode()
      if res in range(200, 399):
        checked = checked and True
      else:
        checked = checked and False
    except:
      checked = checked and False
  if checked:
    weight = weight + 30
    mqa_download_access = mqa_download_access + 30
    print('   Result: OK. Weight assigned 30')
  else:
    print('   Result: ERROR - Responded status code of HTTP HEAD request is not in the 200 or 300 range')
  return weight, mqa_download, mqa_download_access   

def keyword(weight, mqa_keyword):
  weight = weight + 30
  mqa_keyword = mqa_keyword + 30
  print('   Result: OK. The property is set. Weight assigned 30')
  return weight, mqa_keyword

def theme(weight, mqa_theme):
  weight = weight + 30
  mqa_theme = mqa_theme + 30
  print('   Result: OK. The property is set. Weight assigned 30')
  return weight, mqa_theme

def spatial(weight, mqa_spatial):
  weight = weight + 20
  mqa_spatial = mqa_spatial + 20
  print('   Result: OK. The property is set. Weight assigned 20')
  return weight, mqa_spatial

def temporal(weight, mqa_temporal):
  weight = weight + 20
  mqa_temporal = mqa_temporal + 20
  print('   Result: OK. The property is set. Weight assigned 20')
  return weight, mqa_temporal

def format(urls, mach_read_voc, non_prop_voc, weight, mqa_format, mqa_non_propietary, mqa_machine_readable):
  mach_read_checked = True
  non_prop_checked = True
  found_checked = True
  print('   Result: OK. The property is set. Weight assigned 20')
  weight = weight + 20
  mqa_format = mqa_format + 20
  try:

    for url in urls:
      if str(url) in mach_read_voc:
        mach_read_checked = mach_read_checked and True
        
      else:
        mach_read_checked = mach_read_checked and False
      if str(url) in non_prop_voc:
        non_prop_checked = non_prop_checked and True
      else:
        non_prop_checked = non_prop_checked and False

      g = Graph()
      g.parse(url, format="application/rdf+xml")
  except Exception as e:
      print(f'se ha producido una excepcion {e} en la url {url}')
  if (url, None, None) in g:
      found_checked = found_checked and True
  else:
      found_checked = found_checked and False
  if mach_read_checked:
    print('   Result: OK. The property is machine-readable. Weight assigned 20')
    weight = weight + 20
    mqa_machine_readable = mqa_machine_readable + 20
  else:
    print('   Result: ERROR. The property is not machine-readable')
  if non_prop_checked:
    print('   Result: OK. The property is non-propietary. Weight assigned 20')
    weight = weight + 20
    mqa_non_propietary = mqa_non_propietary + 20

  else:
    print('   Result: ERROR. The property is not non-propietary')
  if found_checked:
    result = True
  else:
    result = False
  return weight, mqa_format, mqa_non_propietary, mqa_machine_readable

def license(urls, weight, mqa_license, mqa_license_voc):
  checked = True
  weight = weight + 20
  mqa_license = mqa_license + 20
  print('   Result: OK. The property is set. Weight assigned 20')
  for url in urls:
    try:

      g = Graph()
      g.parse(url, format="application/rdf+xml")
    except Exception as e:
      print(f'Ha habido una excepcion del tipo {e} en {url}')
    if (url, None, None) in g:
      checked = checked and True      
    else:
      checked = checked and False
  if checked:
    weight = weight + 10
    mqa_license_voc = mqa_license_voc + 10
    print('   Result: OK. The property provides the correct license information. Weight assigned 10')
  else:
    print('   Result: ERROR. The license is incorrect -',str(url))
  return weight, mqa_license, mqa_license_voc

def contactpoint(weight, mqa_contact):
  weight = weight + 20
  mqa_contact = mqa_contact + 20
  print('   Result: OK. The property is set. Weight assigned 20')
  return weight, mqa_contact

def mediatype(urls, weight, mqa_media, mqa_media_voc):
  checked = True
  weight = weight + 10
  mqa_media = mqa_media + 10
  print('   Result: OK. The property is set. Weight assigned 10')
  try:
    for url in urls:
      res = requests.get(str(url))
      if res.status_code != 404:
        checked = checked and True
        mqa_media_voc = mqa_media_voc + 10
      else:
        checked = checked and False
  except Exception as e:
      print(f'se ha producido una excepcion {e} en la url {url}')
  if checked:
    result = True
  else:
    result = False
  return weight, mqa_media, mqa_media_voc

def publisher(weight, mqa_publisher):
  weight = weight + 10
  mqa_publisher = mqa_publisher + 10  
  print('   Result: OK. The property is set. Weight assigned 10')
  return weight, mqa_publisher

def accessrights(urls, weight, mqa_rights, mqa_rights_voc):
  uri = URIRef('')
  checked = True
  isURL = True
  weight = weight + 10
  mqa_rights = mqa_rights + 10
  print('   Result: OK. The property is set. Weight assigned 10')
  try:
    for url in urls:
        g = Graph()
        if type(url) != type(uri):
          isURL = False
          continue
        g.parse(url, format="application/rdf+xml")
        if (url, None, None) in g:
          checked = checked and True
        else:
          checked = checked and False
  except Exception as e:
      print(f'se ha producido una excepcion {e} en la url {url}')
  if isURL:
    if checked:
      weight = weight + 5
      mqa_rights_voc = mqa_rights_voc + 5
      print('   Result: OK. The property uses a controlled vocabulary. Weight assigned 5')
    else:
      print('   Result: ERROR. The license is incorrect -', str(url))
  else:
    print('   Result: ERROR. The property does not use a valid URL. No additional weight assigned')
  return weight, mqa_rights, mqa_rights_voc

def issued(weight, mqa_issued):
  weight = weight + 5
  mqa_issued = mqa_issued + 5
  print('   Result: OK. The property is set. Weight assigned 5')
  return weight, mqa_issued

def modified(weight, mqa_modified):
  weight = weight + 5
  mqa_modified = mqa_modified + 5
  print('   Result: OK. The property is set. Weight assigned 5')
  return weight, mqa_modified

def rights(weight, mqa_rights2):
  weight = weight + 5
  mqa_rights2 = mqa_rights2 + 5
  print('   Result: OK. The property is set. Weight assigned 5')
  return weight, mqa_rights2

def byteSize(weight, mqa_bytesize):
  weight = weight + 5
  mqa_bytesize = mqa_bytesize + 5
  print('   Result: OK. The property is set. Weight assigned 5')
  return weight, mqa_bytesize

#funciones comprobaciones MQA-EXTRA

def keyword_extra(objs, weight_extra, description, n_keywords, relation_keywords):      #Pruebas comprobacion string en keyword (nota_extra máxima = 30)
  nota_keywords = 0
  
  keywords = []
  valuable_words = []
  description_filtered = []

  for palabra in description:
    if is_valuable_word(palabra):
      description_filtered.append(palabra)
  
  #Guardamos todas las keywords en un array plano con solo strings
  flattened_keywords = flatten_list(objs)

  num_keywords = len(flattened_keywords)
  #Guardamos las keywords como string
  for word in flattened_keywords:
    word_str = word.n3()
    word_stripped = word_str.strip('"')
    keywords.append(word_stripped)


  #Test 1 -> Comprobar número de keywords (nota_extra máxima = 5)
  if num_keywords >=3:                        
    print('   Result: OK. The number of keywords is addecuate.  Weight_extra assigned = 10/10')
    nota_keywords = nota_keywords + 10
    n_keywords = n_keywords + 10
  if num_keywords == 2:
    print('   Result: ERROR. The number of keywords is low.  Weight_extra assigned = 5/10')
    nota_keywords = nota_keywords + 5
    n_keywords = n_keywords + 5
  else:                                        
    print('   Result: ERROR. The number of keywords is too low.  Weight_extra assigned = 0/10') 

#Test 5 -> Comprobar que las keywords introducidas tienen relación con el campo description (nota máxima = 20)

  if tiene_relacion_chatgpt_keywords(keywords, description_filtered):
    print('   Result: OK. The keywords are related to the description of the dataset.  Weight_extra assigned = 20/20')
    nota_keywords = nota_keywords + 20
    relation_keywords = relation_keywords + 20
  else:
    print('   Result: ERROR. The keywords are not related to the description of the dataset.  Weight_extra assigned = 0/20')

  weight_extra = weight_extra + nota_keywords
  print('   Current weight_extra: ', weight_extra)
  return weight_extra, n_keywords, relation_keywords



def downloadURL_extra(urls, bytesize, weight_extra, file_size):     #Pruebas comprobación del tamaño del archivo (nota_extra máxima = 10)
  
  checked = True
  #Establecemos un margen del 50% de error en el tamaño del archivo
  nota_bytesize = 0
  margin = bytesize * 0.5  
  #Realizamos una petición HTTP-HEAD para obtener el content-length del archivo a partir de la URL de descarga
  for url in urls:
    try:
      response = urllib.request.urlopen(url)
      res = response.info()
      content_length = float(res.get('Content-Length'))
      print (f'Este es content length ->{content_length} y bytesize ->{bytesize}')
      if content_length:
        if abs(bytesize - content_length) <= margin:
          nota_bytesize = nota_bytesize + 10
          file_size = file_size + 10
        else:
          checked = checked and False
          print('   Result: ERROR. The field bytesize does not correspond to the real size of the dataset.  Weight_extra assigned = 0/10')
    except:
      checked = checked and False   
  if checked:
    weight_extra = weight_extra + nota_bytesize
    print(f'   Result: OK. The field bytesize correspond to the real size of the dataset.  Weight_extra assigned = {nota_bytesize}/10')
    print('   Current weight_extra: ', weight_extra)
  else:
    print('   Result: ERROR - Responded status code of HTTP HEAD request is not in the 200 or 300 range')
    print('   Current weight_extra: ', weight_extra)  
  return weight_extra, file_size

def issued_extra(dates, weight_extra, standard_time, recent_time): #Prueba comprobación del estándar XMLSchemaDateTime (nota_extra máxima = 5)
  
  checked_format = False
  checked_recent = False

  for date in dates:
    date_str = str(date)
    if es_formato_datetime(date_str):
      checked = True
      objeto_datetime = dates[0].toPython()
      checked_recent = recent_date(objeto_datetime)
      checked_format = True

    

  
  if checked_format:
    weight_extra = weight_extra + 5
    standard_time = standard_time + 5
    print('   Result: OK. The date is in XMLSchema standard form.  Weight_extra assigned = 5/5')
    print('   Current weight_extra: ', weight_extra)
  else:
    print('   Result: ERROR. The date is not in XMLSchema standard form.  Weight_extra assigned = 0/5')
    print('   Current weight_extra: ', weight_extra)
  
  if checked_recent:
    weight_extra = weight_extra + 5
    recent_time = recent_time + 5
    print('   Result: OK. The dataset is less than 5 years old.  Weight_extra assigned = 5/5')
    print('   Current weight_extra: ', weight_extra)
  else:
    print('   Result: ERROR. The dataset is more than 5 years old.  Weight_extra assigned = 0/5')
    print('   Current weight_extra: ', weight_extra)


  return weight_extra, standard_time, recent_time


def theme_extra(urls, theme_voc, description, weight_extra, standard_theme, relation_theme):
  

  theme_checked = False
  themes = []
  
  for url in urls:
    if str(url) in theme_voc:
      theme_checked = True
      themes.append(url)
  
      

  theme_relation_checked = tiene_relacion_chatgpt_theme(themes, description)

  if theme_checked:
    weight_extra = weight_extra + 10
    standard_theme = standard_theme + 10
    print('   Result: OK. The theme is on the controlled edp vocabulary. Weight_extra assigned = 10/10')
    print('   Current weight_extra: ', weight_extra)
  else:
    print('   Result: ERROR. The theme does not belong to a controlled vocabulary. Weight_extra assigned = 0/10')
    print('   Current weight_extra: ', weight_extra)
  
  if theme_relation_checked:
    weight_extra = weight_extra + 10
    relation_theme = relation_theme + 10
    print('   Result: OK. The theme chosen is related to the description of the dataset. Weight_extra assigned = 10/10')
    print('   Current weight_extra: ', weight_extra)
  else:
    print('   Result: ERROR. The theme chosen is not related to the description of the dataset. Weight_extra assigned = 0/10')
    print('   Current weight_extra: ', weight_extra)

  return weight_extra, standard_theme, relation_theme
