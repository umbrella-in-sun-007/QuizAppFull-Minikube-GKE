from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from quiz.models import Quiz


class Command(BaseCommand):
    help = 'Set up Groups and Permissions for Students and Teachers'

    def handle(self, *args, **options):
        # Create Students group
        students_group, created = Group.objects.get_or_create(name='Students')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Students group'))
        else:
            self.stdout.write(self.style.WARNING('Students group already exists'))
        
        # Students group has no special permissions - they can only view and take quizzes
        students_group.permissions.clear()
        self.stdout.write(self.style.SUCCESS('Configured Students group permissions'))
        
        # Create Teachers group
        teachers_group, created = Group.objects.get_or_create(name='Teachers')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Teachers group'))
        else:
            self.stdout.write(self.style.WARNING('Teachers group already exists'))
        
        # Get Quiz content type
        quiz_content_type = ContentType.objects.get_for_model(Quiz)
        
        # Get all permissions for Quiz model
        quiz_permissions = Permission.objects.filter(content_type=quiz_content_type)
        
        # Assign Quiz permissions to Teachers group
        teachers_group.permissions.clear()
        for perm in quiz_permissions:
            teachers_group.permissions.add(perm)
            self.stdout.write(self.style.SUCCESS(f'Added permission: {perm.codename}'))
        
        # Also add Wagtail page permissions
        from wagtail.models import Page
        page_content_type = ContentType.objects.get_for_model(Page)
        page_permissions = Permission.objects.filter(content_type=page_content_type)
        
        for perm in page_permissions:
            teachers_group.permissions.add(perm)
            self.stdout.write(self.style.SUCCESS(f'Added page permission: {perm.codename}'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Groups and permissions setup complete!'))
        self.stdout.write(self.style.SUCCESS('Teachers can now manage quizzes in the Wagtail admin.'))
        self.stdout.write(self.style.SUCCESS('Students can only view and take quizzes.'))
