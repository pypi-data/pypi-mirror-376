import base64
import os
import sys

try:
    from unittest.mock import patch
except ImportError:
    from unittest.mock import patch  # noqa

from unittest import skipIf, skipUnless

from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory

from pipeline.collector import default_collector
from pipeline.compressors import (
    CSS_REWRITE_PATH_RE,
    JS_REWRITE_PATH_RE,
    TEMPLATE_FUNC,
    Compressor,
    SubProcessCompressor,
)
from pipeline.compressors.yuglify import YuglifyCompressor
from tests.utils import _, pipeline_settings


@pipeline_settings(
    CSS_COMPRESSOR="pipeline.compressors.yuglify.YuglifyCompressor",
    JS_COMPRESSOR="pipeline.compressors.yuglify.YuglifyCompressor",
)
class CompressorTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.compressor = Compressor()
        default_collector.collect()

    def test_js_compressor_class(self):
        self.assertEqual(self.compressor.js_compressor, YuglifyCompressor)

    def test_css_compressor_class(self):
        self.assertEqual(self.compressor.css_compressor, YuglifyCompressor)

    def test_concatenate_and_rewrite(self):
        css = self.compressor.concatenate_and_rewrite(
            [_("pipeline/css/first.css"), _("pipeline/css/second.css")],
            "css/screen.css",
        )
        expected = """.concat {\n  display: none;\n}\n\n.concatenate {\n  display: block;\n}\n"""  # noqa
        self.assertEqual(expected, css)

    def test_concatenate(self):
        js = self.compressor.concatenate(
            [_("pipeline/js/first.js"), _("pipeline/js/second.js")]
        )
        expected = """(function() {\n  window.concat = function() {\n    console.log(arguments);\n  }\n}()) // No semicolon\n\n;(function() {\n  window.cat = function() {\n    console.log("hello world");\n  }\n}());\n"""  # noqa
        self.assertEqual(expected, js)

    @patch.object(base64, "b64encode")
    def test_encoded_content(self, mock):
        self.compressor.asset_contents.clear()
        self.compressor.encoded_content(_("pipeline/images/arrow.png"))
        self.assertTrue(mock.called)
        mock.reset_mock()
        self.compressor.encoded_content(_("pipeline/images/arrow.png"))
        self.assertFalse(mock.called)

    def test_encoded_content_output(self):
        self.compressor.asset_contents.clear()
        encoded = self.compressor.encoded_content(_("pipeline/images/arrow.png"))
        expected = (
            "iVBORw0KGgoAAAANSUhEUgAAAAkAAAAGCAYAAAARx7TFAAAAMk"
            "lEQVR42oXKwQkAMAxC0Q7rEk5voSEepCHC9/SOpLV3JPULgArV"
            "RtDIMEEiQ4NECRNdciCfK3K3wvEAAAAASUVORK5CYII="
        )
        self.assertEqual(encoded, expected)

    def test_relative_path(self):
        relative_path = self.compressor.relative_path(
            "images/sprite.png",
            "css/screen.css",
        )
        self.assertEqual(relative_path, "../images/sprite.png")

    def test_base_path(self):
        base_path = self.compressor.base_path(
            [_("js/templates/form.jst"), _("js/templates/field.jst")]
        )
        self.assertEqual(base_path, _("js/templates"))

    def test_absolute_path(self):
        absolute_path = self.compressor.absolute_path(
            "../../images/sprite.png", "css/plugins/"
        )
        self.assertEqual(absolute_path, "images/sprite.png")
        absolute_path = self.compressor.absolute_path(
            "/images/sprite.png", "css/plugins/"
        )
        self.assertEqual(absolute_path, "/images/sprite.png")

    def test_template_name(self):
        name = self.compressor.template_name("templates/photo/detail.jst", "templates/")
        self.assertEqual(name, "photo_detail")
        name = self.compressor.template_name("templates/photo_edit.jst", "")
        self.assertEqual(name, "photo_edit")
        name = self.compressor.template_name(
            r"templates\photo\detail.jst",  # noqa
            "templates\\",
        )
        self.assertEqual(name, "photo_detail")

    @pipeline_settings(TEMPLATE_SEPARATOR="/")
    def test_template_name_separator(self):
        name = self.compressor.template_name("templates/photo/detail.jst", "templates/")
        self.assertEqual(name, "photo/detail")
        name = self.compressor.template_name("templates/photo_edit.jst", "")
        self.assertEqual(name, "photo_edit")
        name = self.compressor.template_name(
            r"templates\photo\detail.jst",  # noqa
            "templates\\",
        )
        self.assertEqual(name, "photo/detail")

    def test_compile_templates(self):
        templates = self.compressor.compile_templates(
            [_("pipeline/templates/photo/list.jst")]
        )
        self.assertEqual(
            templates,
            """window.JST = window.JST || {};\n%s\nwindow.JST[\'list\'] = template(\'<div class="photo">\\n <img src="<%%= src %%>" />\\n <div class="caption">\\n  <%%= caption %%>\\n </div>\\n</div>\');\n"""  # noqa
            % TEMPLATE_FUNC,
        )
        templates = self.compressor.compile_templates(
            [
                _("pipeline/templates/video/detail.jst"),
                _("pipeline/templates/photo/detail.jst"),
            ]
        )
        self.assertEqual(
            templates,
            """window.JST = window.JST || {};\n%s\nwindow.JST[\'video_detail\'] = template(\'<div class="video">\\n <video src="<%%= src %%>" />\\n <div class="caption">\\n  <%%= description %%>\\n </div>\\n</div>\');\nwindow.JST[\'photo_detail\'] = template(\'<div class="photo">\\n <img src="<%%= src %%>" />\\n <div class="caption">\\n  <%%= caption %%> by <%%= author %%>\\n </div>\\n</div>\');\n"""  # noqa
            % TEMPLATE_FUNC,
        )

    def test_embeddable(self):
        self.assertFalse(
            self.compressor.embeddable(_("pipeline/images/sprite.png"), None)
        )
        self.assertFalse(
            self.compressor.embeddable(_("pipeline/images/arrow.png"), "datauri")
        )
        self.assertTrue(
            self.compressor.embeddable(_("pipeline/images/embed/arrow.png"), "datauri")
        )
        self.assertFalse(
            self.compressor.embeddable(_("pipeline/images/arrow.dat"), "datauri")
        )

    def test_construct_asset_path(self):
        asset_path = self.compressor.construct_asset_path(
            "../../images/sprite.png", "css/plugins/gallery.css", "css/gallery.css"
        )
        self.assertEqual(asset_path, "../images/sprite.png")
        asset_path = self.compressor.construct_asset_path(
            "/images/sprite.png", "css/plugins/gallery.css", "css/gallery.css"
        )
        self.assertEqual(asset_path, "/images/sprite.png")

    def test_concatenate_with_url_rewrite(self) -> None:
        output = self.compressor.concatenate(
            [
                _("pipeline/css/urls.css"),
            ],
            file_sep="",
            output_filename="css/screen.css",
            rewrite_path_re=CSS_REWRITE_PATH_RE,
        )

        self.assertEqual(
            """.embedded-url-svg {
  background-image: url("data:image/svg+xml;charset=utf8,%3Csvg viewBox='0 0 32 32' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath      stroke='rgba(255, 255, 255, 0.5)' stroke-width='2' stroke-linecap='round' stroke-miterlimit='10' d='M4 8h24M4 16h24M4 24h24'/%3E%     3C/svg%3E");
}
@font-face {
  font-family: 'Pipeline';
  src: url('../pipeline/fonts/pipeline.eot');
  src: url('../pipeline/fonts/pipeline.eot?#iefix') format('embedded-opentype');
  src: local('☺'), url('../pipeline/fonts/pipeline.woff') format('woff'), url('../pipeline/fonts/pipeline.ttf') format('truetype'), url('../pipeline/fonts/pipeline.svg#IyfZbseF') format('svg');
  font-weight: normal;
  font-style: normal;
}
.relative-url {
  background-image: url(../pipeline/images/sprite-buttons.png);
}
.relative-url-querystring {
  background-image: url(../pipeline/images/sprite-buttons.png?v=1.0#foo=bar);
}
.absolute-url {
  background-image: url(/images/sprite-buttons.png);
}
.absolute-full-url {
  background-image: url(http://localhost/images/sprite-buttons.png);
}
.no-protocol-url {
  background-image: url(//images/sprite-buttons.png);
}
.anchor-tag-url {
  background-image: url(#image-gradient);
}
@font-face{src:url(../pipeline/fonts/pipeline.eot);src:url(../pipeline/fonts/pipeline.eot?#iefix) format('embedded-opentype'),url(../pipeline/fonts/pipeline.woff) format('woff'),url(../pipeline/fonts/pipeline.ttf) format('truetype');}
""",  # noqa
            output,
        )

    def test_concatenate_with_url_rewrite_data_uri(self):
        output = self.compressor.concatenate(
            [
                _("pipeline/css/nested/nested.css"),
            ],
            file_sep="",
            output_filename="pipeline/screen.css",
            rewrite_path_re=CSS_REWRITE_PATH_RE,
        )

        self.assertEqual(
            """.data-url {
  background-image: url(data:image/svg+xml;charset=US-ASCII,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22iso-8859-1%22%3F%3E%3C!DOCTYPE%20svg%20PUBLIC%20%22-%2F%2FW3C%2F%2FDTD%20SVG%201.1%2F%2FEN%22%20%22http%3A%2F%2Fwww.w3.org%2FGraphics%2FSVG%2F1.1%2FDTD%2Fsvg11.dtd%22%3E%3Csvg%20version%3D%221.1%22%20id%3D%22Layer_1%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20xmlns%3Axlink%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxlink%22%20x%3D%220px%22%20y%3D%220px%22%20%20width%3D%2212px%22%20height%3D%2214px%22%20viewBox%3D%220%200%2012%2014%22%20style%3D%22enable-background%3Anew%200%200%2012%2014%3B%22%20xml%3Aspace%3D%22preserve%22%3E%3Cpath%20d%3D%22M11%2C6V5c0-2.762-2.239-5-5-5S1%2C2.238%2C1%2C5v1H0v8h12V6H11z%20M6.5%2C9.847V12h-1V9.847C5.207%2C9.673%2C5%2C9.366%2C5%2C9%20c0-0.553%2C0.448-1%2C1-1s1%2C0.447%2C1%2C1C7%2C9.366%2C6.793%2C9.673%2C6.5%2C9.847z%20M9%2C6H3V5c0-1.657%2C1.343-3%2C3-3s3%2C1.343%2C3%2C3V6z%22%2F%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3C%2Fsvg%3E);
}
.data-url-quoted {
  background-image: url('data:image/svg+xml;charset=US-ASCII,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22iso-8859-1%22%3F%3E%3C!DOCTYPE%20svg%20PUBLIC%20%22-%2F%2FW3C%2F%2FDTD%20SVG%201.1%2F%2FEN%22%20%22http%3A%2F%2Fwww.w3.org%2FGraphics%2FSVG%2F1.1%2FDTD%2Fsvg11.dtd%22%3E%3Csvg%20version%3D%221.1%22%20id%3D%22Layer_1%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20xmlns%3Axlink%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxlink%22%20x%3D%220px%22%20y%3D%220px%22%20%20width%3D%2212px%22%20height%3D%2214px%22%20viewBox%3D%220%200%2012%2014%22%20style%3D%22enable-background%3Anew%200%200%2012%2014%3B%22%20xml%3Aspace%3D%22preserve%22%3E%3Cpath%20d%3D%22M11%2C6V5c0-2.762-2.239-5-5-5S1%2C2.238%2C1%2C5v1H0v8h12V6H11z%20M6.5%2C9.847V12h-1V9.847C5.207%2C9.673%2C5%2C9.366%2C5%2C9%20c0-0.553%2C0.448-1%2C1-1s1%2C0.447%2C1%2C1C7%2C9.366%2C6.793%2C9.673%2C6.5%2C9.847z%20M9%2C6H3V5c0-1.657%2C1.343-3%2C3-3s3%2C1.343%2C3%2C3V6z%22%2F%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3C%2Fsvg%3E');
}
""",  # noqa
            output,
        )

    def test_concatenate_css_with_sourcemap(self) -> None:
        output = self.compressor.concatenate(
            [
                _("pipeline/css/sourcemap.css"),
            ],
            file_sep="",
            output_filename="css/sourcemap-bundle.css",
            rewrite_path_re=CSS_REWRITE_PATH_RE,
        )

        self.assertEqual(
            output,
            "div {\n"
            "  display: inline;\n"
            "}\n"
            "\n"
            "span {\n"
            "  display: block;\n"
            "}\n"
            "\n"
            "\n"
            "//#  sourceMappingURL=../pipeline/css/sourcemap1.css.map\n"
            "\n"
            "//@ sourceMappingURL=../pipeline/css/sourcemap2.css.map  \n"
            "\n"
            "/*#  sourceMappingURL=../pipeline/css/sourcemap3.css.map */\n"
            "\n"
            "/*@ sourceMappingURL=../pipeline/css/sourcemap4.css.map  */\n"
            "\n"
            "//#  sourceURL=../pipeline/css/sourcemap5.css.map\n"
            "\n"
            "//@ sourceURL=../pipeline/css/sourcemap6.css.map  \n"
            "\n"
            "/*#  sourceURL=../pipeline/css/sourcemap7.css.map */\n"
            "\n"
            "/*@ sourceURL=../pipeline/css/sourcemap8.css.map  */\n",
        )

    def test_concatenate_js_with_sourcemap(self) -> None:
        output = self.compressor.concatenate(
            [
                _("pipeline/js/sourcemap.js"),
            ],
            file_sep=";",
            output_filename="js/sourcemap-bundle.js",
            rewrite_path_re=JS_REWRITE_PATH_RE,
        )

        self.assertEqual(
            output,
            "const abc = 123;\n"
            "\n"
            "\n"
            "//#  sourceMappingURL=../pipeline/js/sourcemap1.js.map\n"
            "\n"
            "//@ sourceMappingURL=../pipeline/js/sourcemap2.js.map  \n"
            "\n"
            "/*#  sourceMappingURL=../pipeline/js/sourcemap3.js.map */\n"
            "\n"
            "/*@ sourceMappingURL=../pipeline/js/sourcemap4.js.map  */\n"
            "\n"
            "//#  sourceURL=../pipeline/js/sourcemap5.js.map\n"
            "\n"
            "//@ sourceURL=../pipeline/js/sourcemap6.js.map  \n"
            "\n"
            "/*#  sourceURL=../pipeline/js/sourcemap7.js.map */\n"
            "\n"
            "/*@ sourceURL=../pipeline/js/sourcemap8.js.map  */\n",
        )

    def test_concatenate_without_rewrite_path_re(self) -> None:
        message = (
            "Compressor.concatenate() was called without passing "
            "rewrite_path_re_= or output_filename=. If you are "
            "specializing Compressor, please update your call "
            "to remain compatible with future changes."
        )

        with self.assertWarnsMessage(DeprecationWarning, message):
            output = self.compressor.concatenate(
                [
                    _("pipeline/js/sourcemap.js"),
                ],
                file_sep=";",
                output_filename="js/sourcemap-bundle.js",
            )

        self.assertEqual(
            output,
            "const abc = 123;\n"
            "\n"
            "\n"
            "//#  sourceMappingURL=sourcemap1.js.map\n"
            "\n"
            "//@ sourceMappingURL=sourcemap2.js.map  \n"
            "\n"
            "/*#  sourceMappingURL=sourcemap3.js.map */\n"
            "\n"
            "/*@ sourceMappingURL=sourcemap4.js.map  */\n"
            "\n"
            "//#  sourceURL=sourcemap5.js.map\n"
            "\n"
            "//@ sourceURL=sourcemap6.js.map  \n"
            "\n"
            "/*#  sourceURL=sourcemap7.js.map */\n"
            "\n"
            "/*@ sourceURL=sourcemap8.js.map  */\n",
        )

    def test_concatenate_without_output_filename(self) -> None:
        message = (
            "Compressor.concatenate() was called without passing "
            "rewrite_path_re_= or output_filename=. If you are "
            "specializing Compressor, please update your call "
            "to remain compatible with future changes."
        )

        with self.assertWarnsMessage(DeprecationWarning, message):
            output = self.compressor.concatenate(
                [
                    _("pipeline/js/sourcemap.js"),
                ],
                file_sep=";",
                rewrite_path_re=JS_REWRITE_PATH_RE,
            )

        self.assertEqual(
            output,
            "const abc = 123;\n"
            "\n"
            "\n"
            "//#  sourceMappingURL=sourcemap1.js.map\n"
            "\n"
            "//@ sourceMappingURL=sourcemap2.js.map  \n"
            "\n"
            "/*#  sourceMappingURL=sourcemap3.js.map */\n"
            "\n"
            "/*@ sourceMappingURL=sourcemap4.js.map  */\n"
            "\n"
            "//#  sourceURL=sourcemap5.js.map\n"
            "\n"
            "//@ sourceURL=sourcemap6.js.map  \n"
            "\n"
            "/*#  sourceURL=sourcemap7.js.map */\n"
            "\n"
            "/*@ sourceURL=sourcemap8.js.map  */\n",
        )

    def test_concatenate_without_file_sep(self) -> None:
        message = (
            "Compressor.concatenate() was called without passing "
            "file_sep=. If you are specializing Compressor, please "
            "update your call to remain compatible with future changes. "
            "Defaulting to JavaScript behavior for "
            "backwards-compatibility."
        )

        with self.assertWarnsMessage(DeprecationWarning, message):
            output = self.compressor.concatenate(
                [
                    _("pipeline/js/first.js"),
                    _("pipeline/js/second.js"),
                ],
                output_filename="js/sourcemap-bundle.js",
                rewrite_path_re=JS_REWRITE_PATH_RE,
            )

        self.assertEqual(
            output,
            "(function() {\n"
            "  window.concat = function() {\n"
            "    console.log(arguments);\n"
            "  }\n"
            "}()) // No semicolon\n"
            "\n"
            ";(function() {\n"
            "  window.cat = function() {\n"
            '    console.log("hello world");\n'
            "  }\n"
            "}());\n",
        )

    def test_legacy_concatenate_and_rewrite(self) -> None:
        message = (
            "Compressor.concatenate_and_rewrite() is deprecated. Please "
            "call concatenate() instead."
        )

        with self.assertWarnsMessage(DeprecationWarning, message):
            output = self.compressor.concatenate_and_rewrite(
                [
                    _("pipeline/css/urls.css"),
                ],
                "css/screen.css",
            )

        self.assertEqual(
            """.embedded-url-svg {
  background-image: url("data:image/svg+xml;charset=utf8,%3Csvg viewBox='0 0 32 32' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath      stroke='rgba(255, 255, 255, 0.5)' stroke-width='2' stroke-linecap='round' stroke-miterlimit='10' d='M4 8h24M4 16h24M4 24h24'/%3E%     3C/svg%3E");
}
@font-face {
  font-family: 'Pipeline';
  src: url('../pipeline/fonts/pipeline.eot');
  src: url('../pipeline/fonts/pipeline.eot?#iefix') format('embedded-opentype');
  src: local('☺'), url('../pipeline/fonts/pipeline.woff') format('woff'), url('../pipeline/fonts/pipeline.ttf') format('truetype'), url('../pipeline/fonts/pipeline.svg#IyfZbseF') format('svg');
  font-weight: normal;
  font-style: normal;
}
.relative-url {
  background-image: url(../pipeline/images/sprite-buttons.png);
}
.relative-url-querystring {
  background-image: url(../pipeline/images/sprite-buttons.png?v=1.0#foo=bar);
}
.absolute-url {
  background-image: url(/images/sprite-buttons.png);
}
.absolute-full-url {
  background-image: url(http://localhost/images/sprite-buttons.png);
}
.no-protocol-url {
  background-image: url(//images/sprite-buttons.png);
}
.anchor-tag-url {
  background-image: url(#image-gradient);
}
@font-face{src:url(../pipeline/fonts/pipeline.eot);src:url(../pipeline/fonts/pipeline.eot?#iefix) format('embedded-opentype'),url(../pipeline/fonts/pipeline.woff) format('woff'),url(../pipeline/fonts/pipeline.ttf) format('truetype');}
""",  # noqa
            output,
        )

    def test_legacy_concatenate_and_rewrite_with_data_uri(self) -> None:
        message = (
            "Compressor.concatenate_and_rewrite() is deprecated. Please "
            "call concatenate() instead."
        )

        with self.assertWarnsMessage(DeprecationWarning, message):
            output = self.compressor.concatenate_and_rewrite(
                [
                    _("pipeline/css/nested/nested.css"),
                ],
                "pipeline/screen.css",
            )

        self.assertEqual(
            """.data-url {
  background-image: url(data:image/svg+xml;charset=US-ASCII,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22iso-8859-1%22%3F%3E%3C!DOCTYPE%20svg%20PUBLIC%20%22-%2F%2FW3C%2F%2FDTD%20SVG%201.1%2F%2FEN%22%20%22http%3A%2F%2Fwww.w3.org%2FGraphics%2FSVG%2F1.1%2FDTD%2Fsvg11.dtd%22%3E%3Csvg%20version%3D%221.1%22%20id%3D%22Layer_1%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20xmlns%3Axlink%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxlink%22%20x%3D%220px%22%20y%3D%220px%22%20%20width%3D%2212px%22%20height%3D%2214px%22%20viewBox%3D%220%200%2012%2014%22%20style%3D%22enable-background%3Anew%200%200%2012%2014%3B%22%20xml%3Aspace%3D%22preserve%22%3E%3Cpath%20d%3D%22M11%2C6V5c0-2.762-2.239-5-5-5S1%2C2.238%2C1%2C5v1H0v8h12V6H11z%20M6.5%2C9.847V12h-1V9.847C5.207%2C9.673%2C5%2C9.366%2C5%2C9%20c0-0.553%2C0.448-1%2C1-1s1%2C0.447%2C1%2C1C7%2C9.366%2C6.793%2C9.673%2C6.5%2C9.847z%20M9%2C6H3V5c0-1.657%2C1.343-3%2C3-3s3%2C1.343%2C3%2C3V6z%22%2F%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3C%2Fsvg%3E);
}
.data-url-quoted {
  background-image: url('data:image/svg+xml;charset=US-ASCII,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22iso-8859-1%22%3F%3E%3C!DOCTYPE%20svg%20PUBLIC%20%22-%2F%2FW3C%2F%2FDTD%20SVG%201.1%2F%2FEN%22%20%22http%3A%2F%2Fwww.w3.org%2FGraphics%2FSVG%2F1.1%2FDTD%2Fsvg11.dtd%22%3E%3Csvg%20version%3D%221.1%22%20id%3D%22Layer_1%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20xmlns%3Axlink%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxlink%22%20x%3D%220px%22%20y%3D%220px%22%20%20width%3D%2212px%22%20height%3D%2214px%22%20viewBox%3D%220%200%2012%2014%22%20style%3D%22enable-background%3Anew%200%200%2012%2014%3B%22%20xml%3Aspace%3D%22preserve%22%3E%3Cpath%20d%3D%22M11%2C6V5c0-2.762-2.239-5-5-5S1%2C2.238%2C1%2C5v1H0v8h12V6H11z%20M6.5%2C9.847V12h-1V9.847C5.207%2C9.673%2C5%2C9.366%2C5%2C9%20c0-0.553%2C0.448-1%2C1-1s1%2C0.447%2C1%2C1C7%2C9.366%2C6.793%2C9.673%2C6.5%2C9.847z%20M9%2C6H3V5c0-1.657%2C1.343-3%2C3-3s3%2C1.343%2C3%2C3V6z%22%2F%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3Cg%3E%3C%2Fg%3E%3C%2Fsvg%3E');
}
""",  # noqa
            output,
        )

    @skipIf(sys.platform.startswith("win"), "requires posix platform")
    def test_compressor_subprocess_unicode(self):
        path = os.path.dirname(os.path.dirname(__file__))
        content = open(path + "/assets/css/unicode.css", encoding="utf-8").read()
        output = SubProcessCompressor(False).execute_command(("cat",), content)
        self.assertEqual(
            """.some_class {
  // Some unicode
  content: "áéíóú";
}
""",
            output,
        )

    def tearDown(self):
        default_collector.clear()


