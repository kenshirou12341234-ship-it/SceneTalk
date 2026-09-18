from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, LoginForm
from django.contrib.auth import login 

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('top:index')

    def form_valid(self, form):
        user = form.save()          
        login(self.request, user)   
        return super().form_valid(form)

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('top:index')