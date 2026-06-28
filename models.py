import datetime
import html
import json
import logging
import re
import sys
import uuid
import zoneinfo

import markdown
import nh3
import requests

from django import forms
from django.conf import settings
from django.db import OperationalError, models
from django.db.models import Count
from django.utils import timezone
from django.utils.html import format_html, mark_safe, strip_tags
from modelcluster.contrib.taggit import ClusterTaggableManager, TaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import Tag, TaggedItemBase
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    HelpPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.admin.ui.tables import Column
from wagtail.contrib.forms.forms import FormBuilder
from wagtail.contrib.forms.models import (
    FORM_FIELD_CHOICES,
    AbstractEmailForm,
    AbstractForm,
    AbstractFormField,
)
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.contrib.forms.utils import get_field_clean_name
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    BaseSiteSetting,
    register_setting,
)
from wagtail.documents import get_document_model
from wagtail.fields import RichTextField, StreamField
from wagtail.images.models import Image as WagtailImage
from wagtail.models import Orderable, Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtailmarkdown.fields import MarkdownField

from .blocks import BodyStreamBlock


logger = logging.getLogger(__name__)


def get_sidebars(request):
    sidebars = []
    for sidebar in SidebarPage.objects.live().all():
        context = sidebar.get_context(request)
        for key in context:
            if not hasattr(sidebar, key):
                setattr(sidebar, key, context[key])
        sidebars.append(sidebar)

    return sidebars


def get_binary_components(input, len):
    res = input
    cur = 0
    ret = []

    while cur < len:
        rem = (res / 2) - int(res / 2)
        ret.append(rem)
        res = int(res / 2)
        cur = cur + 1

    return ret


def get_sidebars_old(request):
    sidebars = []
    for sidebarpage in SidebarPage.objects.live().all():
        sidebar = {"location": sidebarpage.location, "children": []}
        for childpage in sidebarpage.get_children().specific().iterator():
            child = {
                "title": childpage.title,
                "body": childpage.specific.body,
                "context": childpage.specific.get_context(request),
            }

            sidebar["children"].append(child)

        sidebars.append(sidebar)

    return sidebars


class RedirectPage(Page):
    target_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        PageChooserPanel("target_page"),
    ]

    def route(self, request, path_components):
        if path_components:
            return super().route(request, path_components)
        else:
            path_components = [self.target_page.slug]
            return super().route(request, path_components)


class ArticleSingularPage(Page):
    target_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        PageChooserPanel("target_page", page_type=["webikwa_264.ArticlePage"]),
        InlinePanel("submenu_items"),
    ]


class ArticleIndexPage(Page):
    intro = RichTextField(blank=True)
    show_pagetitle = models.BooleanField(
        default=True, help_text="If the page title should be shown"
    )

    show_article_info = models.IntegerField(
        choices=(
            (0, "hide all"),
            (7, "show all"),
            (3, "show authors and date"),
            (1, "show authors"),
            (2, "show date"),
            (4, "show tags"),
        ),
        default=7,
        help_text="Article information to be shown ",
    )
    continue_label = models.CharField(
        "continue reading label",
        blank=True,
        max_length=25,
        default="continue reading",
        help_text='The text to display in the "continue reading" link.  Blank to hide link',
    )

    subpage_types = ["ArticlePage", "SidebarArticlePage"]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        MultiFieldPanel(
            [FieldPanel("continue_label"), FieldPanel("show_article_info")],
            heading="Article Display Options",
        ),
        InlinePanel("submenu_items"),
    ]

    def get_context(self, request):
        tag = request.GET.getlist("tag")

        context = super().get_context(request)

        #        ArticlePages = self.get_children().specific().live()
        ArticlePages = ArticlePage.objects.live().order_by("-last_published_at")
        if tag:
            ArticlePages = ArticlePages.filter(tags__name__in=tag).order_by(
                "last_published_at"
            )

        context["articlepages"] = ArticlePages

        context["sidebars"] = get_sidebars(request)

        return context


class SidebarPage(Page):
    show_pagetitle = models.BooleanField(
        default=False, help_text="If the title of this sidebar should be shown"
    )
    location = models.CharField(
        "location",
        max_length=40,
        blank=True,
        choices=(
            ("left", "left"),
            ("right", "right"),
            ("top", "top"),
            ("bottom", "bottom"),
        ),
    )
    custom_css = models.TextField(
        blank=True,
        help_text='Custom css to be added to the html head section when this page is displayed. Zones will have class names in the format of "zone_1" where "1" is replaced by the zone number',
    )

    content_panels = Page.content_panels + [
        FieldPanel("show_pagetitle"),
        FieldPanel("location"),
        InlinePanel(
            "sidebar_page_zones", help_text="zones are required. Create at least one"
        ),
    ]