class CompressorImplementationTest(TestCase):
    maxDiff = None

    def setUp(self):
        self.compressor = Compressor()
        default_collector.collect(RequestFactory().get("/"))

    def tearDown(self):
        default_collector.clear()

    def _test_compressor(self, compressor_cls, compress_type, expected_file):
        override_settings = {
            (f"{compress_type.upper()}_COMPRESSOR"): compressor_cls,
        }
        with pipeline_settings(**override_settings):
            if compress_type == "js":
                result = self.compressor.compress_js(
                    [_("pipeline/js/first.js"), _("pipeline/js/second.js")]
                )
            else:
                result = self.compressor.compress_css(
                    [_("pipeline/css/first.css"), _("pipeline/css/second.css")],
                    os.path.join("pipeline", "css", os.path.basename(expected_file)),
                )
        with self.compressor.storage.open(expected_file, "r") as f:
            expected = f.read()
        self.assertEqual(result, expected)

    def test_jsmin(self):
        self._test_compressor(
            "pipeline.compressors.jsmin.JSMinCompressor",
            "js",
            "pipeline/compressors/jsmin.js",
        )

    def test_csshtmljsminify(self):
        self._test_compressor(
            "pipeline.compressors.csshtmljsminify.CssHtmlJsMinifyCompressor",
            "css",
            "pipeline/compressors/csshtmljsminify.css",
        )
        self._test_compressor(
            "pipeline.compressors.csshtmljsminify.CssHtmlJsMinifyCompressor",
            "js",
            "pipeline/compressors/csshtmljsminify.js",
        )

    @skipUnless(settings.HAS_NODE, "requires node")
    def test_uglifyjs(self):
        self._test_compressor(
            "pipeline.compressors.uglifyjs.UglifyJSCompressor",
            "js",
            "pipeline/compressors/uglifyjs.js",
        )

    @skipUnless(settings.HAS_NODE, "requires node")
    def test_terser(self):
        self._test_compressor(
            "pipeline.compressors.terser.TerserCompressor",
            "js",
            "pipeline/compressors/terser.js",
        )

    @skipUnless(settings.HAS_NODE, "requires node")
    def test_yuglify(self):
        self._test_compressor(
            "pipeline.compressors.yuglify.YuglifyCompressor",
            "css",
            "pipeline/compressors/yuglify.css",
        )
        self._test_compressor(
            "pipeline.compressors.yuglify.YuglifyCompressor",
            "js",
            "pipeline/compressors/yuglify.js",
        )

    @skipUnless(settings.HAS_NODE, "requires node")
    def test_cssmin(self):
        self._test_compressor(
            "pipeline.compressors.cssmin.CSSMinCompressor",
            "css",
            "pipeline/compressors/cssmin.css",
        )

    @skipUnless(settings.HAS_NODE, "requires node")
    @skipUnless(settings.HAS_JAVA, "requires java")
    def test_closure(self):
        self._test_compressor(
            "pipeline.compressors.closure.ClosureCompressor",
            "js",
            "pipeline/compressors/closure.js",
        )

    @skipUnless(settings.HAS_NODE, "requires node")
    @skipUnless(settings.HAS_JAVA, "requires java")
    def test_yui_js(self):
        self._test_compressor(
            "pipeline.compressors.yui.YUICompressor",
            "js",
            "pipeline/compressors/yui.js",
        )

    @skipUnless(settings.HAS_NODE, "requires node")
    @skipUnless(settings.HAS_JAVA, "requires java")
    def test_yui_css(self):
        self._test_compressor(
            "pipeline.compressors.yui.YUICompressor",
            "css",
            "pipeline/compressors/yui.css",
        )

    @skipUnless(settings.HAS_CSSTIDY, "requires csstidy")
    def test_csstidy(self):
        self._test_compressor(
            "pipeline.compressors.csstidy.CSSTidyCompressor",
            "css",
            "pipeline/compressors/csstidy.css",
        )
