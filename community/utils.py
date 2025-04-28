from django.utils import timezone
from datetime import timedelta

def format_created_at(created_at):
    now = timezone.now()
    if now - created_at < timedelta(days=1):
        return '24小时内'
    elif now - created_at < timedelta(days=7):
        days = (now - created_at).days
        return f'{days}天前'
    return created_at.strftime('%Y-%m-%d %H:%M:%S')