class SidebarPageZone(Orderable):
    sidebar_page = ParentalKey(
        SidebarPage, on_delete=models.CASCADE, related_name="sidebar_page_zones"
    )
    name = models.CharField(
        max_length=40,
        help_text='The name used to identify this zone in the admin panel. This is required but can be as simple as a number or letter (one zone can be named "1", the next "2", etc)',
    )
    title = models.CharField(
        max_length=40,
        blank=True,
        help_text="The title, which is optional, to be displayed on the page",
    )

    def get_active_placements(self):
        return self.article_sidebarplacements.filter(
            expiration_date__gte=datetime.date.today()
        ) | self.article_sidebarplacements.filter(expiration_date__isnull=True)

    def __str__(self):
        return "{} {}".format(self.sidebar_page, self.name)


@register_snippet
class ArticlePageTag(TaggedItemBase):
    content_object = ParentalKey(
        "ArticlePage", related_name="tagged_items", on_delete=models.CASCADE
    )


class BaseArticlePage(Page):
    body = StreamField(
        BodyStreamBlock(),
        blank=True,
        use_json_field=True,
        help_text="The body of the article",
        default=[
            (
                "webik_markdown_block",
                {"markdown": "", "applyclass": "", "applystyle": ""},
            )
        ],
    )
    is_creatable = False

    class Meta:
        verbose_name = "Base Article"

    def featured_image(self):
        try:
            return self.article_images.filter(is_featured=True).first()
        except ArticlePageImage.DoesNotExist:
            try:
                return self.article_images.first()
            except ArticlePageImage.DoesNotExist:
                return None

    def get_default_order(self):
        """ "
        orders the children of the page by ord (allows reordering the page) if less then 20 child pages
        if 20 or more pages use the default setting
        """
        return "-latest_revision_created_at"


