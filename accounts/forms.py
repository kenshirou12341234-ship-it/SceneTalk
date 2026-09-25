from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label="メールアドレス",
        widget=forms.EmailInput(attrs={"placeholder": "example@example.com"}),
    )

    class Meta:
        model = CustomUser
        fields = ("email",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "パスワード"
        self.fields["password2"].label = "パスワード確認"

    def clean_email(self):
        """
        メールアドレスのバリデーション処理
        小文字化して重複チェックを行い、エラーメッセージを適切にコントロールする
        """
        email = self.cleaned_data.get("email")
        if email:
            email = email.lower()
            # 既に存在するメールアドレスの場合
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError(
                    "このメールアドレスは登録できません。入力内容を確認してください。"
                )
        return email

    def save(self, commit=True):
        """
        ユーザー保存処理
        username が必要なカスタムモデルの場合も考慮してメールアドレスをセット
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        
        # モデル構造上 username が必要な場合は email を代入
        if hasattr(user, "username") and not user.username:
            user.username = user.email

        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="メールアドレス",
        widget=forms.EmailInput(attrs={"placeholder": "example@example.com"}),
    )