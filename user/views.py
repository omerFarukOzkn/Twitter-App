from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from posts.models import *
from posts.views import userActions
from django.core.cache import cache
from .forms import *

def loginRegister(request):
    if request.method == 'POST':
        if 'register' in request.POST:
            username = request.POST.get('username')
            name = request.POST.get('name')
            email = request.POST.get('email')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            gender = request.POST.get('gender')
            
            if password1 == password2:
                if User.objects.filter(username = username).exists():
                    messages.error(request, 'Kullanıcı adı zaten mevcut!')
                elif User.objects.filter(email = email).exists():
                    messages.error(request, 'Bu email daha önce kullanıldı')
                elif len(password1) < 6:
                    messages.error(request, 'Şifreniz en az 6 karakter olmalıdır')
                elif username in password1:
                    messages.error(request, 'Şifreniz ile kullanıcı adınız benzer olmamalıdır')
                elif password1.isnumeric():
                    messages.error(request, 'Şifreniz tamamen sayısal olmamalıdır')
                else:
                    # kullanıcı kayıt işlemi
                    user = User.objects.create_user(
                        username = username, 
                        email = email, 
                        password = password1
                    )
                    user.save()
                    profile = Profile.objects.create(
                        user = user,
                        name = name
                    )
                    if gender == 'female':
                        profile.image = 'profiles/default-female.jpg'
                    else:
                        profile.image = 'profiles/default-male.jpg'
                    profile.save()
                    login(request, user)
                    messages.success(request, 'Kaydınız oluşturuldu')
                    return redirect('index')
            else:
                messages.error(request, 'Şifreler uyuşmuyor')
        if 'login' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            user = authenticate(request, username = username, password = password)
            
            if user is not None:
                hata = cache.get('deneme')
                if hata:
                    messages.error(request, 'Hesabınıza şu anda giriş yapamazsınız. Hesabınız kilitlendi.')
                else:
                    login(request, user)
                    messages.success(request, 'Giriş yaptınız')
                    deneme = 0
                    cache.set('deneme', deneme, 100000000)
                    next = request.GET.get('next')
                    if next:
                        return redirect(next)
                    else:
                        return redirect('index')
            else:
                messages.error(request, 'Kullanıcı adı veya şifre hatalı')
    
    return render(request, 'user/loginPage.html')

def userLogout(request):
    logout(request)
    messages.success(request, 'Çıkış yaptınız')
    return redirect('login')

def profile(request, slug):
    meta = request.META.get('HTTP_REFERER') # bir önceki sayfanın linkini çektik
    cache.set('meta', meta, 10000) # bir değeri önbelleğe atmak için
    profil = Profile.objects.get(slug = slug)
    retweets = Post.objects.filter(retweet__in = [profil])
    likes = Post.objects.filter(like__in = [profil])
    if request.method == 'POST':
        if 'follow' in request.POST:
            myProfile = request.user.profile
            if myProfile in profil.follower.all():
                myProfile.follow.remove(profil)
                profil.follower.remove(myProfile)
            else:
                myProfile.follow.add(profil)
                profil.follower.add(myProfile)
                YeniBildirim = Notificate(
                    receiver = profil,
                    sender = request.user.profile,
                    islem = 'takip',
                    message = f"{request.user.profile} kullanıcısı sizi takip etmeye başladı"
                )
                YeniBildirim.save()
            profil.save()
            myProfile.save()
        else:
            userActions(request)
        return redirect('profile', slug = profil.slug)
    
    context = {
        'profil': profil,
        'retweets': retweets,
        'likes': likes
    }
    return render(request, 'user/profile.html', context)


def back(request):
    meta = cache.get('meta') # önbelleğe atılan değeri çekiyoruz
    return redirect(meta)


def change(request):
    profileForm = ProfileForm(instance = request.user.profile)
    username = request.user.username
    email = request.user.email
    
    if request.method == 'POST':
        if 'change' in request.POST:
            oldPassword = request.POST.get('oldPassword')
            newPassword1 = request.POST.get('newPassword1')
            newPassword2 = request.POST.get('newPassword2')
            
            user = authenticate(request, username = request.user, password = oldPassword)
            
            if user is not None:
                if newPassword1 == newPassword2:
                    user.set_password(newPassword1)
                    user.save()
                    messages.success(request, 'Şifreniz değiştirildi')
                    return redirect('login')
                else:
                    messages.error(request, 'Şifreler uyuşmuyor')
                    return redirect('change')
            else:
                messages.error(request, 'Eski şifre hatalı')
                hata = cache.get('deneme')
                hata += 1
                cache.set('deneme', hata, 10000000)
                if hata == 3:
                    logout(request)
                    messages.error(request, '3ten fazla deneme yaptığınız için hesabınıza belli bir süreliğine giriş yapamazsınız')
                    return redirect('login')
                return redirect('change')
            
        profileForm = ProfileForm(request.POST, request.FILES, instance = request.user.profile)
        newUsername = request.POST.get('username')
        newEmail = request.POST.get('email')
        user = request.user
        if profileForm.is_valid():
            profileForm.save()
            if newUsername and newEmail:
                if newUsername != user.username:
                    if User.objects.filter(username = newUsername).exists():
                        messages.error(request, 'Bu kullanıcı adı zaten mevcut')
                    else:
                        user.username = newUsername
                        user.save()
                if newEmail != user.email:
                    if User.objects.filter(email = newEmail).exists():
                        messages.error(request, 'Bu email daha önce kullanılmış')
                    else:
                        user.email = newEmail
                        user.save()
            else:
                messages.error(request, 'Tüm alanların doldurulması zorunludur')
                return redirect('change')
            return redirect('profile', slug = request.user.profile.slug)
    
    context = {
        'profileForm':profileForm,
        'username': username,
        'email': email
    }
    return render(request, 'user/settings.html', context)


def savedTweets(request):
    tweets = Post.objects.filter(saves__in = [request.user.profile])
    if request.method == 'POST':
        userActions(request)
        return redirect('saves')
    context = {
        'tweets': tweets
    }
    return render(request, 'savedTweets.html', context)