from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_protect
from .forms import CustomUserCreationForm
# Create your views here.
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/community_app/')  # 登录成功后重定向到主页，你可以替换为实际的 URL 名称
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@csrf_protect
def custom_logout(request):
    logout(request)
    return redirect('/community_app/')  # 登出后重定向到你想要的页面，这里假设是名为 'home' 的 URL 名称

def check_login(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': '未登录'}, status=401)
    return JsonResponse({'status': 'success'})


