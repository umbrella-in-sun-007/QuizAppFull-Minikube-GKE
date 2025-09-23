from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, Institute

@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'city', 'state', 'country', 'is_active', 'created_at')
    list_filter = ('is_active', 'state', 'country', 'created_at')
    search_fields = ('name', 'code', 'city', 'email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'website')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'institute', 'is_staff', 'is_active', 'approval_status')
    list_filter = ('role', 'institute', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'institute__name')
    actions = ['approve_teachers', 'deactivate_teachers']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Institute', {'fields': ('role', 'institute')}),
        ('Profile', {'fields': ('profile_picture', 'bio', 'phone_number', 'date_of_birth')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Institute', {'fields': ('role', 'institute', 'email', 'first_name', 'last_name')}),
    )

    def approval_status(self, obj):
        """Display approval status for teachers"""
        if obj.role == 'teacher':
            if obj.is_active:
                return "✅ Approved"
            else:
                return "⏳ Pending Approval"
        return "N/A"
    approval_status.short_description = "Approval Status"

    def approve_teachers(self, request, queryset):
        """Bulk action to approve selected teachers"""
        teacher_queryset = queryset.filter(role='teacher', is_active=False)
        updated = teacher_queryset.update(is_active=True)
        if updated:
            self.message_user(request, f'{updated} teacher(s) have been approved successfully.')
        else:
            self.message_user(request, 'No pending teachers found in the selection.', level='warning')
    approve_teachers.short_description = "Approve selected teachers"

    def deactivate_teachers(self, request, queryset):
        """Bulk action to deactivate selected teachers"""
        teacher_queryset = queryset.filter(role='teacher', is_active=True)
        updated = teacher_queryset.update(is_active=False)
        if updated:
            self.message_user(request, f'{updated} teacher(s) have been deactivated.')
        else:
            self.message_user(request, 'No active teachers found in the selection.', level='warning')
    deactivate_teachers.short_description = "Deactivate selected teachers"

    def get_readonly_fields(self, request, obj=None):
        """Make institute field readonly after user creation (except for superusers)"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        
        if obj and obj.pk:  # If editing existing user
            if not request.user.is_superuser:
                readonly_fields.append('institute')
        
        return readonly_fields

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'academic_year', 'subject_specialization', 'student_id')
    list_filter = ('academic_year', 'subject_specialization')
    search_fields = ('user__username', 'user__email', 'user__institute__name')
