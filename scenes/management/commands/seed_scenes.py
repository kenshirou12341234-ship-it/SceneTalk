from django.core.management.base import BaseCommand
from scenes.models import Scene, Phrase

class Command(BaseCommand):
    help = "居酒屋シーンの会話フローを投入します"

    def handle(self, *args, **options):
        Phrase.objects.all().delete()
        Scene.objects.all().delete()

        izakaya = Scene.objects.create(name="居酒屋")

        conversation = [
            # 入店〜案内
            ("staff", "いらっしゃいませ!何名様ですか?", "Welcome! How many people?"),
            ("customer", "2人です。", "Two people, please."),
            ("staff", "こちらのお席へどうぞ。", "This way, please."),
            # 注文
            ("staff", "ご注文はお決まりですか?", "Are you ready to order?"),
            ("customer", "おすすめは何ですか?", "What do you recommend?"),
            ("staff", "生ビールが人気です。", "Draft beer is popular."),
            ("customer", "それをお願いします。", "I'll have that, please."),
            # 食事中
            ("customer", "お水をもらえますか?", "Can I have some water?"),
            ("staff", "少々お待ちください。", "Just a moment, please."),
            # 会計〜退店
            ("customer", "お会計をお願いします。", "Check, please."),
            ("staff", "合計3,000円です。", "That will be 3,000 yen."),
            ("staff", "ありがとうございました!", "Thank you very much!"),
        ]

        for i, (speaker, text_ja, text_en) in enumerate(conversation, start=1):
            Phrase.objects.create(
                scene=izakaya,
                speaker=speaker,
                text_ja=text_ja,
                text_en=text_en,
                order=i,
            )

        self.stdout.write(self.style.SUCCESS("居酒屋シーンの会話フローを投入しました 🍺"))