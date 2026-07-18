from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Creates/updates the monthly invoicing periodic task (safe to run repeatedly)."

    def handle(self, *args, **options):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="5",
            hour="0",
            day_of_month="1",
            month_of_year="*",
            day_of_week="*",
        )
        task, created = PeriodicTask.objects.update_or_create(
            name="Monthly egg invoicing",
            defaults={
                "crontab": schedule,
                "interval": None,
                "task": "invoicing.tasks.run_monthly_invoicing_task",
                "enabled": True,
            },
        )
        verb = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} periodic task '{task.name}' - runs on the 1st of each month at 00:05. "
            f"You can change the schedule or disable it anytime under "
            f"Admin -> Periodic Tasks."
        ))
