import pynecone as pc
import json
from .edcdb import EDCDB

class State(pc.State):
    """The app state."""
    search_text: str
    fetch_text: str

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

edcdb = EDCDB('./Endoscreen_database.csv')

# Add state and page to the app.
app = pc.App(state=State)
app.add_page(index)
app.compile()
