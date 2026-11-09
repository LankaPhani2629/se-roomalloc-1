from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm
from .models import User
from applications.models import Student


class StudentRegistrationForm(forms.ModelForm):
    # User fields
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Desired username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password (min 6 characters)'}), required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}), required=True)
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@college.edu'}))

    # Student Profile fields
    student_id = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ROLL202601'}))
    name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    gender = forms.ChoiceField(choices=Student.GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    course = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B.Tech Computer Science'}))
    year = forms.ChoiceField(choices=Student.YEAR_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Permanent Residential Address'}))
    guardian_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Parent / Guardian Name'}))
    guardian_phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Contact Number'}))
    merit_score = forms.DecimalField(max_digits=5, decimal_places=2, initial=75.0, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}))

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if Student.objects.filter(student_id=student_id).exists():
            raise ValidationError("A student with this Roll / Student ID already exists.")
        return student_id

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        pwd_confirm = cleaned_data.get('confirm_password')
        if pwd and pwd_confirm and pwd != pwd_confirm:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = User(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['name'],
            role=User.ROLE_STUDENT,
            phone=self.cleaned_data['phone']
        )
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            Student.objects.create(
                user=user,
                student_id=self.cleaned_data['student_id'],
                name=self.cleaned_data['name'],
                gender=self.cleaned_data['gender'],
                course=self.cleaned_data['course'],
                year=int(self.cleaned_data['year']),
                phone=self.cleaned_data['phone'],
                email=self.cleaned_data['email'],
                address=self.cleaned_data['address'],
                guardian_name=self.cleaned_data['guardian_name'],
                guardian_phone=self.cleaned_data['guardian_phone'],
                merit_score=self.cleaned_data['merit_score'],
            )
        return user


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
