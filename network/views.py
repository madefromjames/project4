from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import json

from .models import User, Post, Follow, Like


def index(request):
    all_post = Post.objects.all().order_by('-date')

    paginator = Paginator(all_post, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    allLikes = Like.objects.all()
    userLikes = []

    for like in allLikes:
        if request.user.id == like.user.id:
            userLikes.append(like.post.id)
 
    if request.user.is_authenticated:
        return render(request, "network/index.html", {
            "page_obj": page_obj,
            "userLikes": userLikes
        })
    else:
        return render(request, "network/login.html")
    
def profile(request, user_id):
    user = User.objects.get(pk=user_id)
    all_post = Post.objects.filter(user=user).order_by('-date')

    following = Follow.objects.filter(follower=user)
    followers = Follow.objects.filter(followed=user)

    try:
        checkFollow = Follow.objects.get(follower=request.user, followed=user)
        isFollowing = True
    except Follow.DoesNotExist:
        isFollowing = False

    allLikes = Like.objects.all()
    userLikes = []

    for like in allLikes:
        if request.user.id == like.user.id:
            userLikes.append(like.post.id)

    paginator = Paginator(all_post, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "network/profile.html", {
        "page_obj": page_obj,
        "username": user.username,
        "following": following,
        "followers": followers,
        "isFollowing": isFollowing,
        "user_profile": user,
        "userLikes": userLikes
    })

def following(request):
    user = User.objects.get(pk=request.user.id)
    followData = Follow.objects.filter(follower=user)
    all_post = Post.objects.all().order_by('-date')

    followingPost = []

    for post in all_post:
        for person in followData:
            if person.followed == post.user:
                followingPost.append(post)

    allLikes = Like.objects.all()
    userLikes = []

    for like in allLikes:
        if request.user.id == like.user.id:
            userLikes.append(like.post.id)

    paginator = Paginator(followingPost, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "network/following.html", {
            "page_obj": page_obj,
            "userLikes": userLikes
        })

def follow(request):
    userFollow = request.POST.get('follow')
    current_user = User.objects.get(pk=request.user.id)
    followData = User.objects.get(username=userFollow)
    f = Follow(follower=current_user, followed=followData)
    f.save()
    user_id = followData.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))

def unfollow(request):
    userFollow = request.POST.get('unfollow')
    current_user = User.objects.get(pk=request.user.id)
    followData = User.objects.get(username=userFollow)
    f = Follow.objects.get(follower=current_user, followed=followData)
    f.delete()
    user_id = followData.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))
    
def new_post(request):
    if request.method == "POST":
        content = request.POST["content"]
        user = User.objects.get(pk=request.user.id)
        post = Post(content=content, user=user)
        post.save()
        return HttpResponseRedirect(reverse("index"))

@csrf_exempt
def editPost(request, postId):
    if request.method == 'PUT':
        data = json.loads(request.body)
        print(data)
        editPost = Post.objects.get(pk=postId)
        editPost.content = data["content"]
        editPost.save()
        return JsonResponse({'message': 'Edit successful', 'data': data['content']})

def remove_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    like = Like.objects.filter(user=user, post=post)
    like.delete()
    like_count = post.likes_count()
    return JsonResponse({"message": "Like removed!", 'like_count': like_count})

def add_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    newLike = Like(user=user, post=post)
    newLike.save()
    like_count = post.likes_count()
    return JsonResponse({"message": "Like added!", 'like_count': like_count})

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
