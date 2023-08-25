from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestDetailPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.other_user = User.objects.create(username='Другой пользователь')
        cls.notes = Note.objects.create(
            title='Заголовок заметки',
            text='Текст заметки',
            slug='1',
            author=cls.author
        )

    def test_notes_list(self):
        notes_list = (
            (self.author, True),
            (self.other_user, False),
        )
        url = reverse('notes:list')
        for user, notes in notes_list:
            self.client.force_login(user)
            with self.subTest(user=user.username, notes=notes):
                response = self.client.get(url)
                note_object = self.notes in response.context[
                    'object_list'
                ]
                self.assertEqual(note_object, notes)

    def test_form_submission_add_edit(self):
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.notes.slug)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                self.client.force_login(self.author)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(
                    self.client.get(url).context['form'],
                    NoteForm
                )
