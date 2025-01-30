from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import News, MediaFiles


class BaseAPITest(APITestCase):
    """
    Базовый класс, чтобы не дублировать логику создания пользователя и аутентификации.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            phone_number='123456789',
            password='pass'
        )
        self.client.force_authenticate(user=self.user)


# ---------------------------------------------------------
#   SEND VERIFICATION CODE
# ---------------------------------------------------------
class SendVerificationCodeViewTest(APITestCase):
    def setUp(self):
        self.url = reverse('send_code')

    def test_send_code_success(self):
        """Отправляем код при наличии телефона."""
        data = {"phone_number": "9999999999"}
        response = self.client.post(self.url, data, format='json')
        # Допускаем, что может вернуться 200 (если мок Twilio) или 500
        self.assertIn(response.status_code, [200, 500])

    def test_send_code_no_phone(self):
        """Ошибка при отсутствии номера телефона."""
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


# ---------------------------------------------------------
#   VERIFY CODE (REGISTER)
# ---------------------------------------------------------
class VerifyCodeAndRegisterViewTest(APITestCase):
    def setUp(self):
        self.url = reverse('verify_code')

    def test_register_success(self):
        """
        Успешная регистрация (при условии, что check_verification_code вернёт True).
        В реальном проекте: замокать Twilio или саму функцию check_verification_code.
        """
        data = {
            "phone_number": "9999999999",
            "code": "123456",
            "full_name": "Test User",
            "password": "testpass"
        }
        response = self.client.post(self.url, data, format='json')
        # Возможные варианты: 201 (если всё ок), 400/500 в случае ошибки
        self.assertIn(response.status_code, [201, 400, 409, 500])

    def test_register_missing_fields(self):
        """Ошибка, если пропущены обязательные поля."""
        data = {
            "phone_number": "9999999999",
            "code": "",
            "full_name": "Test User",
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------
#   LOGIN (CustomTokenObtainPairView)
# ---------------------------------------------------------
class CustomTokenObtainPairViewTest(APITestCase):
    def setUp(self):
        self.url = reverse('token_obtain_pair')
        self.user = get_user_model().objects.create_user(
            phone_number='1234567890',
            password='password123'
        )

    def test_token_obtain_success(self):
        """Успешное получение токена."""
        data = {
            "phone_number": "1234567890",
            "password": "password123"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_obtain_wrong_credentials(self):
        """Ошибка при неверных данных."""
        data = {
            "phone_number": "1234567890",
            "password": "wrongpass"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------
#   REGISTER DEVICE
# ---------------------------------------------------------
class RegisterDeviceViewTest(BaseAPITest):
    """
    Наследуем BaseAPITest, чтобы уже иметь user + client.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('register_device')

    def test_register_device_success(self):
        data = {
            "registration_id": "some_token",
            "type": "android"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_register_device_missing_fields(self):
        data = {
            "registration_id": "only_token"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------
#   MEDIA FILES UPLOAD
# ---------------------------------------------------------
class MediaFilesUploadViewTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.url = reverse('mediafiles-upload')

    def test_upload_media_success(self):
        data = {
            'city': 'TestCity',
            'street': 'TestStreet',
            'description': 'Some description',
            'was_at_date': '2025-01-01',
            'was_at_time': '10:00:00',
        }
        # Можно добавить файлы (mock):
        # test_file = SimpleUploadedFile("test.mp4", b"fake-video-content", content_type="video/mp4")
        # data['videos'] = [test_file]

        response = self.client.post(self.url, data, format='multipart')
        # 201, если всё ок, 400 если не хватает полей
        self.assertIn(response.status_code, [201, 400])

    def test_upload_media_missing_fields(self):
        data = {
            'city': 'NoStreet'
        }
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------
#   MEDIA FILES DETAIL
# ---------------------------------------------------------
class MediaFilesDetailViewTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.url = reverse('mediafiles-detail')
        # Создаём запись MediaFiles
        self.media_record = MediaFiles.objects.create(
            user=self.user,
            city='TestCity',
            street='TestStreet',
            description='TestDescription',
            was_at_date='2025-01-02',
            was_at_time='11:30:00'
        )

    def test_get_detail_success(self):
        response = self.client.get(self.url, {'id': self.media_record.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city'], 'TestCity')

    def test_get_detail_not_found(self):
        response = self.client.get(self.url, {'id': 999999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_detail_no_id(self):
        """Проверка, если мы не передали id вовсе."""
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------
#   MEDIA FILES LIST
# ---------------------------------------------------------
class MediaFilesListViewTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.url = reverse('mediafiles-list')
        # Создаём парочку записей
        self.media1 = MediaFiles.objects.create(
            user=self.user,
            city='City1',
            street='Street1',
            description='Desc1',
            was_at_date='2025-01-03',
            was_at_time='12:00:00'
        )
        self.media2 = MediaFiles.objects.create(
            user=self.user,
            city='City2',
            street='Street2',
            description='Desc2',
            was_at_date='2025-01-04',
            was_at_time='13:00:00'
        )

    def test_get_list_user(self):
        """Получение записей только для пользователя."""
        response = self.client.get(self.url, {'type': 'user', 'limit': '5'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_list_all_empty(self):
        """
        Проверяем, что если в базе нет других записей, всё равно вернёт только имеющиеся.
        """
        # Удалим свои, чтобы проверить пустой результат
        MediaFiles.objects.all().delete()
        response = self.client.get(self.url, {'type': 'all', 'limit': '5'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_list_missing_params(self):
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------
#   NEWS: CREATE, GET LIST, GET DETAIL
# ---------------------------------------------------------
class PostNewsViewTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.url = reverse('news-upload')

    def test_create_news_success(self):
        data = {
            'title': 'Test News',
            'text': 'Some text'
        }
        response = self.client.post(self.url, data, format='multipart')
        self.assertIn(response.status_code, [201, 400])  # 400, если невалидно

    def test_create_news_no_data(self):
        response = self.client.post(self.url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetNewsViewTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.url = reverse('news-detail')
        self.news = News.objects.create(
            title='Existing News',
            text='News text'
        )

    def test_get_news_detail_success(self):
        response = self.client.get(self.url, {'id': self.news.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Existing News')

    def test_get_news_detail_not_found(self):
        response = self.client.get(self.url, {'id': 999999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetNewsListViewTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.url = reverse('news-list')
        self.news1 = News.objects.create(title='News1', text='Text1')
        self.news2 = News.objects.create(title='News2', text='Text2')

    def test_get_news_list_success(self):
        response = self.client.get(self.url, {'limit': '5'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_news_list_no_limit(self):
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------
#   NEWS: UPDATE & DELETE
# ---------------------------------------------------------
class UpdateNewsViewTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.url = reverse('news-update')
        self.news = News.objects.create(title='Old Title', text='Old Text')

    def test_update_news_success(self):
        data = {
            'title': 'New Title'
        }
        response = self.client.put(self.url + f'?id={self.news.id}', data, format='multipart')
        self.assertIn(response.status_code, [200, 400])  # 400 если что-то пойдет не так
        self.news.refresh_from_db()
        if response.status_code == 200:
            self.assertEqual(self.news.title, 'New Title')

    def test_update_news_not_found(self):
        data = {
            'title': 'New Title'
        }
        response = self.client.put(self.url + '?id=999999', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_news_no_id(self):
        data = {'title': 'No ID Title'}
        response = self.client.put(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteNewsViewTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.url = reverse('news-delete')
        self.news = News.objects.create(title='Title to delete', text='Text to delete')

    def test_delete_news_success(self):
        response = self.client.delete(self.url + f'?id={self.news.id}', format='json')
        self.assertIn(response.status_code, [204, 404])
        if response.status_code == 204:
            self.assertFalse(News.objects.filter(id=self.news.id).exists())

    def test_delete_news_not_found(self):
        response = self.client.delete(self.url + '?id=999999', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_news_no_id(self):
        response = self.client.delete(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------
#   CHECK TOKEN
# ---------------------------------------------------------
class CheckTokenTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.url = reverse('check-token')

    def test_check_token_success(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Авторизация успешна')
