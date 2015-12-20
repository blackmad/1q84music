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
import json
import inflect

# TODO
# - handle when nothing change
# - make the tweets more interesting
# - maybe use the new song title if mutated for the image
# - make sure we have a big enough image

parser = argparse.ArgumentParser()
parser.add_argument('--dry_run', action='store_true')
parser.add_argument('--no_image', action='store_true')
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
  original_parts = [artist, title] 
  parts = mutate_and_pick_random(original_parts, mutate_string)
  return parts

def make_meme(string, top, bottom):
  bing = bing_search_api.BingSearchAPI(keys.bing_search_key)
  params = {'$format': 'json'}
  resp = bing.search('image', string,  params).json()

  resp = [r for r in resp if int(r['Height']) > 300 and int(r['Width'] > 400)]
  # print json.dumps(resp, sort_keys = True, indent = 2)
  url = resp['d']['results'][0]['Image'][0]['MediaUrl']

  response = requests.get(url)
  img = Image.open(StringIO(response.content))
  meme.draw_caption(img, top, top=True, padding=-3)
  meme.draw_caption(img, bottom, top=False, padding=20)

  #output = tempfile.mkstemp(suffix='.jpg')
  #img.save(output[1])
  #return output

  if args.dry_run:
    img.show()
  else:
    with io.BytesIO() as output:
      img.save(output, 'JPEG')
      return output.getvalue()

inflect_engine = inflect.engine()
class PostTemplate:
  def __init__(self, template, matcher=None):
    self.template = template
    self.matcher = matcher
 
  def matches(self, song):
    if self.matcher:
      return self.matcher(song)
    else:
      return True

  def format(self, song, chart):
    print self.template
    return self.template % {
      'title': song.title,
      'artist': song.artist,
      'rank': song.rank,
      'rank_ordinal': inflect_engine.ordinal(song.rank),
      'weeks': song.weeks,
      'weeks_ordinal': inflect_engine.ordinal(song.weeks),
      'chart': chart
   }


templates = [
  PostTemplate(
     'Congratulations to %(artist)s coming in on the %(chart)s at number %(rank)s with their hit %(title)s'
  ),
  PostTemplate(
     'Congratulations to %(artist)s debuting on the %(chart)s at %(rank)s with their hit %(title)s',
     lambda song: song.change == 'New'
  ),
  PostTemplate(
     '%(title)s by %(artist)s debuts on the %(chart)s chart this week',
     lambda song: song.change == 'New'
  ),
  PostTemplate(
     '%(title)s by %(artist)s has been on the %(chart)s for %(weeks)s',
     lambda song: song.weeks > 1
  ),
  PostTemplate(
     'For the %(weeks_ordinal)s week in a row, %(title)s by %(artist)s is the number %(rank)s song on the %(chart)s',
     lambda song: song.weeks > 1
  )
]

def make_post_text(song, chart_name):
  valid_templates = [t for t in templates if t.matches(song)]
  all_possible = [t.format(song, chart_name) for t in valid_templates] 

  if args.dry_run:
    for p in all_possible:
      print '(%s %s) - %s' % (len(p), len(p) < 120, p)

  return random.choice([p for p in all_possible if len(p) < 120])

def post_to_twitter(text, img_bytes):
  t = twitter.Twitter(auth = twitter.OAuth(
     keys.twitter_access_token, keys.twitter_access_token_secret,
     keys.twitter_consumer_key, keys.twitter_consumer_secret
  ))

  t_up = twitter.Twitter(domain = 'upload.twitter.com', auth = twitter.OAuth(
     keys.twitter_access_token, keys.twitter_access_token_secret,
     keys.twitter_consumer_key, keys.twitter_consumer_secret
  ))

  if img_bytes:
    id_img1 = t_up.media.upload(media=img_bytes)["media_id_string"]
  else:
    id_img1 = None
  response = t.statuses.update(status=text, media_ids=id_img1)
  print 'http://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id'])

def save_to_db(artist, title): 
  post = Post.create(artist = artist, title = title)
  
def process_song(song, chart_name):
  new_parts = mutate_song(song.artist, song.title)
  if not new_parts:
    return None
  
  (new_artist, new_title) = new_parts
  new_song = billboard.ChartEntry(
    title = new_title,
    artist = new_artist,
    peakPos = song.peakPos,
    lastPos = song.lastPos,
    weeks = song.weeks,
    rank = song.rank,
    change = song.change
  )
  
  orig = '%s - %s' % (song.artist, song.title)
  post = '%s - %s' % (new_artist, new_title)
  print '%s -->' % orig
  print '--> %s' % post
  if args.no_image:
    img_bytes = None
  else:
    img_bytes = make_meme(orig, post, '')
  post = make_post_text(new_song, chart_name)
  if not args.dry_run:
    post_to_twitter(post, image_bytes)
    save_to_db(song.artist, song.title)

def filter_chart(chart):
  def in_db(song):
    return Post.select().where(
      (Post.artist == song.artist) &
      (Post.title == song.title)
    ).count() > 0

  return [ song for song in chart if not in_db(song) ]

def process_chart(chart_id, chart_name):
  chart = billboard.ChartData(chart_id)
  chart = filter_chart(chart)
  process_song(random.choice(chart), chart_name)

def main():
  sqlite_db.connect()
  Post.create_table(fail_silently = True)
  process_chart('hot-100', 'Hot 100')

if __name__ == "__main__":
  # execute only if run as a script
  main()
