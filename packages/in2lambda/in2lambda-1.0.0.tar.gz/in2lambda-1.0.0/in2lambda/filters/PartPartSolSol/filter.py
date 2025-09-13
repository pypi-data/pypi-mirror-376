#!/usr/bin/env python3

"""Question parts appear one after another, and solutions for those parts come next."""

from typing import Optional

import panflute as pf

from in2lambda.api.set import Set
from in2lambda.filters.markdown import filter


@filter
def pandoc_filter(
    elem: pf.Element,
    doc: pf.elements.Doc,
    set: Set,
    parsing_answers: bool,
) -> Optional[pf.Str]:
    """A Pandoc filter that parses and translates various TeX elements.

    Args:
        elem: The current TeX element being processed. This could be a paragraph,
            ordered list, etc.
        doc: A Pandoc document container - essentially the Pandoc AST.
        set: The Python API that is used to store the result after processing
            the TeX file.
        parsing_answers: Whether an answers-only document is currently being parsed.

    Returns:
        Converted TeX elements for the AST where required
        e.g. replaces math equations so that they are surrounded by $.
    """
    # Question text (ListItem -> List -> Doc)
    if isinstance(elem.ancestor(3), pf.Doc):
        match type(elem):
            case pf.Para:
                if hasattr(pandoc_filter, "question"):
                    pandoc_filter.question.append(pf.stringify(elem))
                else:
                    pandoc_filter.question = [pf.stringify(elem)]
            case pf.OrderedList:
                pandoc_filter.parts = []
                for item in elem.content:
                    pandoc_filter.parts.append(pf.stringify(item))

    # Solutions are in a Div
    if isinstance(elem, pf.Div):
        set.add_question(main_text="\n".join(pandoc_filter.question))
        if hasattr(pandoc_filter, "parts"):
            for part in pandoc_filter.parts:
                set.current_question.add_part_text(part)
        pandoc_filter.question = []
        pandoc_filter.parts = []

        # If the first part of the div is an ordered list, assume part answers
        # If paragraph, extract all paragraphs as total answer
        match type(first_answer_part := elem.content[0]):
            case pf.OrderedList:
                for item in first_answer_part.content:
                    set.current_question.add_solution(pf.stringify(item))
            case pf.Para:
                set.current_question.add_solution(pf.stringify(elem))

    return None
