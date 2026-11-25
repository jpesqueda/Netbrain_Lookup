import unittest
from netbrain_lookup.engine import parse_args
from netbrain_lookup.tui import LookupApp

class TUITests(unittest.IsolatedAsyncioTestCase):
    async def test_mount_and_collapsible(self):
        app = LookupApp(parse_args([]))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            widget = app.query_one("#s-summary")
            self.assertFalse(widget.collapsed)
            widget.collapsed = True
            await pilot.pause()
            self.assertTrue(widget.collapsed)
            self.assertTrue(app.query_one("#password").password)