class PlacementPageListPanel(HelpPanel):
    class BoundPanel(HelpPanel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            content = '<div class="help_placement_page_list"><h3>Available Placement Pages</h3>'
            content = content + "<table><tr><th>page</th></tr>"
            aplaces = PlacementPage.objects.all()
            for page in aplaces:
                content = content + format_html(
                    "<tr><td>{}</td></tr>",
                    page.slug,
                )

            content = content + "</table></div>"
            self.content = content


class TagListPanel(HelpPanel):
    class BoundPanel(HelpPanel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            content = '<div class="help_tag_list"><h3>Current Tags</h3>'
            content = (
                content
                + "<table id='tagged_item_list'><tr><th>Tag</th><th>Count</th><th>&nbsp;</th></tr>"
            )
            tagged_items = Tag.objects.annotate(num_tags=Count("articlepage")).order_by(
                "-num_tags"
            )
            for tagged_item in tagged_items:
                content = content + format_html(
                    "<tr><td>{}</td><td>{}</td><td><button type='button' data-slug='{}'>add</button></tr>",
                    tagged_item.slug,
                    tagged_item.num_tags,
                    tagged_item.slug,
                )

            content = content + "</table></div>"
            content = (
                content
                + """
            <script>
                document.getElementById("tagged_item_list").addEventListener("click", function(e) {
                    e.preventDefault()
                    el_targ = e.target
                    if(el_targ.tagName.toLowerCase() == "button") {
                        el_temp = document.createElement("input")
                        el_targ.parentNode.appendChild(el_temp,el_targ)
                        el_temp.value = el_targ.dataset.slug
                        el_temp.select()
                        document.execCommand("copy")
                        el_targ.parentNode.removeChild(el_temp)

                        tags_input = document.getElementById("id_tags")
                        tags_ul = tags_input.parentNode.querySelector("ul")
                        tags_ul.dispatchEvent(new MouseEvent("click", { view: window, bubbles: true, cancelable: true } ))
                        document.execCommand("paste")
                    }
                })
                </script>
                """
            )
            self.content = content


class PlacementPage(Page):
    show_pagetitle = models.BooleanField(
        default=True, help_text="If the page title should be shown"
    )
    show_article_info = models.IntegerField(
        choices=(
            (0, "hide all"),
            (7, "show all"),
            (3, "show authors and date"),
            (1, "show authors"),
            (2, "show date"),
            (4, "show tags"),
        ),
        default=7,
    )
    continue_label = models.CharField(
        "continue reading label",
        blank=True,
        max_length=25,
        default="continue reading",
        help_text='The text to display in the "continue reading" link.  Blank to hide link',
    )

    content_panels = Page.content_panels + [
        FieldPanel("show_pagetitle"),
        MultiFieldPanel(
            [FieldPanel("continue_label"), FieldPanel("show_article_info")],
            heading="Article Display Options",
        ),
        InlinePanel(
            "page_zones", help_text="Page zones are required. Create at least one"
        ),
        InlinePanel("submenu_items"),
    ]

    def get_context(self, request):
        context = super().get_context(request)

        context["sidebars"] = get_sidebars(request)

        return context


class PageZone(Orderable):
    page = ParentalKey(
        PlacementPage, on_delete=models.CASCADE, related_name="page_zones"
    )
    name = models.CharField(
        max_length=40,
        help_text='The name used to identify this zone in the admin panel.  This is required, but can be as simple as a number or letter (one pagezone can be named "1", the next "2", etc.)',
    )
    title = models.CharField(
        max_length=40,
        blank=True,
        help_text="The title, which is optional.  The title will be displayed on the page",
    )

    def get_active_placements(self):
        return self.article_placements.filter(
            expiration_date__gte=datetime.date.today()
        ) | self.article_placements.filter(expiration_date__isnull=True)

    def __str__(self):
        return "{}: {}".format(self.page, self.name)

    class Meta:
        ordering = ["page", "sort_order"]


class ImageUrlHelpPanel(HelpPanel):
    class BoundPanel(HelpPanel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            try:
                url = self.instance.image.file.url
                alt_text = html.escape(self.instance.alt_text.replace('"', "'"))
                instid = self.instance.id
                content = """
                    <div>
                        <div class="help_image_url">
                            <div>
                                <label class="w-field__label">Image Code</label>
                            </div>
                                <p class="help">
                                    These options are for generating code to place this image in a markdown or html block.  They do not affect how this image is displayed in an image block.
                                </p>
                            <div>
                                <select class="w-field" name="set_image_classwidth">
                                    <option value="widthstandard">Width</option>
                                    <option value="widthverysmall">Very Small</option>
                                    <option value="widthsmall">Small</option>
                                    <option value="widthmediumsmall">Medium Small</option>
                                    <option value="widthmedium">Medium</option>
                                    <option value="widthlarge">Large</option>
                                    <option value="widthverylarge">Very Large</option>
                                </select>
                                <select class="w-field" name="set_image_classfloat">
                                    <option value="sidedefault">Location</option>
                                    <option value="sidecenter">Center</option>
                                    <option value="sideleft">Left</option>
                                    <option value="sideright">Right</option>
                                </select>
                                <p class="help">
                                    The following is the HTML code for the image with size and location classes reflecting the above choices.
                                </p>
                                <span class="help_image_url_copy"
                                <span class="help_image_url_snippet" name="image_url" data-default="&lt;img src=&quot;{url}&quot alt=&quot;{alt_text}&quot; class=&quot;&quot /&gt;">&lt;img src=&quot;{url}&quot alt=&quot;{alt_text}&quot; class=&quot;sidedefault widthdefault&quot; /&gt;</span>
                                <button type="button" class="help_image_url_copy" name="copy_image_url">copy snippet</button>
                            </div>
                        </div>
                    </div>
                """
                self.content = content.format(instid=instid, url=url, alt_text=alt_text)
            except WagtailImage.DoesNotExist as e:
                print(e, type(e))


class ArticlePage(BaseArticlePage):
    date = models.DateField("Post date", default=datetime.date.today)
    summary = MarkdownField(
        blank=True,
        help_text="A summary, in markdown, to be displayed instead of the body for index views.  There is no hard limit on the length but the intention is for this is that it be brief.  The summary can also be included in the body with a summary block",
    )

    authors = ParentalManyToManyField("webikwa_264.Author", blank=True)
    tags = ClusterTaggableManager(through=ArticlePageTag, blank=True)

    show_info = models.IntegerField(
        choices=(
            (0, "hide all"),
            (7, "show all"),
            (3, "show authors and date"),
            (1, "show authors"),
            (2, "show date"),
            (4, "show tags"),
        ),
        default=7,
        help_text="Article information to be shown when viewing the article in a singular page",
    )

    parent_page_types = ["ArticleIndexPage"]

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("date"),
                FieldPanel("authors", widget=forms.CheckboxSelectMultiple),
                FieldPanel("show_info"),
            ],
            heading="Article information",
        ),
        FieldPanel("summary"),
        MultiFieldPanel(
            [
                FieldPanel("body", help_text="The body of the article"),
            ],
            help_text="Add blocks to the body",
        ),
        MultiFieldPanel(
            [
                InlinePanel("article_images", label="Article images"),
            ],
            heading="Images",
        ),
        MultiFieldPanel(
            [
                InlinePanel("article_placements"),
                PlacementPageListPanel(),
            ],
            heading="Placements",
            help_text="If you are using placement pages, place the article in the appropriate page and zone",
        ),
        MultiFieldPanel([FieldPanel("tags"), TagListPanel()]),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("summary"),
        index.SearchField("body"),
    ]

    class Meta:
        verbose_name = "Article"
        ordering = ("-last_published_at",)

    def get_tags(self):
        tag_list = [tag.name for tag in self.tags.all().order_by("name")]
        return ",".join(tag_list)

    def get_placements(self):
        placement_list = []
        for placement in self.article_placements.all():
            placement_line = f"{placement.pagezone}"
            if (
                placement.expiration_date is not None
                and placement.expiration_date < datetime.date.today()
            ):
                placement_line = placement_line + " (expired)"
            placement_list.append(placement_line)
        return placement_list

    def get_show_info(self, info=""):
        infodict = {}
        infolist = get_binary_components(self.show_info, 3)
        if not info:
            return infolist

        infodict["authors"] = infolist[0]
        infodict["date"] = infolist[1]
        infodict["tags"] = infolist[2]
        return infodict[info]

    def show_authors(self):
        return self.get_show_info("authors")

    def show_date(self):
        return self.get_show_info("date")

    def show_tags(self):
        return self.get_show_info("tags")

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["sidebars"] = get_sidebars(request)

        context["tags"] = []
        for tag in context["page"].tags.all():
            context["tags"].append(tag)

        context["show_authors"], context["show_date"], context["show_tags"] = (
            get_binary_components(self.show_info, 3)
        )

        try:
            context["og_url"] = settings.OG_URL
        except AttributeError:
            pass

        context["test"] = "tpva5ic22"

        return context

    def get_success_url(self):
        return "admin/article_pages"


