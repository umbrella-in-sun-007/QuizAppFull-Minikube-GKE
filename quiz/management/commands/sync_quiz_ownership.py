from django.core.management.base import BaseCommand
from quiz.models import Quiz


class Command(BaseCommand):
    help = 'Sync created_by field with owner field for all quizzes'

    def handle(self, *args, **options):
        quizzes = Quiz.objects.all()
        updated_count = 0
        
        for quiz in quizzes:
            if quiz.owner and not quiz.created_by:
                quiz.created_by = quiz.owner
                quiz.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Updated quiz "{quiz.title}" - owner: {quiz.owner.username}'
                ))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Synced ownership for {updated_count} quizzes'
        ))
        
        # Show quizzes with owners
        self.stdout.write(self.style.WARNING('\nCurrent Quiz Ownership:'))
        for quiz in Quiz.objects.all():
            owner_name = quiz.created_by.username if quiz.created_by else 'No owner'
            self.stdout.write(f'  - {quiz.title}: {owner_name}')
