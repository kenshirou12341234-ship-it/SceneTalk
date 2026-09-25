from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CustomUserCreationForm, LoginForm


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("top:index")

    def form_valid(self, form):
        # ユーザーを作成・保存
        user = form.save()
        # 新規登録直後にそのまま自動ログインを実行
        login(self.request, user)
        # success_urlへリダイレクト
        return HttpResponseRedirect(self.get_success_url())


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("top:index")