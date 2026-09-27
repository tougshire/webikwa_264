from django.shortcuts import redirect
from django.conf import settings

from wagtail.admin.views.generic import chooser as chooser_views
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.admin.viewsets.base import ViewSet
from wagtail.admin.viewsets.pages import PageListingViewSet, PageViewSet
from wagtail.admin.ui.tables import Column
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from taggit.models import Tag
from django.templatetags.static import static
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.filters import WagtailFilterSet

from .models import ArticlePage, ArticlePlacement, ArticleSidebarPlacement,  SidebarArticlePage, CalendarEvent, PageZone

import django_filters
import logging

logger = logging.getLogger(__name__)


@hooks.register("register_icons")
def register_icons(icons):
    return icons + ["webikwa_264/article.svg"]


class ArticlePageViewSetFilterSet(WagtailFilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all().order_by("name")
    )
    queryset = ArticlePage.objects.order_by("-last_published_at")

    class Meta:
        model = ArticlePage
        fields = ["tags", "article_placements__pagezone"]

class ArticlePageListingViewSet(PageListingViewSet):
    icon = "article"
    menu_order = 100  # will put in 3rd place (000 being 1st, 100 2nd)
    menu_label = "Articles"
    add_to_admin_menu = True
    model = ArticlePage
    columns = PageListingViewSet.columns + [
        Column("get_tags", "Tags"),
        Column("get_placements", "Placements"),
    ]
    filterset_class = ArticlePageViewSetFilterSet
    ordering = ["-last_published_at"]


article_page_listing_viewset = ArticlePageListingViewSet("article_pages")


@hooks.register("register_admin_viewset")
def register_article_page_listing_viewset():
    return article_page_listing_viewset

class ArticlePageViewSet(PageViewSet):
    columns = PageViewSet.columns + [
        Column("slug", label="Slug", sort_key="slug"),
    ]

article_page_viewset = ArticlePageViewSet("article_pages")



class SidebarArticlePageListingViewSet(PageListingViewSet):
    icon = "article"
    menu_order = 150
    menu_label = "Sidebar Articles"
    add_to_admin_menu = True
    model = SidebarArticlePage


sidebar_article_page_listing_viewset = SidebarArticlePageListingViewSet(
    "sidebar_article_pages"
)


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


@hooks.register("insert_global_admin_css")
def global_admin_css():
    try:
        return format_html(
            "<link rel=\"stylesheet\" href=\"{}\">\n<link rel=\"stylesheet\" href=\"{}\">", static("webikwa_264/admin/css/webikwa_264.css"), static(settings.WEBIKWA["admin_custom_css"])
        )
    except( AttributeError, KeyError):
        return format_html(
            "<link rel=\"stylesheet\" href=\"{}\">", static("webikwa_264/admin/css/webikwa_264.css")
        )

#def xglobal_admin_css():
#    css_string='<link rel="stylesheet" href="{}">'.format(static("webikwa_264/admin/css/webikwa_264.css"))
#    try:
#        css_string = css_string + "\n\n\n\n<link rel=\"stylesheet\" href=\"{}\"".format(static(settings.WEBIKWA["admin_custom_css"]))
#    except( AttributeError, KeyError):
#        logging.info("No custom admin stylesheet specified. If desired, refer to a custom admin stylesheet in settings.WEBEKAH[\"admin_custom_css\"")
#    return format_html(css_string)




@hooks.register("insert_global_admin_js")
def global_admin_js():
    return format_html(
        '<script src="{}"></script>', static("webikwa_264/admin/js/webikwa_264.js")
    )


@hooks.register("after_create_page")
def do_after_page_create(request, page):
    if isinstance(page, ArticlePage) or isinstance(page, SidebarArticlePage):
        return redirect("/admin/")


@hooks.register("after_edit_page")
def do_after_page_edit(request, page):
    if isinstance(page, ArticlePage) or isinstance(page, SidebarArticlePage):
        return redirect("/admin/")

@hooks.register("register_admin_viewset")
def register_article_page_viewset():
    return article_page_viewset


class ArticleChooserView(chooser_views.ChooseView):
    ordering = ["-last_published_at", "title"]

class ArticlePageChooserViewSet(ChooserViewSet):
    # The model can be specified as either the model class or an "app_label.model_name" string;
    # using a string avoids circular imports when accessing the StreamField block class (see below)
    model = "webikwa_264.ArticlePage"

    choose_one_text = "Choose an Article"
    choose_another_text = "Choose another Article"
    edit_item_text = "Edit this Article"
    choose_view_class = ArticleChooserView

article_page_chooser_viewset = ArticlePageChooserViewSet("article_page_chooser")


@hooks.register("register_admin_viewset")
def register_article_page_chooser_viewset():
    return article_page_chooser_viewset


class ArticlePlacementFilterSet(WagtailFilterSet):
    article = django_filters.ModelChoiceFilter(
        queryset=ArticlePage.objects.order_by("-last_published_at")
    )
    pagezone = django_filters.ModelChoiceFilter(
        queryset=PageZone.objects.order_by("page", "sort_order")
    )
    class Meta:
        model=ArticlePlacement
        fields=["article", "pagezone", "expiration_date"]

class ArticlePlacementViewSet(SnippetViewSet):
    model = ArticlePlacement
    add_to_admin_menu=True
    menu_order=120
    list_display = ["article", "pagezone", "expiration_date"]
    inspect_view_enabled = True
    filterset_class = ArticlePlacementFilterSet

#    list_filter = {
#        "pagezone": ["exact"],
#        "article": ["exact"],
#        "expiration_date": ["lt"],
#    }


register_snippet(ArticlePlacementViewSet)


class ArticleSidebarPlacementViewSet(SnippetViewSet):
    model = ArticleSidebarPlacement
    list_display = ["article", 'sidebar_pagezone', "expiration_date"]
    inspect_view_enabled = True
    add_to_admin_menu = True
    menu_order = 175
    #list_filter = {"page": ["exact"], "expiration_date": ["lt"]}


register_snippet(ArticleSidebarPlacementViewSet)


class PageZoneFilterSet(WagtailFilterSet):
    article_placements__article = django_filters.ModelChoiceFilter(
        queryset=ArticlePage.objects.order_by("-last_published_at")
    )
    class Meta:
        model=PageZone
        fields=["article_placements__article"]

class PageZoneViewSet(SnippetViewSet):
    model = PageZone 
    list_display = ["page", 'name', "title", Column("get_article_listr", "Article")]
    inspect_view_enabled = True
    add_to_admin_menu = True
    menu_order = 175
    filterset_class = PageZoneFilterSet


class CalendarEventViewSet(SnippetViewSet):
    model = CalendarEvent
    add_to_admin_menu = True
    menu_order = 190
    icon = "calendar"


register_snippet(CalendarEventViewSet)



