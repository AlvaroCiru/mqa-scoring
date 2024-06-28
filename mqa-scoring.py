#!/usr/bin/env python3
'''
YODA (Your Open DAta)
EU CEF Action 2019-ES-IA-0121
University of Cantabria
Developer: Johnny Choque (jchoque@tlmat.unican.es)
'''

import requests
import urllib.request
import json
from rdflib import Graph, Literal, URIRef, Namespace
import argparse
import mqaMetrics as mqa
import os
from datetime import datetime
import pytz

FOAF = "http://xmlns.com/foaf/0.1/"
DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
URL_EDP = 'https://data.europa.eu/api/mqa/shacl/validation/report'
HEADERS = {'content-type': 'application/rdf+xml'}
MACH_READ_FILE = os.path.join('edp-vocabularies', 'edp-machine-readable-format.rdf')
NON_PROP_FILE = os.path.join('edp-vocabularies', 'edp-non-proprietary-format.rdf')
THEME_FILE = os.path.join('edp-vocabularies', 'edp-data-theme-skos.rdf')

def otherCases(pred, objs, g):
  for obj in objs:
    met = str_metric(obj, g)
    if met == None:
      print('   Result: WARN. Not included in MQA - '+ str_metric(pred, g))
    else:
      print('   Result: WARN. Not included in MQA - '+ str(met))

def str_metric(val, g):
  valStr=str(val)
  for prefix, ns in g.namespaces():
    if val.find(ns) != -1:
      metStr = valStr.replace(ns,prefix+":")
      return metStr

def load_edp_vocabulary(file):
  g = Graph()
  g.parse(file, format="application/rdf+xml")
  voc = []
  for sub, pred, obj in g:
    voc.append(str(sub))
  return voc

def edp_validator(file, weight, mqa_shacl):
  print('* SHACL validation')
  try:
    rdfFile = open(file, "r", encoding="utf-8")
  except Exception as e:
    raise SystemExit(e)
  with rdfFile:
    try:
      payload = rdfFile.read().replace("\n", " ")
      r_edp = requests.post(URL_EDP, data=payload.encode('utf-8'), headers=HEADERS)
      r_edp.raise_for_status()
    except requests.exceptions.HTTPError as err:
      raise SystemExit(err)
    report = json.loads(r_edp.text)
    if valResult(report):
      print('   Result: OK. The metadata has successfully passed the EDP validator. Weight assigned 30')
      weight = weight + 30
      mqa_shacl = mqa_shacl + 30
    else:
      print('   Result: ERROR. DCAT-AP errors found in metadata')
  return weight, mqa_shacl

def valResult(d):
  if 'sh:conforms' in d:
    return d['sh:conforms']
  for k in d:
    if isinstance(d[k], list):
      for i in d[k]:
        if 'sh:conforms' in i:
          return i['sh:conforms']


def get_metrics(g):
  metrics = {}
  for sub, pred, obj in g:
    if pred not in metrics.keys():
      metrics[pred] = None
  for pred in metrics.keys():
    obj_list=[]
    for obj in g.objects(predicate=pred):
      obj_list.append(obj)
    metrics[pred] = obj_list
  return metrics

#Comprobación de inicio y fin del dataset
def temporal_range(g, weight_extra, temp_recent):
  
  start_date = None
  end_date = None
  #Obtener fecha de inicio y fin del archivo
  for s, p, o in g.triples((None, DCAT.startDate, None)):
    start_date = o.toPython()  # Convertir a tipo de dato Python
    if start_date.tzinfo is None:
      start_date = start_date.replace(tzinfo=pytz.utc)
    else:
      start_date = start_date.astimezone(pytz.utc)

  for s, p, o in g.triples((None, DCAT.endDate, None)):
    end_date = o.toPython()  # Convertir a tipo de dato Python
    if end_date.tzinfo is None:
      end_date = end_date.replace(tzinfo=pytz.utc)
    else:
      end_date = end_date.astimezone(pytz.utc) 
  
  # Obtener la fecha y hora actual en UTC
  current_date = datetime.now(pytz.utc)

  if start_date and end_date:  # Ambas fechas están presentes
      if start_date <= current_date <= end_date:
          weight_extra = weight_extra + 5
          temp_recent = temp_recent + 5
          print('   Result: OK. The Dataset is on the time-range established. Weight_extra assigned = 5/5')
          print('   Current weight_extra: ', weight_extra)
  elif start_date and not end_date:  # Solo hay fecha de inicio
      if start_date <= current_date:
          weight_extra = weight_extra + 5
          temp_recent = temp_recent + 5
          print('   Result: OK. The Dataset is on the time-range established. Weight_extra assigned = 5/5')
          print('   Current weight_extra: ', weight_extra)
  elif end_date and not start_date:  # Solo hay fecha de fin
      if current_date <= end_date:
          weight_extra = weight_extra + 5
          temp_recent = temp_recent + 5
          print('   Result: OK. The Dataset is on the time-range established. Weight_extra assigned = 5/5')
          print('   Current weight_extra: ', weight_extra)      
  else:
      print('   Result: ERROR. The Dataset is not on the time-range established. Weight_extra assigned = 0/5')
      print('   Current weight_extra: ', weight_extra)
  return weight_extra, temp_recent

