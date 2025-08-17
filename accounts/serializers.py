from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    username = serializers.CharField(max_length=25)
    first_name = serializers.CharField(max_length=25)
    last_name = serializers.CharField(max_length=25)
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['id','username','email','password','first_name','last_name']
        
    def create(self,validated_data):
        user = User(
            username = validated_data.get('username'),
            email = validated_data['email'],
            first_name = validated_data.get('first_name',''),
            last_name = validated_data.get('last_name','')
        )
        #user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user