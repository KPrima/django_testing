import pytest
from django.conf import settings
from django.urls import reverse

from news.forms import CommentForm

pytestmark = pytest.mark.django_db


def test_comment_form_availability_for_anonymous_user(
    news_pk,
    client,
    admin_client
):
    url = reverse('news:detail', args=news_pk)
    response = client.get(url)
    admin_response = admin_client.get(url)
    assert (isinstance(admin_response.context['form'], CommentForm)
            and 'form' not in response.context)


@pytest.mark.usefixtures('set_of_news')
def test_news_count(client):
    url = reverse('news:home')
    response = client.get(url)
    news = response.context['object_list']
    news_count = news.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.usefixtures('set_of_news')
def test_news_order(client):
    url = reverse('news:home')
    response = client.get(url)
    news = response.context['object_list']
    sorted_list = sorted(
        news,
        key=lambda news: news.date,
        reverse=True
    )
    for current, expected in zip(news, sorted_list):
        assert current.date == expected.date


@pytest.mark.usefixtures('set_of_comments')
def test_comments_order(client, news_pk):
    url = reverse('news:detail', args=news_pk)
    response = client.get(url)
    comments = response.context['news'].comment_set.all()
    comments_sorted_list = sorted(
        comments,
        key=lambda comment: comment.created
    )
    for current, expected in zip(comments, comments_sorted_list):
        assert current.created == expected.created
