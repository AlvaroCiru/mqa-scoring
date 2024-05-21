'''
YODA (Your Open DAta)
EU CEF Action 2019-ES-IA-0121
University of Cantabria
Developer: Johnny Choque (jchoque@tlmat.unican.es)
'''
from wordhoard import Synonyms, Hypernyms, Hyponyms
import re
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
import requests
import re
from rdflib import Graph, URIRef
import urllib.request
from openai import OpenAI
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn
from nltk.corpus.reader import NOUN
from nltk.tag import pos_tag


#Funciones auxiliares 


def tiene_relacion_chatgpt(keywords, description):
  client = OpenAI()
  entrada = "Keywords: " + ". " .join(keywords) + "\nText: " + ". ".join(description)
  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "Eres un asistente para publicadores de datasets en portales de datos abiertos.Vas a recibir dos inputs de texto. Un array de palabras clave keywords describiendo el dataset, y un pequeño texto description en el que se describe la información del dataset.Tu misión es determinar si el conjunto de keywords está bien escogido, basado en si la mayoria de keywords tienen relación con la descripción del dataset, basandote en el significado de las palabras y su contexto.Los inputs de texto y palabras será en ingles, y tu respuesta también.Tu misión también será proporcionar palabras clave que podrían ser útiles para describir el dataset.Tu respuesta será del tipo: Yes/no, the keywords are/are not related with the description given because... y despues sugerir palabras clave que describan mejor el dataset. La decisión de responder Yes se basará en si las keywords tienen relación con la descripción"},
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
    
    # Expresión regular para verificar el formato dateTime    
    patron = r'^-?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|([-+]\d{2}:\d{2}))?$'
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

    # Validación de la hora
    try:
        hour, minute, second = map(int, cadena[11:19].split(':'))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59 or second < 0 or second > 59:
            checked = checked and False
    except ValueError:
        checked = checked and False

    # Validación de la zona horaria
    if len(cadena) > 19 and cadena[19] != 'Z':
        try:
            tz_hour, tz_minute = map(int, cadena[20:].split(':'))
            if tz_hour < -12 or tz_hour > 14 or tz_minute < 0 or tz_minute > 59:
                checked = checked and False
        except ValueError:
            checked = checked and False
    

    return bool(re.match(patron, cadena))

    
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

#Comprobaciones mqa-scoring
def accessURL(urls, weight):
  checked = True
  for url in urls:
    try:
      res = requests.get(url)
      if res.status_code in range(200, 399):
        checked = checked and True
      else:
        checked = checked and False
    except:
      checked = checked and False
  if checked:
    weight = weight + 50
    print('   Result: OK. Weight assigned 50')
  else:
    print('   Result: ERROR - Responded status code of HTTP HEAD request is not in the 200 or 300 range')
  return weight

def downloadURL(urls, weight):
  checked = True
  print('   Result: OK. The property is set. Weight assigned 20')
  weight = weight + 20
  for url in urls:
    try:
      res = requests.get(url)
      if res.status_code in range(200, 399):
        checked = checked and True
      else:
        checked = checked and False
    except:
      checked = checked and False
  if checked:
    weight = weight + 30
    print('   Result: OK. Weight assigned 30')
  else:
    print('   Result: ERROR - Responded status code of HTTP HEAD request is not in the 200 or 300 range')
  return weight

def description(description, weight):
  print("Esto es el campo description ------------------->", description)
  print('   Result: OK. The property is set. Weight assigned 30')
  return weight    

def keyword(weight,):
  weight = weight + 30
  print('   Result: OK. The property is set. Weight assigned 30')
  return weight

def theme(weight):
  weight = weight + 30
  print('   Result: OK. The property is set. Weight assigned 30')
  return weight

def spatial(weight):
  weight = weight + 20
  print('   Result: OK. The property is set. Weight assigned 20')
  return weight

def temporal(weight):
  weight = weight + 20
  print('   Result: OK. The property is set. Weight assigned 20')
  return weight

def format(urls, mach_read_voc, non_prop_voc, weight):
  mach_read_checked = True
  non_prop_checked = True
  found_checked = True
  print('   Result: OK. The property is set. Weight assigned 20')
  weight = weight + 20
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
    if (url, None, None) in g:
      found_checked = found_checked and True
    else:
      found_checked = found_checked and False
  if mach_read_checked:
    print('   Result: OK. The property is machine-readable. Weight assigned 20')
    weight = weight + 20
  else:
    print('   Result: ERROR. The property is not machine-readable')
  if non_prop_checked:
    print('   Result: OK. The property is non-propietary. Weight assigned 20')
    weight = weight + 20
  else:
    print('   Result: ERROR. The property is not non-propietary')
  if found_checked:
    result = True
  else:
    result = False
  return {'result': result, 'url':str(url), 'weight': weight}

def license(urls, weight):
  checked = True
  weight = weight + 20
  print('   Result: OK. The property is set. Weight assigned 20')
  for url in urls:
    g = Graph()
    g.parse(url, format="application/rdf+xml")
    if (url, None, None) in g:
      checked = checked and True
    else:
      checked = checked and False
  if checked:
    weight = weight + 10
    print('   Result: OK. The property provides the correct license information. Weight assigned 10')
  else:
    print('   Result: ERROR. The license is incorrect -',str(url))
  return weight

def contactpoint(weight):
  weight = weight + 20
  print('   Result: OK. The property is set. Weight assigned 20')
  return weight

