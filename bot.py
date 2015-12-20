#!/usr/bin/python

import datetime
import twitter
import keys
import tempfile
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
import peewee
import argparse

# TODO
# - make the tweets more interesting

parser = argparse.ArgumentParser()
parser.add_argument('--dry_run', action='store_true')
args = parser.parse_args()

sqlite_db = peewee.SqliteDatabase('1q84_posts.db')

class BaseModel(peewee.Model):
    class Meta:
        database = sqlite_db

class Post(BaseModel):
    id = peewee.IntegerField(unique=True,primary_key=True)
    artist = peewee.CharField()
    title = peewee.CharField()
    pub_date = peewee.DateTimeField(default=datetime.datetime.now)

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
  str = '%s - %s' % (artist, title)
  new_str = mutate_string(str)
  return new_str

def make_meme(string, top, bottom):
  bing = bing_search_api.BingSearchAPI(keys.bing_search_key)
  params = {'$format': 'json'}
  resp = bing.search('image', string,  params).json()
  url = resp['d']['results'][0]['Image'][0]['MediaUrl']

  response = requests.get(url)
  img = Image.open(StringIO(response.content))
  meme.draw_caption(img, top, bottom)

  #output = tempfile.mkstemp(suffix='.jpg')
  #img.save(output[1])
  #return output

  if args.dry_run:
    img.show()
  else:
    with io.BytesIO() as output:
      img.save(output, 'JPEG')
      return output.getvalue()

def post_to_twitter(text, img_bytes):
  t = twitter.Twitter(auth = twitter.OAuth(
     keys.twitter_access_token, keys.twitter_access_token_secret,
     keys.twitter_consumer_key, keys.twitter_consumer_secret
  ))

  t_up = twitter.Twitter(domain = 'upload.twitter.com', auth = twitter.OAuth(
     keys.twitter_access_token, keys.twitter_access_token_secret,
     keys.twitter_consumer_key, keys.twitter_consumer_secret
  ))

  id_img1 = t_up.media.upload(media=img_bytes)["media_id_string"]
  response = t.statuses.update(status=text, media_ids=id_img1)
  print 'http://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id'])


def save_to_db(artist, title): 
  post = Post.create(artist = artist, title = title)
  
def process_song(song):
  # song.title song.artist
  post = mutate_song(song.artist, song.title)
  orig = '%s - %s' % (song.artist, song.title)
  print 'making %s into' % orig
  print post
  image_file = make_meme(orig, post, '')
  if not args.dry_run:
    post_to_twitter(post, image_file)
    save_to_db(song.artist, song.title)

def filter_chart(chart):
  def in_db(song):
    return Post.select().where(
      (Post.artist == song.artist) &
      (Post.title == song.title)
    ).count() > 0

  return [ song for song in chart if not in_db(song) ]

def process_chart(chart_name):
  chart = billboard.ChartData(chart_name)
  chart = filter_chart(chart)
  process_song(random.choice(chart))

def main():
  sqlite_db.connect()
  Post.create_table(fail_silently = True)
  process_chart('hot-100')

if __name__ == "__main__":
  # execute only if run as a script
  main()
