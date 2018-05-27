from django.shortcuts import render_to_response, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Count
from .models import BlogType, Blog, ReadNum


def get_blog_list_common_data(request, blogs_all_list):
    paginator = Paginator(blogs_all_list, settings.EACH_PAGE_BLOGS_NUMBER)
    page_num = request.GET.get('page', 1)
    page_of_blogs = paginator.get_page(page_num)
    current_page_num = page_of_blogs.number
    # 获取当前页码的前后2页的页码范围
    page_range = list(range(max(current_page_num - 2, 1), current_page_num)) + \
                 list(range(current_page_num, min(current_page_num + 2, paginator.num_pages) + 1))
    # 加上省略页码标志
    if page_range[0] - 1 >= 2:
        page_range.insert(0, '...')
    if paginator.num_pages - page_range[-1] >= 2:
        page_range.append('...')
    # 加上首页和尾页
    if page_range[0] != 1:
        page_range.insert(0, 1)
    if page_range[-1] != paginator.num_pages:
        page_range.append(paginator.num_pages)

    # 获取日期归档统计数量:
    blog_dates = Blog.objects.dates('created_time', 'month', order='DESC')
    blog_dates_dict = {}
    for blog_date in blog_dates:
        blog_count = Blog.objects.filter(created_time__year=blog_date.year, created_time__month=blog_date.month).count()
        blog_dates_dict[blog_date] = blog_count

    # 获取博客分类统计数量 方法一： annotate()
    context = {'blogs': page_of_blogs.object_list, 'page_of_blogs': page_of_blogs,
               'blog_types': BlogType.objects.annotate(blog_count=Count('blog')), 'page_range': page_range,
               'blog_dates': blog_dates_dict}
    """
    # 获取博客分类统计数量  - 方法二
    blog_types = BlogType.objects.all()
    blog_type_list = []
    for blog_type in blog_types:
        blog_type.blog_count = Blog.objects.filter(blog_type=blog_type).count()
        blog_type_list.append(blog_type)
    context = {'blogs': page_of_blogs.object_list, 'page_of_blogs': page_of_blogs,
               'blog_types': blog_type_list, 'page_range': page_range,
               'blog_dates': Blog.objects.dates('created_time', 'month', order='DESC')}
    """
    return context


def blog_list(request):
    blogs_all_list = Blog.objects.all()
    context = get_blog_list_common_data(request, blogs_all_list)
    return render_to_response('blog/blog_list.html', context)


def blogs_with_type(request, blog_type_pk):
    blog_type = get_object_or_404(BlogType, pk=blog_type_pk)
    blogs_all_list = Blog.objects.filter(blog_type=blog_type)
    context = get_blog_list_common_data(request, blogs_all_list)
    context['blog_type'] = blog_type
    return render_to_response('blog/blogs_with_type.html', context)


def blogs_with_date(request, year, month):
    blogs_all_list = Blog.objects.filter(created_time__year=year, created_time__month=month)
    context = get_blog_list_common_data(request, blogs_all_list)
    blog_with_date = '%s年%s月' % (year, month)
    context['blogs_with_date'] = blog_with_date
    return render_to_response('blog/blogs_with_date.html', context)


def blog_detail(request, blog_pk):
    blog = get_object_or_404(Blog, pk=blog_pk)
    if not request.COOKIES.get('blog_%s_num' % blog_pk):
        if ReadNum.objects.filter(blog=blog).count():
            # exist record
            readnum = ReadNum.objects.get(blog=blog)
        else:
            # not exist record
            readnum = ReadNum(blog=blog)
        # 计数加1
        readnum.read_num += 1
        readnum.save()

    # 获取日期归档统计数量:
    blog_dates = Blog.objects.dates('created_time', 'month', order='DESC')
    blog_dates_dict = {}
    for blog_date in blog_dates:
        blog_count = Blog.objects.filter(created_time__year=blog_date.year, created_time__month=blog_date.month).count()
        blog_dates_dict[blog_date] = blog_count

    context = {'blog': blog,
               'blogs_all_list': Blog.objects.all(),
               'blog_types': BlogType.objects.annotate(blog_count=Count('blog')),
               'blog_dates': blog_dates_dict,
               'previous_blog': Blog.objects.filter(created_time__gt=blog.created_time).last(),
               'next_blog': Blog.objects.filter(created_time__lt=blog.created_time).first()}
    response = render_to_response('blog/blog_detail.html', context)
    response.set_cookie('blog_%s_num' % blog_pk, 'True')
    return response