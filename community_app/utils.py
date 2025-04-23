from django.db.models import QuerySet
from django.utils import timezone


def date_handler(obj_data):
    now = timezone.now()
    if isinstance(obj_data, QuerySet) or isinstance(obj_data, list) or isinstance(obj_data, tuple):
        for obj in obj_data:
            delta = now - obj.created_at
            if delta.days < 7:
                obj.display_time = f"{delta.days} 天前" if delta.days else f"24小时内"
            else:
                obj.display_time = obj.created_at.strftime("%m-%d")
            obj.replies_ = []
            for reply in obj.replies.all():
                # 处理一级回复的时间显示
                delta = now - reply.created_at
                if delta.days < 7:
                    reply.display_time = f"{delta.days} 天前" if delta.days else f"24小时内"
                else:
                    reply.display_time = reply.created_at.strftime("%m-%d %H:%M")
                obj.replies_.append(reply)
        return obj_data
    else:
        delta = now - obj_data.created_at
        if delta.days < 7:
            obj_data.display_time = f"{delta.days} 天前" if delta.days else f"24小时内"
        else:
            obj_data.display_time = obj_data.created_at.strftime("%m-%d %H:%M")
        return obj_data