class ArticlePlacement(models.Model):
    article = ParentalKey(ArticlePage, related_name="article_placements")
    pagezone = models.ForeignKey(
        PageZone, on_delete=models.CASCADE, null=True, related_name="article_placements"
    )
    show_body = models.BooleanField(
        "show full body", default=False, help_text="Show the body instead the summary"
    )
    boldness = models.CharField(
        "boldness",
        max_length=40,
        choices=(
            ("bold", "Bold"),
            ("normal", "Normal"),
            ("light", "Light"),
        ),
        default="normal",
        help_text="A signal to the template about how to style this article on this page, from Very Bold to Very Light",
    )
    expiration_date = models.DateField(
        "Expiration Date",
        blank=True,
        null=True,
        help_text="The date after which the article will be removed from this page zone. This is only takes affect when remove_exipred_placements is run",
    )

    def __str__(self):
        return f"{self.article}->{self.pagezone}"

    class Meta:
        ordering = ("pagezone", "article")

    panels = [
        FieldPanel("article", widget=forms.Select),
        "pagezone",
        "show_body",
        "boldness",
        "expiration_date",
    ]


class ArticlePlacementViewSet(SnippetViewSet):
    model = ArticlePlacement
    list_display = ["article", "pagezone", "expiration_date"]
    inspect_view_enabled = True

    list_filter = {
        "pagezone": ["exact"],
        "expiration_date": ["lt"],
    }


register_snippet(ArticlePlacementViewSet)


class SidebarArticlePage(BaseArticlePage):
    date = models.DateField("Post date", default=datetime.date.today)
    show_title = models.BooleanField(
        default=True, help_text="If the title should be shown"
    )

    parent_page_types = ["ArticleIndexPage"]

    content_panels = Page.content_panels + [
        FieldPanel("show_title"),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                InlinePanel("article_sidebarplacements"),
            ],
            heading="Placements",
        ),
    ]


