import pynecone as pc
import json
try:
    from edcdb import EDCDB
except:
    try:
        from .edcdb import EDCDB
    except:
        raise

class State(pc.State):
    """The app state."""
    search_text: str
    fetch_text: str
    img: str

    async def handle_upload(self, file: pc.UploadFile):
        self.img = await file.read()

    def search_set_text(self, text: str):
        self.search_text = text

    def fetch_set_text(self, text: str):
        self.fetch_text = text

    @pc.var
    def search_results(self) -> list[str]:
        return edcdb.api('v1', 'search', self.search_text)[:10]

    @pc.var
    def fetch_results(self) -> str:
        print(self.fetch_text)
        print(edcdb.api('v1','fetch', self.fetch_text))
        #return self.fetch_text
        return json.dumps(edcdb.api('v1','fetch', self.fetch_text))

    @pc.var
    def ocr_result(self) -> str:
        return edcdb.identify(self.img)

async def api(ver: str, func: str, query: str):
    if ver != 'v1':
        return dict()
    if func == 'fetch':
        return edcdb.api('v1', 'fetch', query)
    elif func == 'search':
        return edcdb.api('v1', 'search', query)


def img_upload():
    return pc.input(
        type=pc.InputType.FILE,
        on_change=State.set_img,
    )

def search() -> pc.Component:
    return pc.vstack(
        pc.input(
            placeholder="Search EDCDB...",
            value=State.search_text,
            on_change=State.search_set_text,
        ),
        pc.foreach(State.search_results, lambda result: pc.text(result)),
        pc.input(
            placeholder="Fetch EDCDB...",
            value=State.fetch_text,
            on_change=State.fetch_set_text,
        ),
        pc.text(State.fetch_results),
    )



def index() -> pc.Component:
    return pc.center(
        pc.vstack(
            #navbar(),
            search()

        )
    )
import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data','Endoscreen_database.csv')
edcdb = EDCDB(p)

# Add state and page to the app.
app = pc.App(state=State)
app.api.add_api_route("/api/{ver}/{func}/{query}", api)
app.add_page(index)
app.compile()