def mediatype(urls, weight):
  checked = True
  weight = weight + 10
  print('   Result: OK. The property is set. Weight assigned 10')
  for url in urls:
    res = requests.get(str(url))
    if res.status_code != 404:
      checked = checked and True
    else:
      checked = checked and False
  if checked:
    result = True
  else:
    result = False
  return {'result': result, 'weight': weight}

def publisher(weight):
  weight = weight + 10
  print('   Result: OK. The property is set. Weight assigned 10')
  return weight

def accessrights(urls, weight):
  uri = URIRef('')
  checked = True
  isURL = True
  weight = weight + 10
  print('   Result: OK. The property is set. Weight assigned 10')
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
  if isURL:
    if checked:
      weight = weight + 5
      print('   Result: OK. The property uses a controlled vocabulary. Weight assigned 5')
    else:
      print('   Result: ERROR. The license is incorrect -', str(url))
  else:
    print('   Result: ERROR. The property does not use a valid URL. No additional weight assigned')
  return weight

def issued(weight):
  weight = weight + 5
  print('   Result: OK. The property is set. Weight assigned 5')
  return weight

def modified(weight):
  weight = weight + 5
  print('   Result: OK. The property is set. Weight assigned 5')
  return weight

def rights(weight):
  weight = weight + 5
  print('   Result: OK. The property is set. Weight assigned 5')
  return weight

def byteSize(weight):
  weight = weight + 5
  print('   Result: OK. The property is set. Weight assigned 5')
  return weight

#funciones comprobaciones MQA-EXTRA

def keyword_extra(objs, weight_extra, description):      #Pruebas comprobacion string en keyword (nota_extra máxima = 30)
  nota_keywords = 0
  num_keywords = len(objs)
  keywords = []
  valuable_words = []
  
  #Guardamos las keywords como string
  for word in objs:
    word_str = word.n3()
    word_stripped = word_str.strip('"')
    keywords.append(word_stripped)


  #Test 1 -> Comprobar número de keywords (nota_extra máxima = 5)
  if num_keywords >=3:                        
    print('   Result: OK. The number of keywords is addecuate.  Weight_extra assigned = 5/5')
    nota_keywords = nota_keywords + 5
  else:                                        
    print('   Result: ERROR. The number of keywords is too low.  Weight_extra assigned = 0/5')

  #Test 2 -> Comprobar que las keywords son palabras con sentido y valor suficiente (nota_extra máxima = 5)
  for keyword in keywords:
    if not is_word(keyword):
      keywords.remove(keyword)
    elif is_valuable_word(keyword):
      valuable_words.append(keyword) 

  if len(valuable_words) >= num_keywords:
    print('   Result: OK. All keywords are valuable words for describing a text.  Weight_extra assigned = 5/5')
    nota_keywords = nota_keywords + 5
  elif valuable_words:
    print('   Result: ERROR. Some of the keywords do not describe well a dataset.  Weight_extra assigned = 0/5')

  #Test 4 -> Comprobar que las keywords introducidas tienen relacion entre sí (nota máxima = 10)
    
  if relacion_keywords(keywords):
    print('   Result: OK. The keywords are related in meaning to each other.  Weight_extra assigned = 10/10')
    nota_keywords = nota_keywords + 10
  else:
    print('   Result: ERROR. The keywords are not related in meaning to each other.  Weight_extra assigned = 0/10')

  

#Test 5 -> Comprobar que las keywords introducidas tienen relación con el campo description (nota máxima = 10)

  if tiene_relacion_chatgpt(keywords, description):
    print('   Result: OK. The keywords are related to the description of the dataset.  Weight_extra assigned = 10/10')
    nota_keywords = nota_keywords + 10
  else:
    print('   Result: ERROR. The keywords are not related to the description of the dataset.  Weight_extra assigned = 0/10')

  weight_extra = weight_extra + nota_keywords
  print('   Current weight_extra: ', weight_extra)
  return weight_extra



def downloadURL_extra(urls, bytesize, weight_extra):     #Pruebas comprobación del tamaño del archivo (nota_extra máxima = 10)
  
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
      if content_length:
        if abs(bytesize - content_length) <= margin:
          nota_bytesize = nota_bytesize + 10
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
  return weight_extra

def issued_extra(dates, weight_extra): #Prueba comprobación del estándar XMLSchemaDateTime (nota_extra máxima = 5)
  
  checked = True
  
  for date in dates:
    date_str = str(date)
    checked = checked and es_formato_datetime(date_str)

  if checked:
    weight_extra = weight_extra + 5
    print('   Result: OK. The date is in XMLSchema standard form.  Weight_extra assigned = 5/5')
    print('   Current weight_extra: ', weight_extra)
  else:
    print('   Result: ERROR. The date is not in XMLSchema standard form.  Weight_extra assigned = 0/5')
    print('   Current weight_extra: ', weight_extra)


  return weight_extra


def theme_extra(urls, theme_voc, weight_extra):
  
  theme_checked = True
  found_checked = True
  
  for url in urls:
    if str(url) in theme_voc:
      theme_checked = theme_checked and True
    else:
      theme_checked = theme_checked and False
    g = Graph()
    g.parse(url, format="application/rdf+xml")
    if (url, None, None) in g:
      found_checked = found_checked and True
    else:
      found_checked = found_checked and False

  if theme_checked:
    weight_extra = weight_extra + 10
    print('   Result: OK. The theme is on the controlled edp vocabulary. Weight_extra assigned = 10/10')
    print('   Current weight_extra: ', weight_extra)
  else:
    print('   Result: ERROR. The theme does not belong to a controlled vocabulary. Weight_extra assigned = 0/10')
    print('   Current weight_extra: ', weight_extra)

  return weight_extra