class ArticleSidebarPlacement(Orderable):
    article = ParentalKey(SidebarArticlePage, related_name="article_sidebarplacements")
    sidebar_pagezone = models.ForeignKey(
        SidebarPageZone,
        on_delete=models.CASCADE,
        null=True,
        related_name="article_sidebarplacements",
    )
    expiration_date = models.DateField(
        "Expiration Date",
        blank=True,
        null=True,
        help_text="The date after which the article will be removed from this page zone. This is only takes affect when remove_exipred_placements is run",
    )

    def __str__(self):
        return f"{self.article}->{self.page}:{self.zone}"

    panels = [FieldPanel("sidebar_pagezone", widget=forms.Select), "expiration_date"]


class ArticleSidebarPlacementViewSet(SnippetViewSet):
    model = ArticleSidebarPlacement
    list_display = ["article", "page", "zone", "expiration_date"]
    inspect_view_enabled = True

    list_filter = {"page": ["exact"], "expiration_date": ["lt"]}


register_snippet(ArticleSidebarPlacementViewSet)


class ArticlePageImage(Orderable):
    page = ParentalKey(
        BaseArticlePage, on_delete=models.CASCADE, related_name="article_images"
    )
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.CASCADE, related_name="+"
    )
    alt_text = models.TextField("alt text", blank=True, max_length=250)
    display_with_summary = models.BooleanField(
        "with summary",
        default=False,
        help_text="If this image should appear where the article summary is shown",
    )
    display_before_body = models.BooleanField(
        "before body",
        default=False,
        help_text="If this image should appear before the body of the article",
    )
    display_after_body = models.BooleanField(
        "after_body",
        default=False,
        help_text="If this image should appear after the body of the article",
    )
    is_featured = models.BooleanField(
        "is featured",
        default=False,
        help_text="If this image is the featured image to be used in social media links and similar contexts. Only one should be selected. ",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("image"),
                FieldPanel("alt_text"),
            ],
            heading="Image Properties",
        ),
        MultiFieldPanel(
            [
                FieldPanel("display_with_summary"),
                FieldPanel("display_before_body"),
                FieldPanel("display_after_body"),
                FieldPanel("is_featured"),
            ]
        ),
        ImageUrlHelpPanel(),
    ]


class ArticlePageGalleryImage(Orderable):
    page = ParentalKey(
        BaseArticlePage, on_delete=models.CASCADE, related_name="gallery_images"
    )
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.CASCADE, related_name="+"
    )
    alt_text = models.TextField("alt text", blank=True, max_length=250)

    panels = [
        FieldPanel("image"),
        FieldPanel("alt_text"),
    ]


