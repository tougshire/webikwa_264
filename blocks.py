import datetime

from django import forms
from django.forms import widgets
from django.conf import settings
from django.utils.functional import cached_property

from wagtail.admin.telepath import register
from wagtail.blocks import (
    Block,
    StreamBlock,
    StructBlock,
    BlockQuoteBlock,
    CharBlock,
    ChoiceBlock,
    DateBlock,
    IntegerBlock,
    ListBlock,
    PageChooserBlock,
    RawHTMLBlock,
    RichTextBlock,
    TimeBlock,
    URLBlock,
    StructValue,
)

from wagtail.blocks.struct_block import StructBlockAdapter
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtailmarkdown.blocks import MarkdownBlock


class LinkStructValue(StructValue):
    def get_description(self):
        description = self.get("description")
        if not description:
            try:
                description = self.get("article").title
            except:
                pass
        return description


class LinkBlock(StructBlock):
    page = PageChooserBlock(
        required=False,
        page_type="wagtailcore.Page",
        help_text="Optionaly, an article to link to. If URL is filled in, the aricle's URL will be ignored. If description is filled in, the article's title will be ignored",
    )
    description = CharBlock(
        required=False,
        help_text="A description of the event.  If an article is chosen, this can be left blank to use the article's title",
    )
    url = URLBlock(
        required=False,
        help_text="A URL for the event.  If an article is chosen, this can be left blank to use the article's URL.  If there is no article and this is blank, the description will not be a link",
    )
    groups = CharBlock(
        required=False,
        help_text="A group name or comma separted list of group names for grouping the links. Only links in the parent block's groups be displayed",
    )

    class Meta:
        value_class = LinkStructValue


class LinklistBlock(StructBlock):
    link_list = ListBlock(child_block=LinkBlock)
    linkitem_class = CharBlock(
        "link item class",
        default="linkitem",
        help_text="css class to apply to each item",
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)

        # grouped_links = { group:[] for group in [ group.strip() for group in self.groups.split(",") ] }

        links_grouped = {}
        links = []

        for link in value.get("link_list"):
            link_data = {"url": link.get("url")}
            description = link.get("description")
            page = link.get("page")
            if page:
                if page.live:
                    link_data["page"] = page
                if not description:
                    try:
                        description = link.get("page").title
                    except:
                        pass
            link_data["description"] = description

            if link.get("groups"):
                link_groups = {
                    group: []
                    for group in [
                        group.strip() for group in link.get("groups").split(",")
                    ]
                }

                for group in link_groups:
                    if group not in links_grouped:
                        links_grouped[group] = []
                    links_grouped[group].append(link_data)

            links.append(link_data)

        context["links_grouped"] = links_grouped
        context["links"] = links

        return context

    class Meta:
        template = "webikwa_264/blocks/linklist_block.html"


class EventStructValue(StructValue):
    # tpva5s536 get rid of do_show?
    def do_show(self):
        today = datetime.date.today()
        if self.get("date") < today + datetime.timedelta(
            days=self.get("show_days_before_start")
        ) and self.get("date") > today - datetime.timedelta(
            days=self.get("show_days_after_end")
        ):
            return True
        return False

    def get_description(self):
        description = self.get("description")
        if not description:
            try:
                description = self.get("article").title
            except:
                pass
        return description


# for use as a child block in a list block
class EventBlock(StructBlock):
    def get_default_showbefore():
        try:
            return settings.WEBIKWA["eventlist_showbefore"]
        except (AttributeError, KeyError):
            return 90

    def get_default_showafter():
        try:
            return settings.WEBIKWA["eventlist_showafter"]
        except (AttributeError, KeyError):
            return 1

    date = DateBlock()
    time = TimeBlock(
        required=False,
        help_text="The starting time of the event (uses 24 hour clock.  See https://simple.wikipedia.org/wiki/24-hour_clock",
    )
    article = PageChooserBlock(
        required=False,
        page_type="webikwa_264.ArticlePage",
        help_text="Optionaly, an article to link to. If URL is filled in, the aricle's URL will be ignored. If description is filled in, the article's title will be ignored",
    )
    description = CharBlock(
        required=False,
        help_text="A description of the event.  If an article is chosen, this can be left blank to use the article's title",
    )
    url = URLBlock(
        required=False,
        help_text="A URL for the event.  If an article is chosen, this can be left blank to use the article's URL.  If there is no article and this is blank, the description will not be a link",
    )
    show_days_before_start = IntegerBlock(default=get_default_showbefore())
    show_days_after_end = IntegerBlock(default=get_default_showafter())

    class Meta:
        value_class = EventStructValue


