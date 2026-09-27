"""The detail panel's poster belongs to the row that is still selected.

Artwork arrives asynchronously. Arrowing through a list fired a request per
row, and whichever answer came last was painted - often the previous row's
logo on the row now selected. A failed load (a null pixmap) blanked the
placeholder letter as well.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication

from dopeiptv.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _panel(key):
    pending = []
    painted = []
    w = SimpleNamespace(
        tmdb=None, mode="live", _current_key=key,
        poster_art=SimpleNamespace(
            get=lambda url, cb: pending.append((url, cb))),
        _set_detail_logo=painted.append)
    return w, pending, painted


def test_a_late_logo_is_not_painted_on_the_next_row(qapp):
    w, pending, painted = _panel("a")
    MainWindow._load_detail_poster(w, {"stream_icon": "http://x/a.png"},
                                   False)
    w._current_key = "b"                     # the user arrowed on
    pm = QPixmap(4, 4)
    pending[0][1](pm)
    assert painted == []


def test_the_selected_rows_logo_is_painted(qapp):
    w, pending, painted = _panel("a")
    MainWindow._load_detail_poster(w, {"stream_icon": "http://x/a.png"},
                                   False)
    pm = QPixmap(4, 4)
    pending[0][1](pm)
    assert painted == [pm]


def test_a_failed_load_keeps_the_placeholder(qapp):
    w, pending, painted = _panel("a")
    MainWindow._load_detail_poster(w, {"stream_icon": "http://x/a.png"},
                                   False)
    pending[0][1](QPixmap())
    assert painted == []
