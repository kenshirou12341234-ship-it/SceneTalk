from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
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
        """
        email = self.cleaned_data.get("email")
        if email:
            email = email.lower()
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError(
                    "このメールアドレスは登録できません。入力内容を確認してください。"
                )
        return email

    def clean_password1(self):
        """
        パスワード1（入力欄）の具体エラーメッセージを設定
        """
        password = self.cleaned_data.get("password1")
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as error:
                new_errors = []
                for item in error.error_list:
                    code = getattr(item, "code", "")
                    message = str(item.message if hasattr(item, "message") else item)

                    # 連番・一般的・単純な文字列
                    if code == "common_password" or "一般的" in message or "common" in code:
                        new_errors.append(
                            ValidationError("推測されやすい連番や一般的な文字列は使用できません。")
                        )
                    # 短すぎる
                    elif code == "password_too_short" or "短すぎます" in message:
                        new_errors.append(
                            ValidationError("パスワードが短すぎます。8文字以上で入力してください。")
                        )
                    # 数字のみ
                    elif code == "password_entirely_numeric" or "数字だけ" in message:
                        new_errors.append(
                            ValidationError("数字だけのパスワードは設定できません。")
                        )
                    else:
                        new_errors.append(item)
                raise ValidationError(new_errors)
        return password

    def _post_clean(self):
        """
        Djangoがフォーム検証の『最後（post_clean）』に追加してくる
        password2 側の標準エラーメッセージをここで確実に差し替える
        """
        super()._post_clean()

        # _post_clean実行後に password2 にエラーが付与されている場合
        if "password2" in self._errors:
            raw_p1 = self.data.get("password1")
            raw_p2 = self.data.get("password2")

            # パスワード1と2に入力された文字列が一致している場合
            # （＝不一致エラーではなく、パスワードの強度エラーで弾かれている場合）
            if raw_p1 and raw_p2 and raw_p1 == raw_p2:
                self._errors["password2"] = self.error_class(["他のパスワードをお試しください"])

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        
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