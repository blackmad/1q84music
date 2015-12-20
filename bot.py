#!/usr/bin/python

import pronouncing
from billboard_charts import billboard
import random
from PIL import Image
import string
import gimage
import io
import meme
from pyBingSearchAPI import bing_search_api
import requests
from StringIO import StringIO

def mutate_and_pick_random(parts, mutate_func):
  print 'working on %s' % parts
  alts = [None] * len(parts)

  # rhyme each word
  alts = [mutate_func(part) for part in parts]
  print 'have alts: %s' % parts

  # find the indexes of all the rhymes
  rhymed_indexes = [i for i, v in enumerate(alts) if v]

  if not rhymed_indexes:
    return None
  else:
    # pick a random index
    index = random.choice(rhymed_indexes)
    parts[index] = alts[index]
    return parts

def mutate_string(string):
  parts = string.split(' ')

  def mutate_func(s):
    s = s.lower()
    rhymes = pronouncing.rhymes(s)
    if rhymes:
      return random.choice(rhymes).title()
    else:
      return None

  parts = mutate_and_pick_random(parts, mutate_func)

  if parts:
     return ' '.join(parts)
  else:
    return None
  
  
def mutate_song(artist, title):
  parts = [artist, title]
  parts = mutate_and_pick_random(parts, mutate_string)
  if not parts:
    return None
  else:
    return ' - '.join(parts)

def make_meme(string, top, bottom):
  bing = bing_search_api.BingSearchAPI("kT9eK8B2MnrPK3anGH6oGle0QFawwvU+nnGEKqTU+s0")
  params = {'$format': 'json'}
  resp = bing.search('image', string,  params).json()
  url = resp['d']['results'][0]['Image'][0]['MediaUrl']

  response = requests.get(url)
  img = Image.open(StringIO(response.content))
  meme.draw_caption(img, top, bottom)
  img.show()

def main():
  chart = billboard.ChartData('hot-100')
  for song in chart[0:2]:
    # song.title song.artist
    post = mutate_song(song.artist, song.title)
    orig = '%s - %s' % (song.artist, song.title)
    print post
    make_meme(orig, post, '')

if __name__ == "__main__":
  # execute only if run as a script
  main()
