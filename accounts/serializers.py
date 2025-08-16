from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username','email','password','first_name','last_name']
        
    def create(self,validated_data):
        user = User(
            username = validated_data['username']
            email = validated_data['email']
            first_name = validated_data.get('first_name','')
            last_name = validated_data.get('last_name','')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user