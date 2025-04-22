from django.utils import timezone


def date_handler(obj, stime):
    now = timezone.now()
    # 计算时间差
    delta = now - stime
    if delta.days < 7:
        obj.display_time = f"{delta.days} 天前"
        if delta.days == 0:
            obj.display_time = f"24小时内"
    else:
        obj.display_time = obj.created_at.strftime("%m-%d %H:%M")
    return obj