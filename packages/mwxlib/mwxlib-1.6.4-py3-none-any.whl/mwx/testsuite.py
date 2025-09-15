#! python3
"""Test suite for App, Frame, and ControlPanel.

Get the wx.App or wx.Frame instance and start the main-loop if needed.

Usage:
    with testApp() as app:
        frm = wx.Frame(None)
        frm.Show()

Is equivalent to:
    app = wx.App()
    frm = wx.Frame(None)
    frm.Show()
    app.MainLoop()
"""
from contextlib import contextmanager
import wx

__all__ = ["testApp", "testFrame", "register_plug"]


@contextmanager
def testApp():
    app = wx.GetApp() or wx.App()
    yield app
    if not app.GetMainLoop():
        app.MainLoop()
## wx.App.run = staticmethod(testApp)


@contextmanager
def testFrame(**kwargs):
    with testApp() as app:
        frm = wx.Frame(None, **kwargs)
        yield frm
        frm.Show()
        app.SetTopWindow(frm)
## wx.Frame.run = staticmethod(testFrame)


def register_plug(cls=None, **kwargs):
    if cls is None:
        return lambda f: register(f, **kwargs)
    
    from mwx.graphman import Frame
    with testApp() as app:
        frm = app.GetTopWindow() or Frame(None)
        frm.load_plug(cls, force=1, show=1, **kwargs)
        frm.Show()
        app.SetTopWindow(frm)
    return cls
