from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CustomUserCreationForm, LoginForm


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("top:index")

    def form_valid(self, form):
        # 1. super().form_valid(form) を呼ぶことで self.object (作成されたユーザー) が自動でセットされ、
        #    リダイレクト用レスポンスが生成されます
        response = super().form_valid(form)
        
        # 2. 作成されたユーザーを取得してログインを実行
        login(self.request, self.object)
        
        # 3. 成功レスポンスを返す
        return response


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("top:index")