@register_snippet
class Author(models.Model):
    name = models.CharField(max_length=255)
    author_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("author_image"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Authors"


@register_setting
class SiteSpecificImportantPages(BaseSiteSetting):
    article_index_page = models.ForeignKey(
        "wagtailcore.Page", null=True, on_delete=models.SET_NULL, related_name="+"
    )

    panels = [
        FieldPanel("article_index_page"),
    ]


@register_setting
class SiteTemplateSettings(BaseSiteSetting):
    header_style = models.CharField(
        max_length=255,
        blank=True,
        default="50%",
        help_text="Inline styling for the header",
    )

    banner_image = models.ForeignKey(
        "wagtailimages.Image",
        related_name="+",
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    show_banner_image = models.BooleanField(
        "show banner image",
        default=True,
        help_text="Show the chosen banner image.  If deselected, banner_text will be used instead of the image",
    )
    banner_image_style = models.CharField(
        max_length=255,
        blank=True,
        default="50%",
        help_text="Styling for the banner image or if a single value, A css value representing the width of the banner image. Include at least one semicolon (;) to indicate that this is a style, and not just a width value",
    )
    banner_text = models.CharField(
        "banner_text",
        max_length=80,
        blank=True,
        default="webikwa_264",
        help_text="The alt text to be displayed if there is a banner image, or the text to be displayed if there is no image",
    )
    site_description = models.CharField(
        "site description",
        max_length=80,
        blank=True,
        default="New Wibewa Wagtail Blog",
        help_text="The site description to be displayed near the banner image or banner text",
    )
    show_topbar = models.BooleanField(
        default=False, help_text="If the top sidebar should be shown"
    )
    show_leftbar = models.BooleanField(
        default=False, help_text="If the left sidebar should be shown"
    )
    show_rightbar = models.BooleanField(
        default=False, help_text="If the right sidebar should be shown"
    )
    show_bottombar = models.BooleanField(
        default=False, help_text="If the bottom sidebar should be shown"
    )
    mainmenu_location = models.CharField(
        "main menu location",
        max_length=20,
        choices=(
            ("none", "None"),
            ("top", "Top"),
            ("left", "Left"),
            ("right", "Right"),
        ),
        help_text="The location of the main menu",
        default="top",
    )
    theme_color = models.CharField(
        "theme color",
        max_length=30,
        default="black",
        help_text='The theme color. This should match the base name of a css file in a static folder webikwa_264/css. Ex "blue" if there is a webikwa_264/css/blue.css',
    )
    after_article = MarkdownField(
        "after_article",
        default="""
            <div id="after_article">
                You can share this post on most social media by copying the URL and pasting it into a post.
                <button type="button" id="copy_url_button">copy url</button>
            </div>
            <script>
                var url_button = document.getElementById("copy_url_button")
                url_button.addEventListener("click", function(e) {
                    e.preventDefault()
                    var url_input = document.createElement("input")
                    var url_div = document.getElementById("copy_url_div")
                    url_div.appendChild(url_input)
                    url_input.value=window.location.href
                    url_input.select()
                    document.execCommand("copy")
                    url_div.removeChild(url_input)
                })
            </script>
        """,
        help_text="content to follow each article",
    )
    footer_text = MarkdownField(
        "footer text",
        blank=True,
        default="Created wth Wagtail and webikwa_264",
        help_text="The footer in markdown",
    )
    favicon = models.CharField(
        "path to favicon",
        max_length=125,
        blank=True,
        help_text="The path to the favicon. If static, precede with 'static:' ex: static:images/favicon.ico",
    )

    def __str__(self):
        return (
            "Template Settings for " + self.site.__str__()
            if self.site is not None
            else "None"
        )

    class Meta:
        verbose_name_plural = "Template Settings"


def clean_form(self):
    honeypot_err = False

    for field_name in self.honeypot_field_list:
        field_data = self.cleaned_data.get(field_name)
        if str(field_data) > "":
            honeypot_err = True

    if honeypot_err:
        self.add_error(None, self.honeypot_error_message)

    return self.cleaned_data


class FormPage(AbstractEmailForm):
    # h/t: https://github.com/octavenz/wagtail-snippets/blob/master/form-builder-field-validation.md for explanatin of get_form and use of the descriptor

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.honeypot_error_message = self.honeypot_error_message

        raw_honeypot_field_list = [
            get_field_clean_name(field_label)
            for field_label in self.honeypot_field_names.split(",")
        ]
        honeypot_field_list = []

        self.honeypot_show_intro = False

        for field_name in raw_honeypot_field_list:
            if field_name in form.fields:
                honeypot_field_list.append(field_name)
                self.honeypot_show_intro = True

        form.honeypot_field_list = honeypot_field_list

        form.clean = clean_form.__get__(form)

        form.submission_class = self.get_submission_class()
        form.submission_page = self

        return form

    template = "webikwa_264/contact_page.html"
    # This is the default path.
    # If ignored, Wagtail adds _landing.html to your template name
    landing_page_template = "webikwa_264/contact_page_landing.html"

    intro = RichTextField(
        blank=True,
        help_text="Enter something like a summary of the form's purpose or general instructions for filling it out. If your form contains honeypots, explain that the form has fields or a field which should be left blank",
    )
    thank_you_text = RichTextField(
        blank=True, help_text="Enter text to be shown after the form is submitted"
    )

    honeypot_field_names = models.CharField(
        "honeypot",
        max_length=255,
        blank=True,
        help_text="The name or comma-separated list of names for the field or fields to be left blank by humans in order to trap bots. The field(s) should be single-line required=False",
    )
    honeypot_error_message = models.CharField(
        "honeypot error message",
        max_length=255,
        blank=True,
        default="If you are a person, please read the notes and retry",
        help_text="The name or comma-separated list of names for the field or fields to be left blank by humans in order to trap bots. The field(s) should be single-line required=False",
    )
    honeypot_intro = RichTextField(
        blank=True,
        default="Note: This form has a field or fields which should be left unfilled. In order to trap automatic form fillers, these fields are not marked but a person should be able to figure out which those are",
        help_text="Explain to visitors that the form has a field or fields which humans should realize are to be left blank",
    )

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel("intro"),
        InlinePanel("form_fields", label="Form Fields"),
        FieldPanel("thank_you_text"),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("from_address", classname="col6"),
                        FieldPanel("to_address", classname="col6"),
                    ]
                ),
                FieldPanel("subject"),
            ],
            heading="Email Settings",
        ),
        MultiFieldPanel(
            [
                FieldPanel("honeypot_field_names"),
                FieldPanel("honeypot_intro"),
                FieldPanel("honeypot_error_message"),
            ],
            heading="Honeypot",
        ),
    ]


