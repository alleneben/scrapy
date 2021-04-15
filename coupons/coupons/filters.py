    # coding=utf8
from bs4 import BeautifulSoup
import requests
import json
from itertools import compress 
import re
from w3lib.html import remove_tags, remove_tags_with_content

def getBrands():
    resp = requests.get('http://18.198.147.71:1337/brands')
    data = resp.json()
    brand = {(x["BrandNameEn"].upper(),x["BrandNameHe"]):x["id"] for x in data}
    return brand


def cleanString(htmlExtract):
    if htmlExtract is not None:
        if isinstance(htmlExtract, list):
            soups = [BeautifulSoup(str(he), 'lxml') for he in htmlExtract]
            [[s.extract() for s in soup('script',)] for soup in soups]
            [[s.extract() for s in soup('style',)] for soup in soups]
            [[s.extract() for s in soup('noscript',)] for soup in soups]
            return ''.join([''.join(c.findAll(text=True)) for c in soups]).strip()
        elif isinstance(htmlExtract, str):
            soup = BeautifulSoup(str(htmlExtract), 'lxml')
            [s.extract() for s in soup('script',)]
            [s.extract() for s in soup('style',)]
            [s.extract() for s in soup('noscript',)]
            return ''.join(soup.findAll(text=True)).strip()
    else:
        return ''


def filterBrands(title,brands):
    brand_values = list(brands.values())
    if title is not None:
        titlestr = title.upper()
        fBrand = ' '.join(list(filter(None,  re.split(r"[^A-Za-z]", title.strip()))))
        if (any((en in titlestr) or (he in titlestr) for (en,he) in brands)):
            t = [(en in titlestr) or (he in titlestr) for (en,he) in brands]
            indices_found = [i for i, x in enumerate(t) if x]
            brands_found = [brand_values[index] for index in indices_found]
            if (len(brands_found)==1):
                return brands_found[0]
    return ''


     