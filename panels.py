from django.utils.html import format_html
from wagtail.admin.panels import Panel,HelpPanel
from taggit.models import Tag, TaggedItemBase
from django.db.models import Count, Q
from wagtail.images.models import Image as WagtailImage

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
                                    <option value="aligntcenter">Center</option>
                                    <option value="aligntleft">Left</option>
                                    <option value="aligntright">Right</option>
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



class PlacementListPanel(HelpPanel):
    class BoundPanel(HelpPanel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            def expired_verb(expired):
                return "Expired" if expired else ""

            content = '<div class="help help_placement_list"><h3>Placements</h3>'
            content = (
                content
                + "<table id='placements_list'><tr><th>Page</th><th>Expiration</th></tr>"
            )
            placements = []
            if self.instance.pk:
                placements = (
                    list(self.instance.articlepage_placements.all()) +
                    list(self.instance.articlesidebar_placements.all())
                )
            for placement in placements:
                content = content + format_html(
                    "<tr><td>{}</td><td>{}</td><td>{}</td></tr>",
                    placement.page,
                    placement.expiration_date,
                    expired_verb(placement.is_expired()),
                )

            content = content + "</table></div>"
            self.content = content

class TagListPanel(HelpPanel):
    class BoundPanel(HelpPanel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            content = '<div class="help_table help_tag_list"><h3>Current Tags</h3>'
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
                        tagit_div = document.getElementById("id_tags").parentNode
                        tagit_new = tagit_div.querySelector("li[class='tagit-new']").querySelector("input")
                        tagit_new.parentNode.dispatchEvent(new MouseEvent("click", { view: window, bubbles: true, cancelable: true } ) )
                        tagit_new.value=el_targ.dataset.slug
                    }
                })
                </script>
                """
            )
            self.content = content
