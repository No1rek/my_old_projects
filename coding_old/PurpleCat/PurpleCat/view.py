from django.shortcuts import render
from PurpleCat.models import *
import re
import math

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def main(request, *args, **kwargs):
    recent = Post.objects.all().order_by('-date_published')[:3]
    most_liked = Post.objects.all().order_by('-likes')[:3]
    most_viewed = Post.objects.all().order_by('-views')[:3]
    # print(list([i.date_published for i in recent]))
    categories = Category.objects.all()

    return render(request, 'index.html', locals())
    # return render(request, 'index.html', {'recent': recent, 'most_liked': most_liked, 'most_popular': most_viewed})



def category_view(request, *args, **kwargs):
    POSTS_PER_PAGE = 9
    ALL_CATEGORIES_CAPTION = 'All categories'
    queries = {'recent': '-date_published', 'most-liked': '-likes', 'most-viewed': '-views'}

    categories = Category.objects.all()

    category = ''
    sort_by = ''
    page = 1
    category_link = ''

    if 'category' in kwargs:
        if kwargs['category'] in [cat.link for cat in categories]:
            category = kwargs['category']


    if 'sort_by' in kwargs :
        if kwargs['sort_by'] in ('recent', 'most-viewed', 'most-liked'):
            sort_by = queries[kwargs['sort_by']]
        else:
            sort_by = '-date_published'
    else:
        sort_by = '-date_published'
    if 'page' in kwargs:
        page = kwargs['page']

    if len(category) > 0:
        posts = Post.objects.filter(category__link=category).order_by(sort_by)
    else:
        posts = Post.objects.order_by(sort_by)

    if (page - 1) * POSTS_PER_PAGE > len(posts) or page < 1:
        page = 1

    max_page = math.ceil(len(posts) / POSTS_PER_PAGE)
    next_page =  min(page+1, max_page)
    previous_page = max(page-1, 1)


    articles = posts[(page - 1) * POSTS_PER_PAGE: page * POSTS_PER_PAGE]
    if category == '':
        category = ALL_CATEGORIES_CAPTION
    else:
        category_link = 'category-'+category+'/'
        category = categories.get(link=category).name


    for name, query in queries.items():
        if query == sort_by:
            sort_by = name
            sort_by_link = 's-'+sort_by+'/'
            break
    else:
        sort_by = 'recent'
        sort_by_link = 's-recent/'

    max_page = math.ceil(len(posts) / POSTS_PER_PAGE)
    HOST = 'http://'+request.META['HTTP_HOST']+'/'

    next_page = 'p'+str(min(page + 1, max_page))+'/'
    previous_page = 'p'+str(max(page - 1, 1))+'/'

    return render(request, 'category.html', locals())

def categories(request, *args, **kwargs):
    categories = Category.objects.all()
    return render(request, 'categories.html', locals())

def article(request, *args, **kwargs):
    article_id = kwargs['id']
    article = Post.objects.get(id=article_id)

    articles_to_suggest = 3
    additional_articles = Post.objects.filter(category__name=article.category.name).exclude(title=article.title).order_by('-date_published')[:articles_to_suggest]
    more_articles = (len(additional_articles)>0)

    categories = Category.objects.all()
    return render(request, 'story.html', locals())
