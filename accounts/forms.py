from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email',)
        labels = {
            'email': 'メールアドレス',
        }

    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       self.fields['password1'].label = 'パスワード'
       self.fields['password2'].label = 'パスワード確認'
class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='メールアドレス')