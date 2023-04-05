import pynecone as pc
import json
import os
try:
    from edcdb import EDCDB
except:
    try:
        from .edcdb import EDCDB
    except:
        raise

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
LAST_OCR = ''

class State(pc.State):
    search_text: str = ""
    fetch_text: str = ""
    ocr_results: list[str] = []
    img: str = ""

    async def handle_upload(self, file: pc.UploadFile):

        img = await file.read()

        outfile = os.path.join(ROOTDIR, f".web/public/{file.filename}")

        # Save the file.
        with open(outfile, "wb") as file_object:
            file_object.write(img)
        self.img = file.filename
        self.ocr_results = edcdb.identify(img)


    def search_set_text(self, text: str):
        self.search_text = text

    def fetch_set_text(self, text: str):
        self.fetch_text = text

    @pc.var
    def search_results(self) -> list[str]:
        return edcdb.api('v1', 'search', self.search_text)[:10]

    @pc.var
    def fetch_results(self) -> list[str]:
        return [json.dumps(r) for r in edcdb.api('v1','fetch', self.fetch_text)[:10]]


async def api(ver: str, func: str, query: str):
    if ver != 'v1':
        return dict()
    if func == 'fetch':
        return edcdb.api('v1', 'fetch', query)
    elif func == 'search':
        return edcdb.api('v1', 'search', query)


def ocr():
    return pc.vstack(
        pc.upload(
            pc.vstack(
                pc.button("Select File",),
                pc.text("Drag and drop files here or click to select files"),
            ),
        ),
        pc.button("Upload",
            on_click=lambda: State.handle_upload(pc.upload_files()),
        ),
        pc.image(src=State.img, width="25%", height="25%"),
        pc.vstack(
            pc.foreach(State.ocr_results, lambda res: pc.text(res)),
        )
    )


def search():
    return pc.box(
        pc.input(
            placeholder="Search EDCDB...",
            value=State.search_text,
            on_change=State.search_set_text,
        ),
        pc.vstack(
            pc.foreach(State.search_results, lambda result: pc.text(result)),
            overflow="auto",
            height="15em",
            width="100%",
        ))

def fetch():
    return pc.box(
        pc.input(
            placeholder="Fetch EDCDB...",
            value=State.fetch_text,
            on_change=State.fetch_set_text,
        ),
        pc.vstack(
            pc.foreach(State.fetch_results, lambda res: pc.text(res)),
            overflow="auto",
            height="15em",
            width="100%",
        )
    )

def navbar():
    return pc.box(
        pc.hstack(
            pc.image(src="favicon.ico"),
            pc.heading("My App"),
        ),
        pc.spacer(),
        pc.menu(
            pc.menu_button("Menu"),
        ),
    )

def index() -> pc.Component:
    return pc.vstack(
        #navbar(),
        ocr(),
        search(),
        fetch(),
    )

edcdb = EDCDB()

# Add state and page to the app.
app = pc.App(state=State)
app.api.add_api_route("/api/{ver}/{func}/{query}", api)
app.add_page(index)
app.compile()
