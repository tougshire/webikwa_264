from django.shortcuts import redirect

from wagtail.admin.viewsets.base import ViewSet
from wagtail.admin.viewsets.pages import PageListingViewSet
from .models import ArticlePage, ArticlePlacement, SidebarArticlePage
from wagtail.admin.ui.tables import Column
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from taggit.models import Tag
from django.templatetags.static import static
from django.utils.html import format_html
from wagtail import hooks

import django_filters

@hooks.register("register_icons")
def register_icons(icons):
    return icons + ['webikwa_264/article.svg']

#class ArticlePageFilterSet(PageListingViewSet.filterset_class):
#    tags = django_filters.ModelMultipleChoiceFilter(queryset = Tag.objects.all().order_by('name') )
#    class Meta:
#        model = ArticlePage
#        fields = ["tags","article_placements__page"]
#
##class ArticlePageListingViewSet(PageListingViewSet):
#    icon = "article"
#    menu_order = 100  # will put in 3rd place (000 being 1st, 100 2nd)
#    menu_label = "Articles"
#    add_to_admin_menu = True
#    model = ArticlePage
#    columns = PageListingViewSet.columns + [Column("get_tags","Tags"), Column("get_placements", "Placements")]
#    filterset_class = ArticlePageFilterSet
#
#
#article_page_listing_viewset = ArticlePageListingViewSet("article_pages")
#@hooks.register("register_admin_viewset")
#def register_article_page_listing_viewset():
#    return article_page_listing_viewset
#


class SidebarArticlePageListingViewSet(PageListingViewSet):
    icon = "article"
    menu_order = 110  # will put in 3rd place (000 being 1st, 100 2nd)
    menu_label = "Sidebar Articles"
    add_to_admin_menu = True
    model = SidebarArticlePage


sidebar_article_page_listing_viewset = SidebarArticlePageListingViewSet("sidebar_article_pages")
@hooks.register("register_admin_viewset")
def register_sidebar_article_page_listing_viewset():
    return sidebar_article_page_listing_viewset

class TagsSnippetViewSet(SnippetViewSet):
    panels = [FieldPanel("name")]  # only show the name field
    model = Tag
    icon = "tag"  # change as required
    add_to_admin_menu = True
    menu_label = "Tags"
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    list_display = ["name", "slug"]
    search_fields = ("name",)

register_snippet(TagsSnippetViewSet)

@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('webikwa_264/admin/css/webikwa_264.css'))


@hooks.register('insert_global_admin_js')
def global_admin_js():
    return format_html('<script src="{}"></script>', static('webikwa_264/admin/js/webikwa_264.js'))


@hooks.register('after_create_page')
def do_after_page_create(request, page):
    if isinstance(page, ArticlePage) or isinstance(page, SidebarArticlePage):
        return redirect("/admin/")

@hooks.register('after_edit_page')
def do_after_page_edit(request, page):
    if isinstance(page, ArticlePage) or isinstance(page, SidebarArticlePage):
        return redirect("/admin/")