class EventlistBlock(StructBlock):
    event_list = ListBlock(EventBlock)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)

        events_all = sorted(
            value.get("event_list"),
            key=lambda value: "{}:{}".format(value.get("date"), value.get("time")),
        )
        events_all_grouped = {}
        events_in = []
        events_in_grouped = {}
        today = datetime.date.today()
        for event in events_all:
            description = event.get_description()
            if not description:
                try:
                    description = event.get("article").title
                except:
                    pass
            event.description = description

            date_key = event.get("date").isoformat()
            event_data = {"time": event.get("time"), "description": description}
            article = event.get("article")
            if article:
                if article.live:
                    event_data["article"] = article

            if date_key not in events_all_grouped:
                events_all_grouped[date_key] = {"date": event.get("date"), "events": []}
            events_all_grouped[date_key]["events"].append(event_data)

            if event.get("date") < today + datetime.timedelta(
                days=event.get("show_days_before_start")
            ) and event.get("date") > today - datetime.timedelta(
                days=event.get("show_days_after_end")
            ):
                events_in.append(event)
                if date_key not in events_in_grouped:
                    events_in_grouped[date_key] = {
                        "date": event.get("date"),
                        "events": [],
                    }
                events_in_grouped[date_key]["events"].append(event_data)

        context["events_all"] = events_all
        context["events_all_grouped"] = events_all_grouped
        context["events"] = events_in
        context["events_grouped"] = events_in_grouped

        return context

    class Meta:
        template = "webikwa_264/blocks/eventlist_block.html"


class EventsBlock(StructBlock):
    calendar_tags = CharBlock(required=False)

    def get_context(self, value, parent_context=None):
        from .models import CalendarEvent

        context = super().get_context(value, parent_context=parent_context)

        events_all = CalendarEvent.objects.all()
        tags = list(
            filter(len, [tag.strip() for tag in value["calendar_tags"].split(",")])
        )

        events_all_grouped = {}
        events_in = []
        events_in_grouped = {}
        today = datetime.date.today()
        for event in events_all:
            tag_ok = True
            if tags:
                tag_ok = False
                event_tags = [tag.strip() for tag in event.calendar_tags.split(",")]
                tag_ok = True in [tag in event_tags for tag in tags]

            if tag_ok:
                date_key = event.date.isoformat()
                event_data = {
                    "time": event.time,
                    "description": event.get_description(),
                }
                article = event.article
                if article:
                    if article.live:
                        event_data["article"] = article

                if date_key not in events_all_grouped:
                    events_all_grouped[date_key] = {"date": event.date, "events": []}
                events_all_grouped[date_key]["events"].append(event_data)

                if event.date < today + datetime.timedelta(
                    days=event.show_days_before_start
                ) and event.date > today - datetime.timedelta(
                    days=event.show_days_after_end
                ):
                    events_in.append(event)
                    if date_key not in events_in_grouped:
                        events_in_grouped[date_key] = {
                            "date": event.date,
                            "events": [],
                        }
                    events_in_grouped[date_key]["events"].append(event_data)

        context["events_all"] = events_all
        context["events_all_grouped"] = events_all_grouped
        context["events"] = events_in
        context["events_grouped"] = events_in_grouped

        return context

    class Meta:
        template = "webikwa_264/blocks/eventlist_block.html"


class DocumentBlock(StructBlock):
    document = (DocumentChooserBlock(required=True),)
    title = CharBlock(required=True)

    class Meta:
        icon = "doc-full"
        template = "webikwa_264/blocks/document_block.html"


class ImageBlock(StructBlock):
    image = ImageChooserBlock(required=True)
    caption = CharBlock(required=False)
    attribution = CharBlock(required=False)
    alt = CharBlock(required=True)
    link = URLBlock(required=False)

    class Meta:
        icon = "image"
        template = "webikwa_264/blocks/image_block.html"


class ExternalImageBlock(StructBlock):
    url = URLBlock(required=True)
    caption = CharBlock(required=False)
    attribution = CharBlock(required=False)
    alt = CharBlock(required=True)
    link = URLBlock(required=False)

    class Meta:
        icon = "image"
        template = "webikwa_264/blocks/external_image_block.html"


class HeadingBlock(StructBlock):
    heading_text = CharBlock(classname="title", required=True)
    size = ChoiceBlock(
        choices=[
            ("", "Select a heading size"),
            ("h2", "H2"),
            ("h3", "H3"),
            ("h4", "H4"),
            ("h5", "H5"),
            ("h6", "H6"),
        ],
        blank=True,
        required=False,
    )

    class Meta:
        icon = "title"
        template = "webikwa_264/blocks/heading_block.html"


class SummaryBlock(StructBlock):
    class Meta:
        template = "webikwa_264/blocks/summary_block.html"


class BaseStreamBlock(StreamBlock):
    markdown_block = MarkdownBlock(icon="code")
    paragraph_block = RichTextBlock(
        icon="pilcrow", features=["link", "bold", "italic", "ol", "ul"]
    )
    heading_block = HeadingBlock()
    document_block = DocumentChooserBlock()
    quote_block = BlockQuoteBlock()
    image_block = ImageBlock()
    external_image_block = ExternalImageBlock()
    linklist_block = LinklistBlock()
    events_block = EventsBlock()
    eventlist_block = EventlistBlock()
    embed_block = EmbedBlock(
        label="oEmbed Block",
        help_text="The URL of the source",
        icon="media",
    )
    # linklist_block = LinklistBlock()
    table_block = TableBlock()
    html_block = RawHTMLBlock()
    summary_block = SummaryBlock()


class BodyStreamBlock(BaseStreamBlock):
    pass
