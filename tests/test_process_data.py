"""
Tests for ProcessData module, especially HTML sanitization
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


# HTML Sanitization Tests

def test_sanitize_jira_html_preserves_safe_html():
    """Test that safe HTML tags are preserved"""
    from jirajitsu.process_data import sanitize_jira_html

    safe_html = '<p>This is <strong>bold</strong> and <em>italic</em> text.</p>'
    result = sanitize_jira_html(safe_html)

    assert '<p>' in result
    assert '<strong>' in result
    assert '<em>' in result
    assert 'bold' in result
    assert 'italic' in result


def test_sanitize_jira_html_removes_script_tags():
    """Test that <script> tags are removed (XSS protection)"""
    from jirajitsu.process_data import sanitize_jira_html

    dangerous_html = '<p>Safe text</p><script>alert("XSS")</script><p>More text</p>'
    result = sanitize_jira_html(dangerous_html)

    assert '<script>' not in result
    assert '</script>' not in result
    assert 'Safe text' in result
    assert 'More text' in result


def test_sanitize_jira_html_removes_iframe_tags():
    """Test that <iframe> tags are removed"""
    from jirajitsu.process_data import sanitize_jira_html

    iframe_html = '<p>Text</p><iframe src="evil.com"></iframe><p>More</p>'
    result = sanitize_jira_html(iframe_html)

    assert '<iframe' not in result
    assert 'evil.com' not in result
    assert 'Text' in result
    assert 'More' in result


def test_sanitize_jira_html_removes_event_handlers():
    """Test that event handlers (onclick, onmouseover, etc.) are removed"""
    from jirajitsu.process_data import sanitize_jira_html

    onclick_html = '<a href="http://example.com" onclick="alert(1)" onmouseover="evil()">Link</a>'
    result = sanitize_jira_html(onclick_html)

    assert 'onclick' not in result
    assert 'onmouseover' not in result
    assert '<a href=' in result  # Safe href should be preserved
    assert 'Link' in result


def test_sanitize_jira_html_removes_style_attributes():
    """Test that style attributes are removed (CSS injection protection)"""
    from jirajitsu.process_data import sanitize_jira_html

    style_html = '<p style="color: red; position: absolute;">Text</p>'
    result = sanitize_jira_html(style_html)

    assert 'style=' not in result
    assert 'Text' in result


def test_sanitize_jira_html_removes_internal_ip_images():
    """Test that images with internal IP addresses are removed"""
    from jirajitsu.process_data import sanitize_jira_html

    internal_img = '<p>Text</p><img src="http://192.168.1.1/image.png" /><p>More</p>'
    result = sanitize_jira_html(internal_img)

    assert '192.168' not in result
    assert 'Text' in result
    assert 'More' in result


def test_sanitize_jira_html_preserves_external_images():
    """Test that external images are preserved"""
    from jirajitsu.process_data import sanitize_jira_html

    external_img = '<p>Text</p><img src="https://example.com/image.png" alt="Test" /><p>More</p>'
    result = sanitize_jira_html(external_img)

    assert 'example.com' in result
    assert '<img' in result
    assert 'alt=' in result


def test_sanitize_jira_html_preserves_links():
    """Test that links with safe attributes are preserved"""
    from jirajitsu.process_data import sanitize_jira_html

    link_html = '<p>Check <a href="https://example.com" title="Example">this link</a></p>'
    result = sanitize_jira_html(link_html)

    assert '<a' in result
    assert 'href=' in result
    assert 'example.com' in result
    assert 'title=' in result
    assert 'this link' in result


def test_sanitize_jira_html_preserves_lists():
    """Test that lists are preserved"""
    from jirajitsu.process_data import sanitize_jira_html

    list_html = '<ul><li>Item 1</li><li>Item 2</li></ul>'
    result = sanitize_jira_html(list_html)

    assert '<ul>' in result
    assert '<li>' in result
    assert 'Item 1' in result
    assert 'Item 2' in result


def test_sanitize_jira_html_preserves_tables():
    """Test that tables are preserved"""
    from jirajitsu.process_data import sanitize_jira_html

    table_html = '<table><tr><th>Header</th></tr><tr><td>Data</td></tr></table>'
    result = sanitize_jira_html(table_html)

    assert '<table>' in result
    assert '<tr>' in result
    assert '<th>' in result
    assert '<td>' in result
    assert 'Header' in result
    assert 'Data' in result


def test_sanitize_jira_html_preserves_code_blocks():
    """Test that code blocks are preserved"""
    from jirajitsu.process_data import sanitize_jira_html

    code_html = '<pre><code>def hello():\n    print("world")</code></pre>'
    result = sanitize_jira_html(code_html)

    assert '<pre>' in result
    assert '<code>' in result
    assert 'def hello' in result


def test_sanitize_jira_html_handles_empty_input():
    """Test that empty/null input is handled gracefully"""
    from jirajitsu.process_data import sanitize_jira_html

    assert sanitize_jira_html('') == ''
    assert sanitize_jira_html(None) is None


def test_sanitize_jira_html_allows_class_attribute():
    """Test that class attributes are preserved (for JIRA CSS classes)"""
    from jirajitsu.process_data import sanitize_jira_html

    class_html = '<p class="jira-paragraph">Text with class</p>'
    result = sanitize_jira_html(class_html)

    assert 'class=' in result
    assert 'jira-paragraph' in result


# Wiki Markup Cleaning Tests

def test_clean_jira_wiki_markup_removes_color_tags():
    """Test that JIRA wiki color tags are removed"""
    from jirajitsu.process_data import clean_jira_wiki_markup

    wiki_text = 'This is {color:red}red text{color} and {color:#333333}gray text{color}.'
    result = clean_jira_wiki_markup(wiki_text)

    assert '{color:red}' not in result
    assert '{color:#333333}' not in result
    assert '{color}' not in result
    assert 'red text' in result
    assert 'gray text' in result


def test_clean_jira_wiki_markup_handles_empty_input():
    """Test that empty/null input is handled gracefully"""
    from jirajitsu.process_data import clean_jira_wiki_markup

    assert clean_jira_wiki_markup('') == ''
    assert clean_jira_wiki_markup(None) is None


# Internal Image Stripping Tests

def test_strip_internal_images_removes_192_168_addresses():
    """Test that images with 192.168.x.x addresses are removed"""
    from jirajitsu.process_data import strip_internal_images

    html = '<p>Text</p><img src="http://192.168.1.100/img.png" /><p>More</p>'
    result = strip_internal_images(html)

    assert '192.168' not in result
    assert '<img' not in result or 'img.png' not in result
    assert 'Text' in result


def test_strip_internal_images_handles_various_formats():
    """Test that various internal IP image formats are removed"""
    from jirajitsu.process_data import strip_internal_images

    # Different quote styles
    html1 = '<img src="http://192.168.0.1/image.png" />'
    html2 = "<img src='http://192.168.0.1/image.png' />"

    assert '192.168' not in strip_internal_images(html1)
    assert '192.168' not in strip_internal_images(html2)


def test_strip_internal_images_preserves_external_images():
    """Test that external images are not removed"""
    from jirajitsu.process_data import strip_internal_images

    html = '<img src="https://example.com/image.png" />'
    result = strip_internal_images(html)

    assert '<img' in result
    assert 'example.com' in result


def test_strip_internal_images_handles_empty_input():
    """Test that empty/null input is handled gracefully"""
    from jirajitsu.process_data import strip_internal_images

    assert strip_internal_images('') == ''
    assert strip_internal_images(None) is None
