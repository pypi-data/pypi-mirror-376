"""Markdown to Telegram entities converter.

This module implements a converter that takes a Markdown string and
produces two things:

* A plain text message with all Markdown delimiters removed.
* A list of Telegram message entity dictionaries describing where
  formatting (bold, italic, underline, links, code, lists and
  block quotes) should be applied.

Telegram’s Bot API accepts an array of message entities alongside the
plain text.  This approach avoids the pitfalls of Telegram’s
``parse_mode`` (Markdown or HTML) by explicitly specifying the
formatting spans.  The parser supports common inline Markdown
constructs such as bold, italic, underline, strikethrough, spoiler,
inline code, code blocks and links, as well as block‑level
constructs like headings, quotes (including expandable/collapsed
quotes) and simple unordered and ordered lists.  It does not yet
support tables or embedded images.  See the README for examples.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

# Constants used for list rendering.  NBSP is a non‑breaking space to prevent
# line breaks between a list marker and the text.  FIGSPACE is a figure
# space used to pad numbers in ordered lists so that they align vertically.
NBSP = '\u00A0'
FIGSPACE = '\u2007'
# Cycle of bullet symbols used for nested unordered lists.  These symbols
# repeat with increasing nesting depth: level 0 → '•', level 1 → '◦', level 2 → '▪'.
BULLET_MARKERS = ['•', '◦', '▪']


@dataclass
class MessageEntity:
    """Represents a Telegram message entity.

    The Telegram bot API requires that styled text be accompanied by
    metadata describing the *offset* and *length* of each entity in
    UTF‑16 code units【16645222028428†L31-L89】.  Additional fields such as
    ``language`` or ``url`` may be present depending on the entity type
    (see https://core.telegram.org/type/MessageEntity for details).
    This class stores the information in a Pythonic form and exposes
    a ``to_dict`` method for conversion into the format expected by
    the API.

    To support collapsed block quotes, a ``collapsed`` attribute is
    provided.  When ``True``, this indicates that the block quote
    should be collapsed by default.  According to the Telegram schema,
    the ``collapsed`` flag applies to ``messageEntityBlockquote`` and
    determines whether a quote appears folded or expanded in the UI【885819747867534†L114-L123】.
    """

    type: str
    offset: int
    length: int
    url: Optional[str] = None
    language: Optional[str] = None
    collapsed: Optional[bool] = None

    def to_dict(self) -> Dict[str, object]:
        """Convert this entity to a dict compatible with the Bot API.

        Only fields that are set (non-None) are included.  For block
        quote entities, the ``collapsed`` flag is passed through as
        ``True`` if present.
        """
        d: Dict[str, object] = {
            "type": self.type,
            "offset": self.offset,
            "length": self.length,
        }
        if self.url:
            d["url"] = self.url
        if self.language:
            d["language"] = self.language
        if self.collapsed:
            # Only include collapsed flag when True; Telegram uses the
            # presence of this flag to denote expandable quotes【885819747867534†L114-L123】.
            d["collapsed"] = True
        return d


def utf16_length(s: str) -> int:
    """Compute the length of a string in UTF‑16 code units.

    Telegram counts offsets and lengths in terms of UTF‑16 code units
    rather than Unicode code points or UTF‑8 bytes.  Code points
    outside the Basic Multilingual Plane (i.e. those above U+FFFF)
    occupy **two** UTF‑16 code units, whereas all others occupy
    exactly one【16645222028428†L69-L79】.  This helper iterates over each
    character and adds two to the count if its ordinal is greater
    than 0xFFFF; otherwise it adds one.

    Parameters
    ----------
    s : str
        The string to measure.

    Returns
    -------
    int
        The number of UTF‑16 code units required to encode ``s``.
    """

    length = 0
    for ch in s:
        # Characters above the BMP are represented as surrogate pairs
        length += 2 if ord(ch) > 0xFFFF else 1
    return length


def parse_markdown_to_entities(markdown_text: str) -> Tuple[str, List[Dict[str, object]]]:
    """Convert a Markdown string into a plain message and Telegram entities.

    This function orchestrates the entire conversion process.  It
    normalises newlines, extracts fenced code blocks, then delegates
    parsing of the surrounding fragments to :func:`_parse_fragment`,
    which handles headings and block quotes in addition to inline
    formatting.  Offsets are accumulated in UTF‑16 code units so
    they may be passed directly to the Telegram Bot API.  The returned
    entity list is sorted by ascending offset so that parent entities
    always precede nested ones.

    Parameters
    ----------
    markdown_text : str
        A valid Markdown document.  Portions of the document enclosed
        within triple backticks (`````...``` ``) are treated as
        preformatted code blocks and mapped to ``pre`` entities,
        optionally capturing the specified language.

    Returns
    -------
    tuple
        A pair ``(message, entities)`` where ``message`` is the plain
        text of the original document with all Markdown delimiters
        removed, and ``entities`` is a list of dictionaries describing
        the formatting to be applied.
    """

    if not isinstance(markdown_text, str):
        raise TypeError("markdown_text must be a string")

    # Normalise line endings
    md = markdown_text.replace("\r\n", "\n").replace("\r", "\n")

    message_parts: List[str] = []
    entities: List[MessageEntity] = []
    global_offset = 0  # running UTF‑16 offset in the output message

    # Regex to match fenced code blocks with optional language specifier.
    # The pattern captures the language (everything up to the first newline)
    # and the code (everything up to the closing fence).  The DOTALL flag
    # allows ``.*`` to match across newlines.
    fence_pattern = re.compile(r"```(?P<lang>[^\n]*)\n(?P<code>.*?)```", re.DOTALL)

    pos = 0
    for match in fence_pattern.finditer(md):
        start, end = match.span()
        # Text preceding this code block
        plain_segment = md[pos:start]
        if plain_segment:
            out_text, out_entities = _parse_fragment(plain_segment, global_offset)
            message_parts.append(out_text)
            entities.extend(out_entities)
            global_offset += utf16_length(out_text)

        # Handle the code block itself
        lang = match.group('lang').strip()
        code = match.group('code')
        if code:
            # Pre entity: language is optional; empty language yields None
            entities.append(
                MessageEntity(
                    type="pre",
                    offset=global_offset,
                    length=utf16_length(code),
                    language=lang or None,
                )
            )
            message_parts.append(code)
            global_offset += utf16_length(code)

        pos = end

    # Process any trailing text after the last code block
    tail = md[pos:]
    if tail:
        out_text, out_entities = _parse_fragment(tail, global_offset)
        message_parts.append(out_text)
        entities.extend(out_entities)

    # Concatenate all parts into the final message string
    message = ''.join(message_parts)

    # Sort entities by offset so that outer entities come before nested ones
    entities_sorted = [e.to_dict() for e in sorted(entities, key=lambda x: x.offset)]

    return message, entities_sorted


def _parse_inline_entities(text: str, base_offset: int) -> Tuple[str, List[MessageEntity]]:
    """Parse inline Markdown formatting within a plain text segment.

    This helper is responsible for handling all formatting constructs
    that do not span multiple lines.  It removes Markdown delimiters
    from the output and constructs ``MessageEntity`` instances for
    the affected ranges.  Offsets are measured relative to the full
    message by adding ``base_offset`` to the UTF‑16 length of the
    characters emitted so far.

    The grammar supported here is deliberately simple: only a
    handful of two‑character delimiters (``**``, ``__``, ``~~``,
    ``||``) and single‑character delimiters (``*``, ``_``, `````
    for inline code) are recognised.  Inline links of the form
    ``[label](url)`` are also parsed.  Any delimiter that does not
    have a matching closing delimiter later in the string is treated
    as literal text.

    Parameters
    ----------
    text : str
        A substring of the original document without code fences.
    base_offset : int
        The UTF‑16 offset at which this substring begins in the full
        output message.

    Returns
    -------
    tuple
        ``(clean_text, entities)`` where ``clean_text`` is the input
        with all Markdown delimiters removed and ``entities`` is a list
        of :class:`MessageEntity` objects describing the formatting.
    """

    output_chars: List[str] = []
    entities: List[MessageEntity] = []
    # Stack of open delimiters: each entry is a tuple
    # (delim, entity_type, start_output_index)
    stack: List[Tuple[str, str, int]] = []
    i = 0
    n = len(text)

    # Precompute positions of closing delimiters to determine whether a
    # potential opening delimiter has a corresponding closing delimiter.
    # Without this check a solitary ``*`` would incorrectly open an
    # italic span and eat the remainder of the message.
    def has_closing_delim(delim: str, start_index: int) -> bool:
        return text.find(delim, start_index) != -1

    while i < n:
        ch = text[i]

        # Attempt to parse inline link: [text](url)
        if ch == '[':
            # Find the closing ']' and ensure it is followed by '(' and ')' for the URL
            close_bracket = text.find(']', i + 1)
            if close_bracket != -1 and close_bracket + 1 < n and text[close_bracket + 1] == '(':
                close_paren = text.find(')', close_bracket + 2)
                if close_paren != -1:
                    link_text = text[i + 1:close_bracket]
                    url = text[close_bracket + 2:close_paren]
                    # Emit link text
                    offset_utf16 = base_offset + utf16_length(''.join(output_chars))
                    length_utf16 = utf16_length(link_text)
                    entities.append(
                        MessageEntity(
                            type='text_link',
                            offset=offset_utf16,
                            length=length_utf16,
                            url=url,
                        )
                    )
                    output_chars.extend(list(link_text))
                    i = close_paren + 1
                    continue
            # If link syntax is malformed fall through and treat '[' as literal

        # Two‑character delimiters for bold, underline, strikethrough and spoilers
        two_char_delims = {
            '**': 'bold',
            '__': 'underline',
            '~~': 'strikethrough',
            '||': 'spoiler',
        }
        # Check if any two‑character delimiter matches at the current position
        delim_found: Optional[str] = None
        entity_type: Optional[str] = None
        for delim, etype in two_char_delims.items():
            if text.startswith(delim, i):
                delim_found = delim
                entity_type = etype
                break
        if delim_found:
            # Treat this delimiter as markup either if there is a pending
            # opening delimiter on the stack (so this closes it) or if a
            # matching delimiter appears later in the string.  Without
            # this short‑circuit the closing delimiter would incorrectly
            # be emitted as literal because no *additional* delimiter
            # exists beyond it.
            if (stack and stack[-1][0] == delim_found) or has_closing_delim(delim_found, i + len(delim_found)):
                if stack and stack[-1][0] == delim_found:
                    # Closing delimiter
                    _, etype_open, start_pos = stack.pop()
                    current_output = ''.join(output_chars)
                    inner_text = current_output[start_pos:]
                    length_utf16 = utf16_length(inner_text)
                    offset_utf16 = base_offset + utf16_length(current_output[:start_pos])
                    entities.append(
                        MessageEntity(
                            type=etype_open,
                            offset=offset_utf16,
                            length=length_utf16,
                        )
                    )
                else:
                    # Opening delimiter
                    stack.append((delim_found, entity_type, len(output_chars)))
                i += len(delim_found)
                continue
            # Otherwise no closing delimiter exists and there is no
            # pending open delimiter, so treat the characters literally.

        # Inline code: single backtick
        if ch == '`':
            # Look for the next backtick to close the code span
            close_backtick = text.find('`', i + 1)
            if close_backtick != -1:
                code_content = text[i + 1:close_backtick]
                offset_utf16 = base_offset + utf16_length(''.join(output_chars))
                length_utf16 = utf16_length(code_content)
                entities.append(
                    MessageEntity(
                        type='code',
                        offset=offset_utf16,
                        length=length_utf16,
                    )
                )
                output_chars.extend(list(code_content))
                i = close_backtick + 1
                continue
            # No closing backtick: treat as literal

        # Single‑character delimiters for italic ("*" or "_")
        if ch in ('*', '_'):
            # Treat this delimiter as markup if it either closes a pending
            # italic entity (top of the stack is the same delimiter) or
            # there is a matching delimiter later in the string.  Otherwise
            # fall through and emit the character literally (e.g. in "3*4=12").
            if (stack and stack[-1][0] == ch) or has_closing_delim(ch, i + 1):
                if stack and stack[-1][0] == ch:
                    # Closing italic delimiter
                    _, etype_open, start_pos = stack.pop()
                    current_output = ''.join(output_chars)
                    inner_text = current_output[start_pos:]
                    length_utf16 = utf16_length(inner_text)
                    offset_utf16 = base_offset + utf16_length(current_output[:start_pos])
                    entities.append(
                        MessageEntity(
                            type=etype_open,
                            offset=offset_utf16,
                            length=length_utf16,
                        )
                    )
                else:
                    # Opening italic delimiter
                    stack.append((ch, 'italic', len(output_chars)))
                i += 1
                continue
            # Otherwise treat as literal (fall through)

        # Escape character: treat the next character literally
        if ch == '\\':
            if i + 1 < n:
                output_chars.append(text[i + 1])
                i += 2
                continue
            # Trailing backslash: drop it
            i += 1
            continue

        # Default case: copy character to output
        output_chars.append(ch)
        i += 1

    # Any remaining unmatched delimiters on the stack are ignored.  Their
    # opening markers have already been removed from the output, and no
    # corresponding entities are created.  This behaviour aligns with
    # Telegram’s recommendation to generate entities only when markup
    # constructs are properly paired.

    return ''.join(output_chars), entities

def _parse_fragment(fragment: str, base_offset: int) -> Tuple[str, List[MessageEntity]]:
    """Parse a fragment of Markdown that does not contain code fences.

    In addition to inline formatting supported by :func:`_parse_inline_entities`,
    this function recognises top‑level constructs that span complete lines:

    * **Headings**: Lines beginning with one or more ``#`` characters followed by
      a space are treated as headings.  The heading markers are stripped
      from the output and the remaining text is wrapped in a single ``bold``
      entity (regardless of the heading level).  Inline formatting inside
      the heading is still processed normally.

    * **Block quotes**: Lines starting with ``>`` (optionally preceded by
      whitespace) are interpreted as block quotes.  The ``>`` and any
      following space are removed from the output.  If the text immediately
      following ``>`` begins with ``||``, the quote will be marked as
      ``expandable_blockquote`` (collapsed by default in the Telegram UI);
      otherwise it is a normal ``blockquote``.  Consecutive quote lines
      are coalesced into a single quote entity spanning the entire region,
      including newlines.  Inline formatting inside the quote is honoured.

    * **Unordered and ordered lists**: Lines beginning with ``-``, ``*`` or
      ``+`` followed by a space are treated as unordered list items.  Lines
      beginning with digits followed by ``.`` or ``)`` and a space are
      treated as ordered list items.  The indentation (spaces or tabs) of
      the marker determines the nesting level.  Unordered lists cycle
      through the bullet symbols ``•``, ``◦`` and ``▪`` at increasing
      nesting depths.  Ordered lists pad numbers with figure spaces so that
      multi‑digit numbers align.  Continuation lines (those with greater
      indentation that do not start with a list marker) are indented to
      align with the text of the previous list item.  Inline formatting
      inside list items is honoured.

    All other lines are passed through to :func:`_parse_inline_entities`.

    Parameters
    ----------
    fragment : str
        A substring of the original Markdown document that does not
        include fenced code blocks.
    base_offset : int
        The UTF‑16 offset at which this fragment begins in the full
        output message.

    Returns
    -------
    tuple
        ``(clean_text, entities)`` where ``clean_text`` is the input
        with block quote and heading markers removed and inline
        formatting stripped, and ``entities`` is a list of
        :class:`MessageEntity` objects describing the formatting.  The
        ``offset`` values on the returned entities are absolute,
        measured from the start of the full message.
    """

    output_parts: List[str] = []
    entities: List[MessageEntity] = []
    offset = base_offset

    # Split the fragment into lines, keeping line separators so newlines are
    # preserved in the output and counted towards offsets.
    lines = re.split('(?<=\n)', fragment)

    # Variables to track an open block quote region.  When processing
    # consecutive lines beginning with '>', we accumulate their length
    # and record whether any line has been marked as collapsed (via a
    # leading '||').  At the end of the region, we emit a single
    # blockquote entity with the appropriate ``collapsed`` flag.
    block_start_offset: Optional[int] = None
    block_length_acc = 0
    block_collapsed: bool = False

    i = 0
    num_lines = len(lines)
    while i < num_lines:
        line = lines[i]
        # Detect unordered list item: leading hyphen, asterisk or plus sign followed by space
        bullet_match = re.match(r'^([ \t]*)([-*+])\s+(.*)', line)
        # Detect ordered list item: digits followed by '.' or ')' and a space
        number_match = re.match(r'^([ \t]*)(\d+)[\.)]\s+(.*)', line)
        if bullet_match or number_match:
            # Finalise any active block quote before starting a list
            if block_start_offset is not None:
                entities.append(
                    MessageEntity(
                        type=current_quote_type,
                        offset=block_start_offset,
                        length=block_length_acc,
                    )
                )
                block_start_offset = None
                block_length_acc = 0

            indent_str = bullet_match.group(1) if bullet_match else number_match.group(1)
            # Compute list nesting level based on indentation: each two spaces = one level, each tab = 2 levels
            # Replace tabs with four spaces for counting and divide by 2
            expanded_indent = indent_str.replace('\t', '    ')
            level = len(expanded_indent) // 2

            # For ordered lists, determine padding width by scanning ahead
            width = 0
            if number_match:
                # Determine the contiguous ordered list sequence at this indent
                j = i
                while j < num_lines:
                    nm = re.match(r'^([ \t]*)(\d+)[\.)]\s+', lines[j])
                    if nm and nm.group(1).replace('\t', '    ') == expanded_indent:
                        width = max(width, len(nm.group(2)))
                        j += 1
                    else:
                        break
            # Process list items until indent decreases or pattern breaks
            while i < num_lines:
                curr_line = lines[i]
                bm = re.match(r'^([ \t]*)([-*+])\s+(.*)', curr_line)
                nm = re.match(r'^([ \t]*)(\d+)[\.)]\s+(.*)', curr_line)
                # Determine if current line matches same indent
                if bm and bm.group(1).replace('\t', '    ') == expanded_indent:
                    # Unordered list item
                    item_text = bm.group(3)
                    bullet_index = level % len(BULLET_MARKERS)
                    bullet_char = BULLET_MARKERS[bullet_index]
                    prefix = (NBSP * (level * 2)) + bullet_char + NBSP
                    prefix_len = utf16_length(prefix)
                    # Parse inline formatting within the list item
                    clean_item, inline_entities = _parse_inline_entities(item_text, offset + prefix_len)
                    entities.extend(inline_entities)
                    output_parts.append(prefix + clean_item)
                    offset += utf16_length(prefix + clean_item)
                    # Append newline if present in the original line
                    if curr_line.endswith('\n'):
                        output_parts.append('\n')
                        offset += utf16_length('\n')
                    # Advance line index
                    i += 1
                    # Handle continuation lines: lines that are indented further and do not start with a list marker
                    while i < num_lines:
                        next_line = lines[i]
                        # If the next line starts with a list marker at any indent, stop continuation
                        bm_next = re.match(r'^([ \t]*)([-*+])\s+', next_line)
                        nm_next = re.match(r'^([ \t]*)(\d+)[\.)]\s+', next_line)
                        if bm_next or nm_next:
                            break
                        # Determine indent length of next_line
                        indent_match = re.match(r'^([ \t]+)', next_line)
                        if indent_match:
                            next_exp = indent_match.group(1).replace('\t', '    ')
                            if len(next_exp) > len(expanded_indent):
                                # Continuation line; indent to align with current prefix
                                cont_text = next_line
                                # Remove leading whitespace to match message indentation
                                stripped = re.sub(r'^[ \t]+', '', cont_text)
                                cont_prefix = NBSP * (level * 2 + len(bullet_char) + 1)
                                clean_cont, cont_entities = _parse_inline_entities(stripped, offset + utf16_length(cont_prefix))
                                entities.extend(cont_entities)
                                output_parts.append(cont_prefix + clean_cont)
                                offset += utf16_length(cont_prefix + clean_cont)
                                if cont_text.endswith('\n'):
                                    output_parts.append('\n')
                                    offset += utf16_length('\n')
                                i += 1
                                continue
                        break
                    continue
                elif nm and nm.group(1).replace('\t', '    ') == expanded_indent:
                    # Ordered list item
                    num_str = nm.group(2)
                    item_text = nm.group(3)
                    # Pad number string using figure spaces for alignment
                    padded_num = num_str.rjust(width, FIGSPACE)
                    prefix = (NBSP * (level * 2)) + padded_num + '.\u00A0'
                    # Note: prefix contains a literal dot and a NBSP after the number
                    prefix_len = utf16_length(prefix)
                    clean_item, inline_entities = _parse_inline_entities(item_text, offset + prefix_len)
                    entities.extend(inline_entities)
                    output_parts.append(prefix + clean_item)
                    offset += utf16_length(prefix + clean_item)
                    if curr_line.endswith('\n'):
                        output_parts.append('\n')
                        offset += utf16_length('\n')
                    i += 1
                    # Handle continuation lines for ordered list items
                    while i < num_lines:
                        next_line = lines[i]
                        # If the next line starts with a list marker, stop continuation
                        bm_next = re.match(r'^([ \t]*)([-*+])\s+', next_line)
                        nm_next2 = re.match(r'^([ \t]*)(\d+)[\.)]\s+', next_line)
                        if bm_next or nm_next2:
                            break
                        indent_match2 = re.match(r'^([ \t]+)', next_line)
                        if indent_match2:
                            next_exp = indent_match2.group(1).replace('\t', '    ')
                            if len(next_exp) > len(expanded_indent):
                                stripped = re.sub(r'^[ \t]+', '', next_line)
                                cont_prefix = NBSP * (level * 2 + width + 2)
                                clean_cont, cont_entities = _parse_inline_entities(stripped, offset + utf16_length(cont_prefix))
                                entities.extend(cont_entities)
                                output_parts.append(cont_prefix + clean_cont)
                                offset += utf16_length(cont_prefix + clean_cont)
                                if next_line.endswith('\n'):
                                    output_parts.append('\n')
                                    offset += utf16_length('\n')
                                i += 1
                                continue
                        break
                    continue
                else:
                    break
            # End of list handling; skip default line processing
            continue

        # Identify quote lines: optional whitespace, '>' then optional single space
        quote_match = re.match(r'^(\s*)>( ?)(.*)', line)
        if quote_match:
            # Extract the text after the quote marker
            quote_content = quote_match.group(3)
            # Determine if this quote is collapsed by default
            collapsed = False
            if quote_content.startswith('||'):
                collapsed = True
                # Remove the collapsed marker.  If a space follows the
                # "||" sequence then drop it as well so the quote
                # content does not start with an extra space.
                if quote_content.startswith('|| '):
                    quote_content = quote_content[3:]
                else:
                    quote_content = quote_content[2:]
            # Start a new block quote region if not already active
            if block_start_offset is None:
                block_start_offset = offset
                block_length_acc = 0
                block_collapsed = collapsed
            # If already active and this line introduces collapsed flag, record it
            elif collapsed and not block_collapsed:
                block_collapsed = True
            # Parse inline formatting within the quote line
            clean_text, inline_entities = _parse_inline_entities(quote_content, offset)
            entities.extend(inline_entities)
            output_parts.append(clean_text)
            delta_len = utf16_length(clean_text)
            offset += delta_len
            block_length_acc += delta_len
            # Preserve the newline at the end of the line, if present
            if line.endswith('\n'):
                output_parts.append('\n')
                offset += utf16_length('\n')
                block_length_acc += utf16_length('\n')
            i += 1
            continue
        else:
            # Finalise any active block quote before handling non‑quote line
            if block_start_offset is not None:
                # Use expandable_blockquote type for collapsed quotes, blockquote for regular ones
                entity_type = 'expandable_blockquote' if block_collapsed else 'blockquote'
                entities.append(
                    MessageEntity(
                        type=entity_type,
                        offset=block_start_offset,
                        length=block_length_acc,
                    )
                )
                block_start_offset = None
                block_length_acc = 0
                block_collapsed = False

        # Check for heading: one or more '#' followed by at least one space
        heading_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if heading_match:
            heading_text = heading_match.group(2)
            # Parse inline formatting within the heading
            clean_heading, inline_entities = _parse_inline_entities(heading_text, offset)
            entities.extend(inline_entities)
            heading_len = utf16_length(clean_heading)
            # Wrap the entire heading in a bold entity regardless of level
            entities.append(
                MessageEntity(
                    type='bold',
                    offset=offset,
                    length=heading_len,
                )
            )
            # Append the cleaned heading text
            output_parts.append(clean_heading)
            offset += heading_len
            # Preserve newline if present
            if line.endswith('\n'):
                output_parts.append('\n')
                offset += utf16_length('\n')
            i += 1
            continue

        # Otherwise treat as normal line with inline formatting
        clean_line, inline_entities = _parse_inline_entities(line, offset)
        entities.extend(inline_entities)
        output_parts.append(clean_line)
        offset += utf16_length(clean_line)
        i += 1

    # If the fragment ended inside a quote, finalise the block quote.  Use
    # the accumulated ``block_collapsed`` flag to determine whether to
    # include the ``collapsed`` field on the resulting entity.  The
    # entity type is always ``blockquote``【885819747867534†L114-L123】.
    if block_start_offset is not None:
        # Use expandable_blockquote type for collapsed quotes, blockquote for regular ones
        entity_type = 'expandable_blockquote' if block_collapsed else 'blockquote'
        entities.append(
            MessageEntity(
                type=entity_type,
                offset=block_start_offset,
                length=block_length_acc,
            )
        )

    return ''.join(output_parts), entities