"""User model for Task Tracker."""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager for User model using email instead of username."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with email and password."""
        if not email:
            raise ValueError('Email address is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model using email as username field.
    
    Fields:
    - email: Unique email address (used for authentication)
    - first_name: User's first name
    - last_name: User's last name  
    - position: Job position/title
    - department: Department name
    - is_active: Whether user account is active
    - date_joined: Date when user registered
    """
    
    username = None  # Remove username field
    email = models.EmailField(
        'Email адрес',
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким email уже существует.',
        }
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    position = models.CharField('Должность', max_length=255, blank=True)
    department = models.CharField('Отдел', max_length=255, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']
    
    def __str__(self):
        """Return user's full name or email."""
        return self.get_full_name() or self.email
    
    def get_full_name(self):
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
