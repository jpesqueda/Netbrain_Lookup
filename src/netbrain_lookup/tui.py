"""Textual interface; all live lookups use the same engine as the CLI."""
from argparse import Namespace
from collections import Counter
from pathlib import Path
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import (Button, Collapsible, DataTable, Footer, Header, Input,
                             Label, ProgressBar, RichLog, Select, Static, Switch)
from . import engine
from .cli import execute

TABLE_COLUMNS = [
    ("Target", "target"), ("Type", "target_type"), ("Status", "status"),
    ("Endpoint IP", "endpoint_ip"), ("MAC Address", "endpoint_mac"),
    ("Switch", "switch_name"), ("Switch IP", "switch_ip"),
    ("Interface", "switch_port"), ("Port Description", "port_description"),
]


class LookupApp(App):
    TITLE = "NETBRAIN ENDPOINT LOOKUP"
    SUB_TITLE = "v1.0.0"
    CSS = """
    Screen { background: #101613; color: #dce8df; }
    #body { padding: 0 2; }
    Input, Select { margin-bottom: 1; }
    Label { color: #69d88a; }
    .buttons { height: auto; margin: 1 0; }
    Button { margin-right: 1; }
    Collapsible { margin-bottom: 1; }
    #events { height: 8; border: solid #35463b; }
    #results { height: 15; }
    #state { color: #69d88a; height: auto; }
    #details { height: auto; }
    #progress { margin: 1 0; }
    """
    BINDINGS = [("ctrl+q", "safe_quit", "Exit"), ("f2", "new_lookup", "New lookup")]

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.rows = []
        self.running = False
        self.last_code = 0

    def compose(self) -> ComposeResult:
        a = self.args
        yield Header()
        with VerticalScroll(id="body"):
            with Collapsible(title="Connection settings", collapsed=False, id="connection"):
                yield Label("NetBrain HTTPS URL")
                yield Input(value=a.url or "", placeholder="https://netbrain.example.local", id="url")
                yield Label("Username")
                yield Input(value=a.username or "", id="username")
                yield Label("Password")
                yield Input(password=True, value=a.password or "", id="password")
                yield Label("Tenant (name or ID; optional if only one)")
                yield Input(value=a.tenant or "", id="tenant")
                yield Label("Domain (name or ID; optional if only one)")
                yield Input(value=a.domain or "", id="domain")
            with Collapsible(title="Search input", collapsed=False, id="search-input"):
                yield Select([("Single IP / MAC", "host"), ("Hosts file", "file")],
                             value="file" if a.hosts_file else "host", allow_blank=False, id="source")
                yield Input(value=a.hosts_file or a.host or "", placeholder="IP, MAC or file path", id="target")
                yield Label("Output CSV or directory")
                yield Input(value=a.output or "Netbrain_Lookup_Report.csv", id="output")
            with Collapsible(title="Advanced settings", collapsed=True):
                yield Label("Search mode")
                yield Select([("Fast", "fast"), ("Standard", "standard"), ("Deep", "deep")],
                             value="fast" if a.fast else "deep" if a.deep else "standard",
                             allow_blank=False, id="mode")
                yield Label("Workers (1-20)")
                yield Input(value=str(a.workers), type="integer", id="workers")
                yield Label("Timeout / retries")
                yield Input(value=str(a.timeout), type="integer", id="timeout")
                yield Input(value=str(a.retries), type="integer", id="retries")
                yield Label("Disable TLS validation (unsafe)")
                yield Switch(value=a.insecure, id="insecure")
                yield Label("Overwrite existing reports")
                yield Switch(value=a.overwrite, id="overwrite")
            with Horizontal(classes="buttons"):
                yield Button("Start lookup", id="start", variant="success")
                yield Button("New lookup", id="new")
                yield Button("Exit", id="exit")
            yield Static("Ready", id="state", markup=False)
            yield ProgressBar(total=100, show_eta=False, id="progress")
            with Collapsible(title="Execution messages", collapsed=True, id="messages"):
                yield RichLog(id="events", markup=False, highlight=False)
            with Collapsible(title="Endpoint results", collapsed=False, id="result-section"):
                yield Select([("All", "all"), ("Found", "found"), ("Not found", "not-found"),
                              ("Errors", "error"), ("Other", "other")], value="all",
                             allow_blank=False, id="filter")
                yield Input(placeholder="Filter by IP, MAC, switch or port", id="filter-text")
                yield DataTable(cursor_type="row", zebra_stripes=True, id="results")
                yield Static("", id="shown", markup=False)
            with Collapsible(title="Selected endpoint", collapsed=True, id="detail-section"):
                yield Static("Select a row to see all fields.", id="details", markup=False)
            with Horizontal(classes="buttons"):
                yield Button("Expand all", id="expand")
                yield Button("Collapse all", id="collapse")
            for key, title in [("input", "Input"), ("summary", "Results"), ("output-summary", "Output"),
                               ("methods", "Search methods"), ("verification", "Secondary verification")]:
                with Collapsible(title=title, collapsed=key in ("methods", "verification"), id="s-"+key):
                    yield Static("No results yet.", id="v-"+key, markup=False)
        yield Footer()

    def on_mount(self):
        self.query_one("#results", DataTable).add_columns(*(name for name, _ in TABLE_COLUMNS))
        self.query_one("#password", Input).focus()
        self.args.password = None

    def field(self, name):
        return self.query_one("#"+name, Input).value.strip()

    @on(Button.Pressed)
    def button(self, event):
        key = event.button.id
        if key == "start":
            self.start_lookup()
        elif key == "new":
            self.action_new_lookup()
        elif key == "exit":
            self.action_safe_quit()
        elif key in ("expand", "collapse"):
            for widget in self.query(Collapsible):
                widget.collapsed = key == "collapse"

    def action_safe_quit(self):
        if self.running:
            self.notify("Lookup is still running; wait for completion.", severity="warning")
        else:
            self.exit(self.last_code)

    def action_new_lookup(self):
        if self.running:
            self.notify("Lookup is still running.", severity="warning")
            return
        self.rows = []
        self.refresh_table()
        self.query_one("#events", RichLog).clear()
        self.query_one("#progress", ProgressBar).update(progress=0)
        self.query_one("#state", Static).update("Ready")
        for widget in self.query("Static"):
            if widget.id and widget.id.startswith("v-"):
                widget.update("No results yet.")
        self.query_one("#details", Static).update("Select a row to see all fields.")
        self.query_one("#connection", Collapsible).collapsed = False
        self.query_one("#search-input", Collapsible).collapsed = False
        self.query_one("#password", Input).value = ""
        self.query_one("#password", Input).focus()

    def start_lookup(self):
        if self.running:
            return
        a = Namespace(**vars(self.args))
        a.url, a.username = self.field("url"), self.field("username")
        a.password = self.query_one("#password", Input).value
        a.tenant, a.domain = self.field("tenant") or None, self.field("domain") or None
        target = self.field("target")
        if not all((a.url, a.username, a.password, target)):
            self.query_one("#state", Static).update("ERROR: URL, username, password and target are required.")
            return
        a.hosts_file = target if self.query_one("#source", Select).value == "file" else None
        a.host = None if a.hosts_file else target
        if a.hosts_file and not Path(a.hosts_file).is_file():
            self.query_one("#state", Static).update("ERROR: Hosts file not found.")
            return
        a.output = self.field("output") or "Netbrain_Lookup_Report.csv"
        mode = self.query_one("#mode", Select).value
        a.fast, a.deep, a.standard = mode == "fast", mode == "deep", mode == "standard"
        try:
            a.workers, a.timeout, a.retries = (int(self.field(k)) for k in ("workers", "timeout", "retries"))
            if not 1 <= a.workers <= 20 or a.timeout < 1 or not 0 <= a.retries <= 10:
                raise ValueError
        except ValueError:
            self.query_one("#state", Static).update("ERROR: Workers 1-20, timeout > 0, retries 0-10.")
            return
        a.insecure = self.query_one("#insecure", Switch).value
        if a.insecure and a.ca_file:
            self.query_one("#state", Static).update("ERROR: CA file and insecure mode conflict.")
            return
        a.overwrite = self.query_one("#overwrite", Switch).value
        a.non_interactive = True
        self.query_one("#password", Input).value = ""
        self.rows = []
        self.refresh_table()
        self.query_one("#details", Static).update("Select a row to see all fields.")
        for widget in self.query("Static"):
            if widget.id and widget.id.startswith("v-"):
                widget.update("No results yet.")
        self.query_one("#events", RichLog).clear()
        self.query_one("#progress", ProgressBar).update(progress=0)
        self.query_one("#state", Static).update("Connecting...")
        self.query_one("#start", Button).disabled = True
        self.running = True
        self.run_lookup(a)

    @work(thread=True, exclusive=True)
    def run_lookup(self, args):
        engine.EVENT = lambda kind, data: self.call_from_thread(self.receive, kind, data)
        code = 1
        try:
            code = execute(args)
        finally:
            engine.EVENT = None
            self.call_from_thread(self.finished, code)

    def receive(self, kind, data):
        if kind == "message":
            self.query_one("#events", RichLog).write(data)
            if "ERROR:" in data:
                self.query_one("#state", Static).update(data)
                self.query_one("#messages", Collapsible).collapsed = False
        elif kind == "progress":
            percent, done, total, phase = data
            self.query_one("#progress", ProgressBar).update(progress=percent)
            self.query_one("#state", Static).update(f"{phase}: {done}/{total}")
        elif kind == "result":
            self.rows = data["rows"]
            self.refresh_table()
            counts = engine.target_summary(self.rows)
            types = counts
            methods = Counter(r["lookup_method"] for r in self.rows)
            self.query_one("#v-input", Static).update(
                f"Total targets: {counts['total']}\nIP targets: {types['IP']}\nMAC targets: {types['MAC']}\nWorkers: {data['workers']}\nMode: {data['mode']}")
            self.query_one("#v-summary", Static).update(
                f"Found: {counts['found']}\nNot found: {counts['not-found']}\nErrors: {counts['error']}\nOther: {counts['other']}\nResult rows: {len(self.rows)}")
            self.query_one("#v-output-summary", Static).update(
                f"CSV report: {data['output']}\nDiagnostic log: {data['log']}\nExecution time: {data['elapsed']:.2f}s")
            self.query_one("#v-methods", Static).update("\n".join(f"{k}: {v}" for k,v in sorted(methods.items())))
            stats = data["fallback"]
            self.query_one("#v-verification", Static).update(
                "Not requested" if not stats["requested"] else "\n".join(f"{k}: {v}" for k,v in stats.items()))
            self.query_one("#progress", ProgressBar).update(progress=100)
            self.query_one("#connection", Collapsible).collapsed = True
            self.query_one("#search-input", Collapsible).collapsed = True
            self.query_one("#result-section", Collapsible).collapsed = False
            self.query_one("#result-section", Collapsible).scroll_visible()

    def finished(self, code):
        self.running = False
        self.last_code = code
        self.query_one("#start", Button).disabled = False
        if code == 0:
            self.query_one("#state", Static).update("Lookup completed successfully.")
        elif self.rows:
            self.query_one("#state", Static).update("Lookup completed with errors. See diagnostic log.")
        else:
            self.query_one("#messages", Collapsible).collapsed = False

    @on(Select.Changed, "#filter")
    def filter_changed(self, event):
        self.refresh_table()

    @on(Input.Changed, "#filter-text")
    def text_changed(self, event):
        self.refresh_table()

    def refresh_table(self):
        table = self.query_one("#results", DataTable)
        if not table.columns:
            return
        choice = self.query_one("#filter", Select).value
        term = self.field("filter-text").casefold()
        table.clear()
        count = 0
        for i, row in enumerate(self.rows):
            status = row["status"]
            if choice != "all" and not (status == choice or choice == "other" and status not in ("found","not-found","error")):
                continue
            if term and term not in " ".join(str(v) for v in row.values()).casefold():
                continue
            from rich.text import Text
            color = {"found":"green", "not-found":"yellow", "error":"red"}.get(status, "white")
            table.add_row(*(Text(str(row.get(k, "")).replace("-", " ").upper(), style=color)
                            if k == "status" else Text(str(row.get(k,""))) for _,k in TABLE_COLUMNS), key=str(i))
            count += 1
        self.query_one("#shown", Static).update(f"Showing {count} of {len(self.rows)} rows")

    @on(DataTable.RowSelected, "#results")
    def selected(self, event):
        row = self.rows[int(event.row_key.value)]
        self.query_one("#details", Static).update("\n".join(f"{k}: {v}" for k,v in row.items()))
        section = self.query_one("#detail-section", Collapsible)
        section.collapsed = False
        section.scroll_visible()
