# !/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time: 2018/5/11 12:48
# @Author: Administrator
# @File: views.py

import datetime
from django.shortcuts import render, redirect
from django.db.models import Count
from django.utils import timezone
from django.db.models import Sum
from django.core.cache import cache
from django.contrib import auth
from django.contrib.contenttypes.models import ContentType
from read_statistics.utils import get_seven_days_read_data,  \
                                  get_today_hot_data,        \
                                  get_yesterday_hot_data
from blog.models import BlogType, Blog


def get_seven_days_hot_data():
    today = timezone.now().date()
    one_week_before = today - datetime.timedelta(days=6)
    seven_hot_blogs = Blog.objects    \
                          .filter(read_details__date__lte=today, read_details__date__gte=one_week_before)  \
                          .values('id', 'title')   \
                          .annotate(read_num_sum=Sum('read_details__read_num'))   \
                          .order_by('-read_num_sum')
    return seven_hot_blogs[:7]


def get_30_days_hot_data():
    today = timezone.now().date()
    one_month_before = today - datetime.timedelta(days=29)
    one_month_blogs = Blog.objects \
                             .filter(read_details__date__lte=today, read_details__date__gte=one_month_before) \
                             .values('id', 'title') \
                             .annotate(read_num_sum=Sum('read_details__read_num')) \
                             .order_by('-read_num_sum')
    return one_month_blogs[:7]


def login(request):
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    user = auth.authenticate(request, username=username, password=password)
    if user is not None:
        auth.login(request, user)
        # Redirect to a home page.
        return redirect('/')
    else:
        return render(request, 'error.html', {'message': '用户名或密码不正确！'})


def home(request):
    context_type = ContentType.objects.get_for_model(Blog)
    dates, read_nums = get_seven_days_read_data(context_type)
    today_hot_data = get_today_hot_data(context_type)
    yesterday_hot_data = get_yesterday_hot_data(context_type)

    # 获取七天内的缓存数据
    seven_hot_blogs = cache.get('seven_hot_blogs')
    if seven_hot_blogs is None:
        seven_hot_blogs = get_seven_days_hot_data()
        cache.set('seven_hot_blogs', seven_hot_blogs, 3600)

    # 获取30天内的缓存数据
    one_month_blogs = cache.get('one_month_blogs')
    if one_month_blogs is None:
        one_month_blogs = get_30_days_hot_data()
        cache.set('one_month_blogs', one_month_blogs, 3600)

    context = {'read_nums': read_nums,
               'dates': dates,
               'today_hot_data': today_hot_data,
               'yesterday_hot_data': yesterday_hot_data,
               'seven_hot_blogs': seven_hot_blogs,
               'one_month_blogs': one_month_blogs,
               }
    return render(request, 'home.html', context)


def about(request):
    # 获取日期归档统计数量:
    blog_dates = Blog.objects.dates('created_time', 'month', order='DESC')
    blog_dates_dict = {}
    for blog_date in blog_dates:
        blog_count = Blog.objects.filter(created_time__year=blog_date.year, created_time__month=blog_date.month).count()
        blog_dates_dict[blog_date] = blog_count

    # 获取博客分类统计数量 方法一： annotate()
    context = {'blog_types': BlogType.objects.annotate(blog_count=Count('blog')),
               'blog_dates': blog_dates_dict}
    return render(request,'about.html', context)