class FormField(AbstractFormField):
    page = ParentalKey(FormPage, on_delete=models.CASCADE, related_name="form_fields")


class ArticleCommentPage(Page):
    date = models.DateField("Post date", default=datetime.date.today)
    body = models.CharField(
        max_length=250, blank=True, help_text="The body of the comment"
    )
    commenter_display_name = models.CharField(
        max_length=250, blank=True, help_text="The body of the comment"
    )
    in_reply_to = models.ForeignKey(
        "ArticleCommentPage", on_delete=models.SET_NULL, null=True, blank=True
    )

    parent_page_types = ["ArticlePage"]

    class Meta:
        verbose_name = "Comment"

    search_fields = Page.search_fields + [
        index.SearchField("body"),
        index.SearchField("commenter_display_name"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("date"),
                FieldPanel(
                    "commenter_display_name", widget=forms.CheckboxSelectMultiple
                ),
            ],
            heading="Article information",
        ),
        FieldPanel("body"),
    ]


def get_timezone():
    return settings.TIME_ZONE if hasattr(settings, "TIME_ZONE") else "Etc/UTC"


class CalendarEvent(models.Model):
    date = models.DateField()
    time = models.TimeField(
        blank=True, null=True, help_text="The starting time of the event.  Optional"
    )
    article = models.ForeignKey(
        ArticlePage,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Optionaly, an article to link to. If URL is filled in, the aricle's URL will be ignored. If description is filled in, the article's title will be ignored",
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Optionaly, a page to link to. Similar notes to Article.  If Article and Page are both selected, the article takes precedence.",
        related_name="events_for_page",
    )
    description = models.CharField(
        blank=True,
        max_length=255,
        help_text="A description of the event.  If left blank and an article or page is chosen, then the article or page's title will be used as the description.",
    )
    url = models.URLField(
        blank=True,
        help_text="A URL for the event.  If left blank and an article or page is chosen, then the event description will link to the article or page.  If left blank with no article or page, then the event descrtiption will not be a link.",
    )

    calendar_tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="An optional comma-separated list of tags.  Calendar tags may be used by the displaying block to filter events.  These are not the same as tags used in articles",
    )

    priority = models.IntegerField(
        choices=[(1, "1"), (2, "2"), (3, "3")],
        default=2,
        help_text='The priorty of the event, with 1, 2, and 3 being high, normal, and low respectively.  This affects how early the event will be displayed on a list and the CSS class, which will be "eventpri" plus the number (ex: "eventpri2")',
    )

    def get_description(self):
        description = self.description
        if not description:
            try:
                description = self.article.title
            except AttributeError:
                try:
                    description = self.page.title
                except AttributeError:
                    pass

        return description

    def get_url(self):
        url = self.url
        if not url:
            try:
                url = self.article.url
            except AttributeError:
                try:
                    url = self.page.url
                except AttributeError:
                    pass

        return url

    def __str__(self):
        return "{} {}".format(self.get_description(), self.date)

    class Meta:
        ordering = ("date", "time")


class CalendarEventViewSet(SnippetViewSet):
    model = CalendarEvent
    add_to_admin_menu = True
    menu_order = 300
    icon = "calendar"


register_snippet(CalendarEventViewSet)


class SubMenuItem(Orderable):
    under_page = ParentalKey(
        Page,
        help_text="The page for which this submenu item should be displayed",
        on_delete=models.CASCADE,
        related_name="submenu_items",
    )
    label = models.CharField(max_length=20, help_text="The label to be displayed")
    target = models.ForeignKey(
        Page, on_delete=models.CASCADE, help_text="The target page"
    )
