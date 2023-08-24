from http import HTTPStatus
from random import choice

import pytest
from django.urls import reverse
from pytest_django.asserts import assertFormError, assertRedirects

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


pytestmark = pytest.mark.django_db


def test_create_comment_with_a_bad_word(admin_client, news_pk):
    bad_words_data = {
        'text':
        f'Текст комментария, в котором есть плохое слово: {choice(BAD_WORDS)}'
    }
    url = reverse('news:detail', args=news_pk)
    response = admin_client.post(url, data=bad_words_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    assert Comment.objects.count() == 0


def test_user_can_create_comment(admin_client, admin_user, form_data, news):
    url = reverse('news:detail', args=[news.pk])
    response = admin_client.post(url, data=form_data)
    assertRedirects(response, url + '#comments')
    assert Comment.objects.count() == 1
    new_comment = Comment.objects.get()
    assert new_comment.author == admin_user
    assert new_comment.text == form_data['text']
    assert new_comment.news == news


def test_anonymous_user_cant_create_comment(client, form_data, news):
    url = reverse('news:detail', args=[news.pk])
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    assertRedirects(response, f'{login_url}?next={url}')
    assert Comment.objects.count() == 0


def test_author_can_edit_comment(
        author_client,
        form_data,
        news_pk,
        comment,
        news):
    url = reverse('news:edit', args=[comment.pk])
    response = author_client.post(url, form_data)
    assertRedirects(response, reverse(
        'news:detail',
        args=news_pk
    ) + '#comments')
    comment.refresh_from_db()
    assert comment.author == comment.author
    assert comment.text == form_data['text']
    assert comment.news == news


def test_other_user_cant_edit_comment(
        admin_client,
        form_data,
        comment,
        news
):
    url = reverse('news:edit', args=[comment.pk])
    response = admin_client.post(url, form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.author == comment.author
    assert comment.text == comment_from_db.text
    assert comment.news == news


def test_author_can_delete_comment(author_client, comment, news_pk):
    url = reverse('news:delete', args=[comment.pk])
    response = author_client.post(url)
    assertRedirects(response, reverse(
        'news:detail',
        args=news_pk
    ) + '#comments')
    assert Comment.objects.count() == 0


def test_other_user_cant_delete_comment(
        admin_client,
        comment
):
    url = reverse('news:delete', args=[comment.pk])
    response = admin_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1
