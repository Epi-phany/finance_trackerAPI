from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin,BaseUserManager

class CustomUserManager(BaseUserManager):
    def _create_user(self, email, username, password,first_name,last_name, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        if not password:
            raise ValueError('Password is not provided')

        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email,username, password,first_name,last_name,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_active',True)
        extra_fields.setdefault('is_superuser',False)
        return self._create_user(email,username, password,first_name, last_name, **extra_fields)

    def create_superuser(self, email,username, password,first_name,last_name, **extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_active',True)
        extra_fields.setdefault('is_superuser',True)
        return self._create_user(email,username, password,first_name, last_name,**extra_fields)

class User(AbstractBaseUser,PermissionsMixin):
    # Abstractbaseuser has password, last_login, is_active by default

    username = models.CharField(max_length=90, null=True,unique=True)
    email = models.EmailField(db_index=True, unique=True, max_length=254, null=True)
    first_name = models.CharField(max_length=240, null=True)
    last_name = models.CharField(max_length=255, null=True)
    # mobile = models.CharField(max_length=50, null=True)
    # address = models.CharField(max_length=250, null=True)

    is_staff = models.BooleanField(default=True) 
    is_active = models.BooleanField(default=True) 
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email','first_name','last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username}"

