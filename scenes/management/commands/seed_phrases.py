import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from scenes.models import Scene, Phrase


class Command(BaseCommand):
    help = "CSVファイルからフレーズデータを登録する"

    def handle(self, *args, **options):
        csv_path = Path(__file__).resolve().parent.parent.parent / "fixtures" / "phrases.csv"
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                scene, _ = Scene.objects.get_or_create(name=row["scene_name"])

                Phrase.objects.update_or_create(
                    scene=scene,
                    display_order=row["display_order"],
                    defaults={
                        "turn_order": row["turn_order"],
                        "npc_en": row["npc_en"],
                        "staff_jp": row["staff_jp"],
                        "staff_en": row["staff_en"],
                    },
                )

        self.stdout.write(self.style.SUCCESS("フレーズデータの登録が完了しました"))