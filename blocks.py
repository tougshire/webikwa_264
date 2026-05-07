import datetime

from django import forms
from django.forms import widgets
from django.conf import settings
from django.utils.functional import cached_property

from wagtail.admin.telepath import register
from wagtail.blocks import (
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


class EventStructValue(StructValue):
    def do_show(self):
        today = datetime.date.today()
        if self.get('date') < today + datetime.timedelta(days = self.get("show_days_before_start")) and self.get('date') > today - datetime.timedelta(days = self.get("show_days_after_end")):
            return True
        return False

    def get_description(self):
        description = self.get("description")
        if not description:
            try:
                description=self.get("article").title
            except:
                pass
        return description

# for use as a child block in a list block
class EventBlock(StructBlock):

    def get_default_showbefore():
        try:
            return settings.WEBIKWA["eventlist_showbefore"]
        except:
            return 90

    def get_default_showafter():
        try:
            return settings.WEBIKWA["eventlist_showafter"]
        except:
            return 1

    date = DateBlock()
    time = TimeBlock( required=False, help_text="The starting time of the event (uses 24 hour clock.  See https://simple.wikipedia.org/wiki/24-hour_clock")
    article = PageChooserBlock( required=False, page_type="webikwa_264.ArticlePage", help_text="Optionaly, an article to link to. If URL is filled in, the aricle's URL will be ignored. If description is filled in, the article's title will be ignored")
    description = CharBlock( required=False, help_text="A description of the event.  If an article is chosen, this can be left blank to use the article's title")
    url = URLBlock( required=False, help_text="A URL for the event.  If an article is chosen, this can be left blank to use the article's URL.  If there is no article and this is blank, the description will not be a link")
    show_days_before_start = IntegerBlock(default = get_default_showbefore())
    show_days_after_end = IntegerBlock(default = get_default_showafter())
    
    class Meta:
        value_class = EventStructValue

class EventlistBlock(ListBlock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        events_all = sorted(context['value'], key=lambda  value  :  "{}:{}".format(value["date"], value["time"]  ) )

        events_all_grouped = {}
        events_in = []
        events_in_grouped = {}
        today = datetime.date.today()
        for event in events_all:
            description = event.get("description")
            if not description:
                try:
                    description = event.get("article").title
                except:
                    pass
            event.description = description

            date_key = event.get("date").isoformat()
            event_data = { "time":event.get("time"), "description":description }
            article = event.get("article")
            if article:
                if article.live:
                    event_data["article"] = article

            if date_key not in events_all_grouped:
                events_all_grouped[ date_key ] = { "date": event.get("date"), "events": []  }
            events_all_grouped[ date_key ]["events"].append( event_data ) 

            if event.get("date") < today + datetime.timedelta(days = event.get("show_days_before_start")) and event.get("date") > today - datetime.timedelta(days =event.get("show_days_after_end")):
                events_in.append(event)
                if date_key not in events_in_grouped:
                    events_in_grouped[date_key] = { "date": event.get("date"), "events": [] }
                events_in_grouped[ date_key ]["events"].append( event_data ) 

        context["events_all"] = events_all
        context["events_all_grouped"] = events_all_grouped
        context["events"] = events_in
        context["events_grouped"] = events_in_grouped

        return context


    class Meta:
        template = "webikwa_264/blocks/eventlist_block.html"

class DocumentBlock(StructBlock):
    document = DocumentChooserBlock(required=True),
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

class IframeBlock(StructBlock):
    url = URLBlock(required=True)
    caption = CharBlock(required=False)
    alt = CharBlock(required=True)

    class Meta:
        icon = "image"
        template = "webikwa_264/blocks/iframe_block.html"
    
class BaseStreamBlock(StreamBlock):
    markdown_block = MarkdownBlock(icon="code")
    paragraph_block = RichTextBlock(icon="pilcrow", features=["link","bold","italic","ol","ul"])
    heading_block = HeadingBlock()
    document_block = DocumentChooserBlock()
    quote_block = BlockQuoteBlock()
    image_block = ImageBlock()
    eventlist_block = EventlistBlock(
        child_block=EventBlock()
    )
    external_image_block = ExternalImageBlock()
    embed_block = EmbedBlock(
        help_text="The URL of the source",
        icon="media",
    )
    html_block = RawHTMLBlock()
    table = TableBlock()

class BodyStreamBlock(BaseStreamBlock):
    pass
