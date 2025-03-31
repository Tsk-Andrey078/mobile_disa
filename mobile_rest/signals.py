import logging
import mobile_rest.firebase_init

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import MediaFiles
from fcm_django.models import FCMDevice
from firebase_admin import messaging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=MediaFiles)
def mediafiles_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except sender.DoesNotExist:
            instance._old_status = None


@receiver(post_save, sender=MediaFiles)
def mediafiles_post_save(sender, instance, created, **kwargs):
    old_status = getattr(instance, "_old_status", None)
    # Если объект только что создан – уведомление не отправляем
    if created:
        return

    # Отправка уведомления, если статус изменился и стал "Done" или "Fail"
    if old_status != instance.status and instance.status in ("Done", "Fail"):
        if instance.status == "Done":
            title = "Заявка выполнена"
            body = f"Ваша заявка отработана. ID: {instance.id}"
            data_payload = {"id": str(instance.id)}
        elif instance.status == "Fail":
            title = "Заявка отклонена"

            error_code = getattr(instance, "error_code", "Не указан")
            error_text = getattr(instance, "error_text", "Не указана")
            body = f"Ваша заявка отклонена. ID: {instance.id}, Код: {error_code}, Ошибка: {error_text}"
            data_payload = {
                "id": str(instance.id),
                "error_code": error_code,
                "error_text": error_text,
            }
        else:
            return

        user_devices = FCMDevice.objects.filter(user=instance.user)
        tokens = [device.registration_id for device in user_devices if device.registration_id]

        if tokens:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data_payload,
                tokens=tokens,
            )
            try:
                response = messaging.send_multicast(message)
                logger.info(f"Sent notification to user {instance.user.id}: {response.success_count} success, {response.failure_count} failure")
            except Exception as e:
                logger.exception(f"Error sending user notification: {e}")
