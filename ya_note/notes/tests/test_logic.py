from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.form_data = {'title': 'Заголовок заметки',
                         'text': 'Текст заметки',
                         'slug': 'abcd'}
        cls.ADD_URL = reverse('notes:add')

    def test_anonymous_user_cant_create_note(self):
        response = self.client.post(self.ADD_URL, data=self.form_data)
        login_url = reverse('users:login')
        redirect_url = f'{login_url}?next={self.ADD_URL}'
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_can_create_note(self):
        self.client.force_login(self.author)
        response = self.client.post(self.ADD_URL, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get(slug='abcd')
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.author)

    def test_slug_must_be_unique(self):
        self.client.force_login(self.author)
        self.client.post(self.ADD_URL, data=self.form_data)
        response = self.client.post(self.ADD_URL, data=self.form_data)
        warning_message = self.form_data['slug'] + WARNING
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=warning_message
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        self.client.force_login(self.author)
        del self.form_data['slug']
        response = self.client.post(self.ADD_URL, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get(slug='zagolovok-zametki')
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    TITLE = 'Заголовок заметки'
    TEXT = 'Текст заметки'
    NEW_TITLE = 'Новый заголовок заметки'
    NEW_TEXT = 'Новый текст заметки'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.other_user = User.objects.create(username='Другой пользователь')
        cls.other_user_client = Client()
        cls.other_user_client.force_login(cls.other_user)
        cls.notes = Note.objects.create(
            title=cls.TITLE,
            text=cls.TEXT,
            slug='1',
            author=cls.author
        )
        cls.edit_url = reverse('notes:edit', args=[cls.notes.slug])
        cls.delete_url = reverse('notes:delete', args=[cls.notes.slug])
        cls.form_data = {'title': cls.NEW_TITLE,
                         'text': cls.NEW_TEXT}

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.other_user_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.text, self.NEW_TEXT)
        self.assertEqual(self.notes.title, self.NEW_TITLE)
        self.assertEqual(self.notes.slug, 'novyij-zagolovok-zametki')
        self.assertEqual(self.notes.author, self.author)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.other_user_client.post(
            self.edit_url,
            data=self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.notes.id)
        self.assertEqual(self.notes.text, note_from_db.text)
        self.assertEqual(self.notes.title, note_from_db.title)
        self.assertEqual(self.notes.slug, note_from_db.slug)
        self.assertEqual(self.notes.author, note_from_db.author)