def main():
  mach_read_voc = []
  non_prop_voc = []

  parser = argparse.ArgumentParser(description='Calculates the score obtained by a metadata according to the MQA methodology specified by data.europa.eu')
  parser.add_argument('-f', '--file', type=str, required=True, help='RDF file to be validated')
  args = parser.parse_args()

  g = Graph()
  g.parse(args.file, format="application/rdf+xml")

  mach_read_voc = load_edp_vocabulary(MACH_READ_FILE)
  non_prop_voc = load_edp_vocabulary(NON_PROP_FILE)

  weight = 0
  weight = 0
  description = ""
  bytesize = 0
  mqa_keyword = 0
  mqa_theme = 0
  mqa_spatial = 0
  mqa_temporal = 0
  mqa_access = 0
  mqa_download = 0
  mqa_download_access = 0
  mqa_format = 0
  mqa_media = 0
  mqa_media_voc = 0
  mqa_non_propietary = 0
  mqa_machine_readable = 0
  mqa_shacl = 0
  mqa_license = 0
  mqa_license_voc = 0
  mqa_rights = 0
  mqa_rights_voc = 0
  mqa_contact = 0
  mqa_publisher = 0
  mqa_rights2 = 0
  mqa_bytesize = 0
  mqa_issued = 0
  mqa_modified = 0
  keywords = []
  weight, mqa_shacl = edp_validator(args.file, weight, mqa_shacl)
  print('   Current weight =',weight)

  metrics = get_metrics(g)
  f_res = {}
  f_res = f_res.fromkeys(['result', 'url', 'weight'])
  m_res = {}
  m_res = m_res.fromkeys(['result', 'weight'])

  # Puntuación MQA
  for pred in metrics.keys():
    met = str_metric(pred, g)
    objs = metrics[pred]
    print('*',met)

    if met == "dcat:accessURL":
      weight, mqa_access = mqa.accessURL(objs, weight, mqa_access)
    elif met == "dcat:downloadURL":
      weight, mqa_download, mqa_download_access = mqa.downloadURL(objs, weight, mqa_download, mqa_download_access)
    elif met == "dct:description":
      description = objs
    elif met == "dcat:keyword":
      weight, mqa_keyword = mqa.keyword(weight, mqa_keyword)
      keywords.append(objs)
    elif met == "dcat:theme":
      weight, mqa_theme = mqa.theme(weight, mqa_theme)
    elif met == "dct:spatial":
      weight, mqa_spatial = mqa.spatial(weight, mqa_spatial)
    elif met == "dct:temporal":
      weight, mqa_temporal = mqa.temporal(weight, mqa_temporal)
    elif met == "dct:format":
      weight, mqa_non_propietary, mqa_machine_readable, mqa_format = mqa.format(objs, mach_read_voc, non_prop_voc, weight, mqa_format, mqa_non_propietary, mqa_machine_readable)
    elif met == "dct:license":
      weight, mqa_license, mqa_license_voc = mqa.license(objs, weight,mqa_license, mqa_license_voc)
    elif met == "dcat:contactPoint":
      weight, mqa_contact = mqa.contactpoint(weight, mqa_contact)
    elif met == "dcat:mediaType":
      weight, mqa_media, mqa_media_voc = mqa.mediatype(objs, weight, mqa_media, mqa_media_voc)
    elif met == "dct:publisher":
      weight, mqa_publisher = mqa.publisher(weight, mqa_publisher)
    elif met == "dct:accessRights":
      weight, mqa_rights, mqa_rights_voc = mqa.accessrights(objs, weight, mqa_rights, mqa_rights_voc)
    elif met == "dct:issued":
      weight, mqa_issued = mqa.issued(weight, mqa_issued)
    elif met == "dct:modified":
      weight, mqa_modified = mqa.modified(weight, mqa_modified)
    elif met == "dct:rights":
      weight, mqa_rights2 = mqa.rights(weight, mqa_rights2)
    elif met == "dcat:byteSize":
      weight, mqa_bytesize = mqa.byteSize(weight, mqa_bytesize)
      bytesize = float(objs[0])
    else:
      otherCases(pred, objs, g)
    print('   Current weight =',weight)

  print('* dct:format & dcat:mediaType')
  if f_res['result'] and m_res['result']:
    weight = weight + 10
    print('   Result: OK. The properties belong to a controlled vocabulary. Weight assigned 10')
    print('   Current weight=',weight)
  else:
    print('   Result: WARN. The properties do not belong to a controlled vocabulary')



  #Puntuación MQA-EXTRA
  print('MQA_Extra evaluation of critical fields:')
  theme_voc = load_edp_vocabulary(THEME_FILE)
  weight_extra = 0
  n_keywords = 0
  relation_keywords = 0
  file_size = 0
  standard_time = 0
  recent_time = 0
  standard_theme = 0
  relation_theme = 0
  temp_recent = 0
  for pred in metrics.keys():
    met = str_metric(pred, g)
    objs = metrics[pred]
    

    if met == "dcat:keyword" and description != "":
      print('*',met)
      print(objs)
      weight_extra, n_keywords, relation_keywords = mqa.keyword_extra(keywords, weight_extra, description, n_keywords, relation_keywords)
    elif met == "dcat:downloadURL" and bytesize != 0:
      print('*',met)
      weight_extra, file_size = mqa.downloadURL_extra(objs, bytesize, weight_extra, file_size)
    elif met == "dct:issued":
      print('*',met)
      weight_extra, standard_time, recent_time = mqa.issued_extra(objs, weight_extra, standard_time, recent_time)
    elif met == "dct:temporal":
      print('*',met)
      weight_extra, temp_recent = temporal_range(g, weight_extra, temp_recent)
    elif met == "dcat:theme":
      print('*',met)
      weight_extra, standard_theme, relation_theme = mqa.theme_extra(objs, theme_voc, description,  weight_extra, standard_theme, relation_theme)

  
  
  print('\n')
  print('Overall MQA scoring:', str(weight))
  print('Overall MQA-enhanced scoring:', str(weight_extra))

  return weight, weight_extra

if __name__ == "__main__":
  main()
