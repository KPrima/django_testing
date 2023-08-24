import pytest
from django.urls import reverse
from django.conf import settings

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'username, is_available',
    (
        (pytest.lazy_fixture('admin_client'), True),
        (pytest.lazy_fixture('client'), False)
    )
)
def test_comment_form_availability_for_anonymous_user(
    news_pk,
    username,
    is_available
):
    url = reverse('news:detail', args=news_pk)
    response = username.get(url)
    result = 'form' in response.context
    assert result == is_available


@pytest.mark.usefixtures('set_of_news')
def test_news_count(client):
    url = reverse('news:home')
    response = client.get(url)
    news = response.context['object_list']
    news_count = len(news)
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
