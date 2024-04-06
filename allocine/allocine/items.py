# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FilmItem(scrapy.Item):
    film_id = scrapy.Field()
    title = scrapy.Field()
    img_src = scrapy.Field()
    release = scrapy.Field()
    duration = scrapy.Field()
    genres = scrapy.Field()
    synopsis = scrapy.Field()
    nationality = scrapy.Field()
    budget = scrapy.Field()
    director = scrapy.Field()
    casting = scrapy.Field()
    societies = scrapy.Field()
    entries = scrapy.Field()


class BoxOfficeItem(scrapy.Item):
    film_id = scrapy.Field()
    entries = scrapy.Field()
