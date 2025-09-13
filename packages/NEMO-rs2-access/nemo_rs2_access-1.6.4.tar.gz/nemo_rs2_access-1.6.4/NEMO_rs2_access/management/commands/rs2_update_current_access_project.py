from django.core.management import BaseCommand

from NEMO_rs2_access import rs2


class Command(BaseCommand):
    help = "Run every few minutes to update the project to charge on current area access records."

    def handle(self, *args, **options):
        rs2.update_current_access_project()
