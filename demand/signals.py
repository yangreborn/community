# signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Demand, DemandStatusChange

@receiver(pre_save, sender=Demand)
def record_status_change(sender, instance, **kwargs):
    if instance.pk:  # 确保不是新创建的对象
        try:
            old = Demand.objects.get(pk=instance.pk)
            if old.status != instance.status:  # 状态发生变化
                DemandStatusChange.objects.create(
                    demand=instance,
                    from_status=old.status,
                    to_status=instance.status,
                    changed_by=instance._status_change_user,  # 需要设置
                    change_reason=getattr(instance, '_status_change_reason', None)
                )
        except Demand.DoesNotExist:
            pass